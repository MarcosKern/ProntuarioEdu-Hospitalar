from sqlalchemy import text

from prontuario_backend.config.database import engine_for


def test_database_connection(mysql_url):
    db = engine_for(mysql_url)

    try:
        with db.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            assert result.scalar() == 1
    finally:
        db.dispose()