"""SECCIÓN: BASE DE DATOS — Motor, sesiones y clase base SQLAlchemy."""

from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """SECCIÓN: ORM BASE — Clase padre de todas las tablas."""
    pass


# SECCIÓN: DATABASE ENGINE — Usa la URL normalizada con psycopg versión 3.
engine = create_engine(
    settings.sqlalchemy_database_url,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """SECCIÓN: DB DEPENDENCY — Entrega una sesión y garantiza su cierre."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
