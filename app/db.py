from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base  # This pulls in all models
import os

engine = None
SessionLocal = None

def init_engine(db_url: str):
    global engine, SessionLocal
    engine = create_engine(db_url, echo=False, future=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine

def init_db(db_url: str):
    engine = init_engine(db_url)
    Base.metadata.create_all(bind=engine)
