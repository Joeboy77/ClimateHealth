from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from climahealth.infrastructure.database.tables import Base


def build_engine(url: str) -> Engine:
    return create_engine(url, pool_pre_ping=True, future=True)


def create_schema(engine: Engine) -> None:
    Base.metadata.create_all(engine)


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
