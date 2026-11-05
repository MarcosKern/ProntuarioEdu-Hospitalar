from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from prontuario_backend.config.database import session
from prontuario_backend.models.security import AuditEvent, RecordPermission


def require_record_access(subject, record_id, action, request_id):
    """Call before every real record operation; no implicit role or admin bypass."""
    if action not in {"read", "write"}:
        raise HTTPException(403, "Acesso negado")
    try:
        with session() as db:
            permission = db.scalar(select(RecordPermission.id).where(
                RecordPermission.subject == subject,
                RecordPermission.record_id == str(record_id),
                RecordPermission.action == action,
            ))
            db.add(AuditEvent(subject=subject, record_id=str(record_id), action=action,
                              outcome="allowed" if permission else "denied", request_id=request_id))
            db.commit()
    except SQLAlchemyError:
        raise HTTPException(503, "Controle de acesso indisponível") from None
    if not permission:
        raise HTTPException(403, "Acesso negado")
