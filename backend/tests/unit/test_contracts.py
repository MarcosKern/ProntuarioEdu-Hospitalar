from uuid import uuid4

import pytest
from pydantic import ValidationError

from prontuario_backend.views.auth import (
    IdentityResponse,
    LoginRequest,
    PasswordChangeRequest,
    RefreshRequest,
    TokenResponse,
)
from prontuario_backend.views.errors import ErrorResponse, error_body
from prontuario_backend.views.health import HealthResponse


@pytest.mark.parametrize("model,payload", [
    (LoginRequest, {"grant_type": "password", "username": "admin", "password": "isolated-secret", "role": "admin"}),
    (LoginRequest, {"grant_type": "password", "username": "admin", "password": "isolated-secret", "client_secret": "unsupported"}),
    (RefreshRequest, {"refresh_token": "isolated-refresh", "user_id": str(uuid4())}),
    (PasswordChangeRequest, {"current_password": "isolated-current", "new_password": "isolated-new-password", "admin": True}),
])
def test_authentication_inputs_reject_unexpected_or_unsupported_fields(model, payload):
    with pytest.raises(ValidationError):
        model.model_validate(payload)


@pytest.mark.parametrize("payload", [{"refresh_token": ""}, {"refresh_token": "x" * 201},
                                      {"refresh_token": 123}, {"refresh_token": "isolated-refresh", "scope": "x" * 513}])
def test_refresh_inputs_have_bounded_types_and_lengths(payload):
    with pytest.raises(ValidationError):
        RefreshRequest.model_validate(payload)


def test_valid_login_and_password_inputs_keep_secrets_out_of_repr():
    login = LoginRequest(grant_type="password", username="admin", password="isolated-login-secret", client_id="", client_secret="")
    password = PasswordChangeRequest(current_password="isolated-current", new_password="isolated-new-password")
    assert "isolated-login-secret" not in repr(login)
    assert "isolated-current" not in repr(password)
    assert "isolated-new-password" not in repr(password)


@pytest.mark.parametrize("model,payload", [
    (IdentityResponse, {"subject": "invalid-id"}),
    (HealthResponse, {"status": "failed", "database": "ok"}),
    (TokenResponse, {"access_token": "isolated-access", "refresh_token": "isolated-refresh", "expires_in": 0, "scope": "identity:read"}),
])
def test_response_models_reject_invalid_ids_states_and_expiration(model, payload):
    with pytest.raises(ValidationError):
        model.model_validate(payload)


def test_identity_serializes_uuid_and_filters_private_fields():
    subject = str(uuid4())
    identity = IdentityResponse.model_validate({"subject": subject, "hash_senha": "must-not-escape"})
    assert identity.model_dump(mode="json") == {"subject": subject}


def test_error_envelope_is_shared_and_preserves_request_id():
    request_id = str(uuid4())
    body = error_body("validation_error", request_id)
    assert body == {"error": {"code": "validation_error", "request_id": request_id}}
    assert str(ErrorResponse.model_validate(body).error.request_id) == request_id
