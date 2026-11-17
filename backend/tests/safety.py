"""Validate the target before opening any connection or executing destructive SQL."""

import re

from sqlalchemy.engine import make_url


def identity(url):
    parsed = make_url(url)
    host = (parsed.host or "").lower()
    if host in {"localhost", "127.0.0.1", "::1"}:
        host = "loopback"
    return host, parsed.port or 3306, (parsed.database or "").casefold()


def validate_test_database(url, application_urls, confirmation):
    parsed = make_url(url)
    if (
        parsed.drivername != "mysql+pymysql"
        or not parsed.host
        or not re.fullmatch(r"prontuario_test(?:_[a-z0-9_]+)?", parsed.database or "")
    ):
        raise ValueError("Use a dedicated MySQL prontuario_test database")
    if confirmation != parsed.database:
        raise ValueError(
            "MYSQL_TEST_ALLOW_RESET must explicitly match the test database name"
        )
    for application_url in application_urls:
        if application_url and identity(url) == identity(application_url):
            raise ValueError("Test database must differ from the application database")
