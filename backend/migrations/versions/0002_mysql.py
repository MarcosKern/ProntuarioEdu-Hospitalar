"""MySQL audit triggers and case-sensitive identity matching."""

from alembic import op
from sqlalchemy.dialects import mysql

revision = "0002_mysql"
down_revision = "0001_security"
branch_labels = None
depends_on = None


def upgrade():
    if op.get_bind().dialect.name != "mysql":
        raise RuntimeError("This revision requires MySQL")
    for table in ("record_permissions", "audit_events"):
        op.alter_column(
            table,
            "subject",
            existing_type=mysql.VARCHAR(255),
            type_=mysql.VARCHAR(255, charset="utf8mb4", collation="utf8mb4_bin"),
            existing_nullable=False,
        )
    for operation in ("UPDATE", "DELETE"):
        op.execute(
            f"CREATE TRIGGER audit_no_{operation.lower()} BEFORE {operation} ON audit_events FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Audit events are append only'"
        )


def downgrade():
    for operation in ("update", "delete"):
        op.execute(f"DROP TRIGGER audit_no_{operation}")
