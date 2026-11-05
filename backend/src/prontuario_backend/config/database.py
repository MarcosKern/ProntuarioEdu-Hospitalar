import os
from pathlib import Path

from sqlalchemy import create_engine, text


def check_database():
    url = os.getenv("DATABASE_URL", "sqlite:///./data/development.db")
    if url.startswith("sqlite:///./"):
        Path(url.removeprefix("sqlite:///./")).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            return connection.execute(text("SELECT 1")).scalar_one() == 1
    finally:
        engine.dispose()
