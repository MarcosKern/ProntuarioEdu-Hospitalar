from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from prontuario_backend.config.database import Base


class RecordPermission(Base):
    __tablename__ = "record_permissions"
    __table_args__ = (UniqueConstraint("subject", "record_id", "action"),)
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    subject: Mapped[str] = mapped_column(String(255, collation="utf8mb4_0900_bin"))
    record_id: Mapped[str] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(String(32))


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    subject: Mapped[str] = mapped_column(String(255, collation="utf8mb4_0900_bin"))
    action: Mapped[str] = mapped_column(String(32))
    record_id: Mapped[str] = mapped_column(String(36))
    outcome: Mapped[str] = mapped_column(String(16))
    request_id: Mapped[str] = mapped_column(String(36))
