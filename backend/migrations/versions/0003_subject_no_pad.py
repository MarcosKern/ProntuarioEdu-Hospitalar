"""Preserve exact OIDC subject comparisons, including trailing spaces."""
from alembic import op
from sqlalchemy.dialects import mysql

revision = "0003_subject_no_pad"
down_revision = "0002_mysql"
branch_labels = None
depends_on = None


def upgrade():
    for table in ("record_permissions", "audit_events"):
        op.alter_column(table, "subject", existing_type=mysql.VARCHAR(255),
                        type_=mysql.VARCHAR(255, charset="utf8mb4", collation="utf8mb4_0900_bin"), existing_nullable=False)


def downgrade():
    # May fail safely if newly distinct subjects would collide under PAD SPACE.
    for table in ("record_permissions", "audit_events"):
        op.alter_column(table, "subject", existing_type=mysql.VARCHAR(255),
                        type_=mysql.VARCHAR(255, charset="utf8mb4", collation="utf8mb4_bin"), existing_nullable=False)
