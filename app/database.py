import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_URL = f"sqlite:///{ROOT / 'accounting.db'}"

class Base(DeclarativeBase):
    pass

def make_engine(url: str | None = None):
    url = url or os.getenv("DATABASE_URL", DEFAULT_URL)
    engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def enable_fk(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
    return engine

engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False)

def get_db():
    with SessionLocal() as db:
        yield db
