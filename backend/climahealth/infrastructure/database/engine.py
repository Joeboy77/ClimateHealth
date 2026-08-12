from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Column, Engine, create_engine, inspect, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session, sessionmaker

from climahealth.infrastructure.database.tables import Base


def build_engine(url: str) -> Engine:
    return create_engine(url, pool_pre_ping=True, future=True)


def create_schema(engine: Engine) -> None:
    """Create missing tables, then add missing columns.

    create_all builds tables that do not exist but leaves existing ones untouched, so a
    database created before a column was added keeps failing every query that selects it.
    This adds what the models declare and the database lacks.

    Additive only, and deliberately so: it never drops a column, narrows a type, or
    rewrites data. Anything beyond adding a column is a real migration that somebody
    should look at rather than something a process should do to itself on startup.
    """
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as connection:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue
            present = {column["name"] for column in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in present:
                    continue
                connection.execute(text(_add_column_statement(table.name, column)))


def _add_column_statement(table_name: str, column: Column[object]) -> str:
    declaration = column.type.compile(dialect=postgresql.dialect())
    clause = f'ALTER TABLE "{table_name}" ADD COLUMN "{column.name}" {declaration}'
    # An existing row needs a value for a column that cannot be null, and the model's
    # own default is the only sensible one to give it.
    if column.default is not None and getattr(column.default, "is_scalar", False):
        clause += f" DEFAULT {_as_sql_literal(column.default.arg)}"
    if not column.nullable:
        clause += " NOT NULL"
    return clause


def _as_sql_literal(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


class SessionFactory:
    def __init__(self, engine: Engine) -> None:
        self._sessionmaker = sessionmaker(bind=engine, expire_on_commit=False)

    @contextmanager
    def begin(self) -> Iterator[Session]:
        session = self._sessionmaker()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
