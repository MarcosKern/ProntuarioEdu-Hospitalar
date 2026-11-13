from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, insert, select
from sqlalchemy.exc import IntegrityError

from prontuario_backend.config.database import engine, session
from prontuario_backend.models.security import AuditEvent, RecordPermission


@pytest.fixture
def technical_schema(mysql_url):
    backend = Path(__file__).resolve().parents[2]
    command.upgrade(Config(str(backend / "alembic.ini")), "head")
    database = engine()
    yield database
    assert database.pool.checkedout() == 0


def permission():
    return RecordPermission(
        id=str(uuid4()), subject=str(uuid4()), record_id=str(uuid4()), action="read"
    )


def persisted_counts(database):
    with database.connect() as connection:
        return (
            connection.scalar(select(func.count()).select_from(RecordPermission)),
            connection.scalar(select(func.count()).select_from(AuditEvent)),
        )


def test_session_commit_is_visible_to_another_connection(technical_schema):
    row = permission()
    with session() as db:
        db.add(row)
        db.commit()
    with technical_schema.connect() as connection:
        assert (
            connection.scalar(
                select(RecordPermission.id).where(RecordPermission.id == row.id)
            )
            == row.id
        )


def test_session_close_rolls_back_flushed_work_without_commit(technical_schema):
    with session() as db:
        db.add(permission())
        db.flush()
        assert db.scalar(select(func.count()).select_from(RecordPermission)) == 1
        assert persisted_counts(technical_schema) == (0, 0)
    assert persisted_counts(technical_schema) == (0, 0)


def test_session_begin_rolls_back_permission_and_audit_after_application_error(
    technical_schema,
):
    row = permission()
    with (
        pytest.raises(RuntimeError, match="isolated business failure"),
        session() as db,
        db.begin(),
    ):
        db.add(row)
        db.add(
            AuditEvent(
                subject=row.subject,
                record_id=row.record_id,
                action="read",
                outcome="allowed",
                request_id=str(uuid4()),
            )
        )
        db.flush()
        raise RuntimeError("isolated business failure")
    assert persisted_counts(technical_schema) == (0, 0)


def test_database_constraint_failure_rolls_back_the_whole_unit_and_session_can_be_reused(
    technical_schema,
):
    row = permission()
    with session() as db:
        db.add(row)
        db.add(
            AuditEvent(
                subject=row.subject,
                record_id=row.record_id,
                action="read",
                outcome="allowed",
                request_id=str(uuid4()),
            )
        )
        db.flush()
        db.add(
            RecordPermission(
                id=str(uuid4()),
                subject=row.subject,
                record_id=row.record_id,
                action=row.action,
            )
        )
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()
        assert persisted_counts(technical_schema) == (0, 0)
        db.add(permission())
        db.commit()
    assert persisted_counts(technical_schema) == (1, 0)


def test_core_begin_commits_permission_and_audit_together(technical_schema):
    row = permission()
    with technical_schema.begin() as connection:
        connection.execute(
            insert(RecordPermission).values(
                id=row.id,
                subject=row.subject,
                record_id=row.record_id,
                action=row.action,
            )
        )
        connection.execute(
            insert(AuditEvent).values(
                subject=row.subject,
                record_id=row.record_id,
                action="read",
                outcome="allowed",
                request_id=str(uuid4()),
            )
        )
    assert persisted_counts(technical_schema) == (1, 1)


def test_core_begin_rolls_back_permission_and_audit_after_application_error(
    technical_schema,
):
    row = permission()
    with (
        pytest.raises(RuntimeError, match="isolated business failure"),
        technical_schema.begin() as connection,
    ):
        connection.execute(
            insert(RecordPermission).values(
                id=row.id,
                subject=row.subject,
                record_id=row.record_id,
                action=row.action,
            )
        )
        connection.execute(
            insert(AuditEvent).values(
                subject=row.subject,
                record_id=row.record_id,
                action="read",
                outcome="allowed",
                request_id=str(uuid4()),
            )
        )
        raise RuntimeError("isolated business failure")
    assert persisted_counts(technical_schema) == (0, 0)
