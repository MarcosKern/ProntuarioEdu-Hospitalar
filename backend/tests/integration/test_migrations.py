from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import func, insert, inspect, select, text

from prontuario_backend.config.database import Base, engine
from prontuario_backend.models.security import AuditEvent, RecordPermission

BACKEND = Path(__file__).resolve().parents[2]
TECHNICAL_TABLES = {"alembic_version", "record_permissions", "audit_events"}


def test_incremental_migrations_create_only_empty_technical_tables_on_mysql84(
    mysql_url,
):
    config = Config(str(BACKEND / "alembic.ini"))
    database = engine()
    assert inspect(database).get_table_names() == []
    for target, expected_collation, expected_triggers in [
        ("0001_security", None, set()),
        ("0002_mysql", "utf8mb4_bin", {"audit_no_update", "audit_no_delete"}),
        ("head", "utf8mb4_0900_bin", {"audit_no_update", "audit_no_delete"}),
    ]:
        command.upgrade(config, target)
        assert set(inspect(database).get_table_names()) == TECHNICAL_TABLES
        with database.connect() as connection:
            assert connection.scalar(text("SELECT VERSION()")).startswith("8.4.")
            assert connection.scalar(text("SELECT @@session.time_zone")) == "+00:00"
            assert (
                connection.scalar(text("SELECT version_num FROM alembic_version"))
                == ScriptDirectory.from_config(config).get_revision(target).revision
            )
            for table in (RecordPermission, AuditEvent):
                assert connection.scalar(select(func.count()).select_from(table)) == 0
            assert set(
                connection.scalars(
                    text("""
                SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE()
            """)
                )
            ) == {"InnoDB"}
            triggers = set(
                connection.scalars(
                    text("""
                SELECT TRIGGER_NAME FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE()
            """)
                )
            )
            assert triggers == expected_triggers
            if expected_collation:
                collations = list(
                    connection.scalars(
                        text("""
                    SELECT COLLATION_NAME FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME IN ('record_permissions','audit_events') AND COLUMN_NAME='subject'
                """)
                    )
                )
                assert collations == [expected_collation, expected_collation]
    assert database.pool.checkedout() == 0


def test_repeated_upgrade_preserves_existing_permissions_and_append_only_audit(
    mysql_url,
):
    config = Config(str(BACKEND / "alembic.ini"))
    command.upgrade(config, "head")
    database = engine()
    subject, record = str(uuid4()), str(uuid4())
    with database.begin() as connection:
        connection.execute(
            insert(RecordPermission).values(
                subject=subject, record_id=record, action="read"
            )
        )
        connection.execute(
            insert(AuditEvent).values(
                subject=subject,
                record_id=record,
                action="read",
                outcome="allowed",
                request_id=str(uuid4()),
            )
        )
    with database.connect() as connection:
        before = [
            connection.execute(select(table)).all()
            for table in (RecordPermission, AuditEvent)
        ]
    command.upgrade(config, "head")
    command.upgrade(config, "head")
    with database.connect() as connection:
        assert [
            connection.execute(select(table)).all()
            for table in (RecordPermission, AuditEvent)
        ] == before
        assert all(len(rows) == 1 for rows in before)
    assert database.pool.checkedout() == 0


def test_migrated_technical_schema_matches_sqlalchemy_models(mysql_url):
    command.upgrade(Config(str(BACKEND / "alembic.ini")), "head")
    with engine().connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        assert compare_metadata(context, Base.metadata) == []
