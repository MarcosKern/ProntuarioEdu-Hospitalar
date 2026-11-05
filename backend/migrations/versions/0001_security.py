"""Security tables only: no records, users or grants are inserted."""
from alembic import op
import sqlalchemy as sa

revision = "0001_security"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("record_permissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("record_id", sa.String(36), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.UniqueConstraint("subject", "record_id", "action"))
    op.create_table("audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("record_id", sa.String(36), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("outcome", sa.String(16), nullable=False),
        sa.Column("request_id", sa.String(36), nullable=False))
    if op.get_bind().dialect.name == "postgresql":
        op.execute("""CREATE FUNCTION reject_audit_change() RETURNS trigger AS $$
            BEGIN RAISE EXCEPTION 'Audit events are append only'; END;
            $$ LANGUAGE plpgsql""")
        op.execute("CREATE TRIGGER audit_append_only BEFORE UPDATE OR DELETE ON audit_events FOR EACH ROW EXECUTE FUNCTION reject_audit_change()")


def downgrade():
    op.drop_table("audit_events")
    op.drop_table("record_permissions")
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP FUNCTION reject_audit_change()")
