"""SQLAlchemy engine and session."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from config import get_settings

settings = get_settings()
_url = settings["database_url"] or "sqlite:///./submissions.db"

if _url.startswith("sqlite"):
    engine = create_engine(
        _url,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
