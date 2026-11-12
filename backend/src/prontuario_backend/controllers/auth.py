from datetime import UTC, datetime

from prontuario_backend.config.auth import AuthenticatedUser
from prontuario_backend.config.settings import get_settings
from prontuario_backend.views.auth import SessionResponse


def session_status(user: AuthenticatedUser) -> SessionResponse:
    """Informa a validade do access token; a renovação pertence ao provedor OAuth2."""
    remaining = max(0, int((user.expires_at - datetime.now(UTC)).total_seconds()))
    return SessionResponse(
        subject=user.subject,
        expires_at=user.expires_at,
        expires_in_seconds=remaining,
        refresh_required=remaining <= get_settings().oidc_refresh_window_seconds,
    )
