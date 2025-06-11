# db.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
from app.config import load_db_config

DEFAULT_DB_URL = "postgresql://postgres:1465@localhost:5432/med_db_test"

_engine = None
_SessionLocal = None

def init_engine(db_url: str = None):
    global _engine, _SessionLocal
    if not db_url:
        db_url = load_db_config() or DEFAULT_DB_URL
    _engine = create_engine(db_url, echo=False, future=True)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine

def init_db(db_url: str = None):
    engine = init_engine(db_url)
    Base.metadata.create_all(bind=engine)

def get_session():
    if _SessionLocal is None:
        raise RuntimeError("Сессия не инициализирована — вызови init_engine() сначала.")
    return _SessionLocal()
