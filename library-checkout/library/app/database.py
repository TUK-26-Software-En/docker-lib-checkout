import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


def _build_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        # heroku-style postgres:// → postgresql://
        return url.replace("postgres://", "postgresql://", 1) if url.startswith("postgres://") else url
    # local dev fallback: construct from individual vars
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db   = os.environ.get("POSTGRES_DB", "library")
    user = os.environ.get("POSTGRES_USER", "library")
    pw   = os.environ.get("POSTGRES_PASSWORD", "library123")
    return f"postgresql://{user}:{pw}@{host}:{port}/{db}"


DATABASE_URL = _build_url()
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
