from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from prontuario_backend.config.settings import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache(maxsize=4)
def engine_for(url):
    settings = get_settings()
    options = {"connect_timeout": settings.mysql_connect_timeout,
               "read_timeout": settings.mysql_read_timeout,
               "write_timeout": settings.mysql_write_timeout,
               "init_command": "SET time_zone = '+00:00'"}
    ca = settings.mysql_ssl_ca
    if ca:
        options["ssl"] = {"ca": ca, "check_hostname": True}
    return create_engine(url, pool_pre_ping=True, pool_timeout=settings.mysql_pool_timeout, hide_parameters=True, connect_args=options)



def engine():
    return engine_for(get_settings().database_url.get_secret_value())


def session():
    return sessionmaker(bind=engine(), expire_on_commit=False)()


def check_database():
    with engine().connect() as connection:
        return connection.execute(text("SELECT 1")).scalar_one() == 1
