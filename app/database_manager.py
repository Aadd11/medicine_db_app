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

            logger.info(f"Успешное подключение к базе данных {database}")
            return True

        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
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
        #        self.create_readonly_user()
                return True

        except Exception as e:
            logger.error(f"Ошибка при создании базы данных: {e}")
            return False

        return False

    def create_tables(self):
        """Создание таблиц"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Таблицы базы данных успешно созданы")
        except Exception as e:
            logger.error(f"Ошибка при создании таблиц: {e}")
            raise

    def create_readonly_user(self, admin_username=None, admin_password=None, readonly_user='pharmacy_user',
                             readonly_pass='readonly123') -> bool:
        """Создаёт read-only пользователя через подключение от имени администратора"""
        if not admin_username or not admin_password:
            logger.error("Не переданы данные администратора для создания read-only пользователя")
            return False

        conn_str = f"postgresql+psycopg2://{admin_username}:{admin_password}@{self._connection_params['host']}:{self._connection_params['port']}/{self._connection_params['database']}"

        try:
            logger.info("Подключение к базе от имени администратора: %s", admin_username)
            admin_engine = create_engine(conn_str, echo=False)
            with admin_engine.begin() as conn:
                # Проверка существования пользователя
                logger.debug("Выполняем проверку наличия пользователя %s", readonly_user)
                result = conn.execute(
                    text("SELECT 1 FROM pg_roles WHERE rolname = :username"),
                    {"username": readonly_user}
                ).scalar()

                if not result:
                    logger.info("Пользователь %s не существует. Создаём.", readonly_user)
                    query = f"CREATE USER {readonly_user} WITH PASSWORD :pwd"
                    logger.debug("SQL: %s", query)
                    conn.execute(text(query), {"pwd": readonly_pass})
                else:
                    logger.info("Пользователь %s уже существует. Пропускаем создание.", readonly_user)

                dbname = self._connection_params['database']

                queries = [
                    f"GRANT CONNECT ON DATABASE {dbname} TO {readonly_user};",
                    f"GRANT USAGE ON SCHEMA public TO {readonly_user};",
                    f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {readonly_user};",
                    f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO {readonly_user};"
                ]

                for sql in queries:
                    try:
                        logger.debug("Выполняем SQL: %s", sql)
                        conn.execute(text(sql))
                    except Exception as e:
                        logger.error("Ошибка при выполнении запроса: %s\n%s", sql, e)
                        raise

                logger.info("Права SELECT успешно выданы пользователю %s", readonly_user)
                return True

        except Exception as e:
            logger.exception("Ошибка при создании read-only пользователя: %s", e)
            return False

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
            logger.info("Отключение от базы данных")

    @property
    def is_connected(self) -> bool:
        """Проверка текущего подключения"""
        return self.engine is not None and self.test_connection()

    @property
    def connection_params(self) -> Optional[dict]:
        """Получение текущих параметров подключения"""
        return self._connection_params.copy() if self._connection_params else None


db_manager = DatabaseManager()
