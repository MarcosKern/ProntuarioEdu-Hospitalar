"""Security tables only: no records, users or grants are inserted."""

import sqlalchemy as sa
from alembic import op

revision = "0001_security"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "record_permissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("record_id", sa.String(36), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.UniqueConstraint("subject", "record_id", "action"),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("record_id", sa.String(36), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("outcome", sa.String(16), nullable=False),
        sa.Column("request_id", sa.String(36), nullable=False),
    )


def downgrade():
    op.drop_table("audit_events")
    op.drop_table("record_permissions")
