from functools import lru_cache
from pathlib import Path

from prontuario_backend.config.settings import get_settings
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


@lru_cache(maxsize=4)
def engine_for(url):
    if url.startswith("sqlite:///./"):
        Path(url.removeprefix("sqlite:///./")).parent.mkdir(parents=True, exist_ok=True)
    kwargs = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {}
    return create_engine(url, pool_pre_ping=True, hide_parameters=True, **kwargs)


def engine():
    return engine_for(get_settings().database_url.get_secret_value())


def session():
    return sessionmaker(bind=engine(), expire_on_commit=False)()


def check_database():
    with engine().connect() as connection:
        return connection.execute(text("SELECT 1")).scalar_one() == 1
