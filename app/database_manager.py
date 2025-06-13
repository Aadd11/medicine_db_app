"""
Управление и подключение к бд
"""

import logging
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from app.models.base import Base
from app.models import *  # Import all models

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Управление и подключение к бд"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._connection_params = None
    
    def connect(self, host: str, port: int, database: str, username: str, password: str) -> bool:
        """Connect to existing database"""
        try:
            connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            self.engine = create_engine(connection_string, echo=False)
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.SessionLocal = sessionmaker(bind=self.engine)
            self._connection_params = {
                'host': host, 'port': port, 'database': database,
                'username': username, 'password': password
            }
            
            logger.info(f"Successfully connected to database {database}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def create_database(self, host: str, port: int, database: str, username: str, password: str) -> bool:
        """Создание бд и инициализация схемы"""
        try:

            postgres_conn = psycopg2.connect(
                host=host, port=port, database='postgres',
                user=username, password=password
            )
            postgres_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            with postgres_conn.cursor() as cursor:

                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (database,)
                )
                if cursor.fetchone():
                    postgres_conn.close()
                    return self.connect(host, port, database, username, password)
                

                cursor.execute(
                    sql.SQL("CREATE DATABASE {}").format(
                        sql.Identifier(database)
                    )
                )
            
            postgres_conn.close()
            

            if self.connect(host, port, database, username, password):
                self.create_tables()
                return True
            
        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            return False
        
        return False
    
    def create_tables(self):
        """Создание таблиц"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def get_session(self) -> Optional[Session]:
        """Get database session"""
        if self.SessionLocal:
            return self.SessionLocal()
        return None
    
    def test_connection(self) -> bool:
        """проверка подключения"""
        if not self.engine:
            return False
        
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
    
    def disconnect(self):
        """Отключение от бд"""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.SessionLocal = None
            self._connection_params = None
            logger.info("Disconnected from database")
    
    @property
    def is_connected(self) -> bool:
        """Проверка текущего подключения"""
        return self.engine is not None and self.test_connection()
    
    @property
    def connection_params(self) -> Optional[dict]:
        """Получение текущих параметров подключсения"""
        return self._connection_params.copy() if self._connection_params else None


db_manager = DatabaseManager()
