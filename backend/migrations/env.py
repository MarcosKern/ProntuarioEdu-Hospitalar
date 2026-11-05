from alembic import context
from prontuario_backend.config.database import Base, engine
from prontuario_backend.models import security  # noqa: F401

with engine().connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()
