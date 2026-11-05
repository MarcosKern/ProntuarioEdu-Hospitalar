from prontuario_backend.config.database import check_database


def database_ready():
    return check_database()
