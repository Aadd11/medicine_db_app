import hashlib
import secrets
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.employee import Employee
from app.database_manager import db_manager


class AuthManager:
    """Authentication manager"""

    def __init__(self):
        self.current_user = None
        self.current_employee = None

    @staticmethod
    def hash_password(password: str) -> str:
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        try:
            salt, password_hash = hashed.split(':')
            return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
        except ValueError:
            return False

    def is_first_run(self) -> bool:
        session = db_manager.get_session()
        if not session:
            return True

        try:
            user_count = session.query(func.count(User.id)).scalar()
            return user_count == 0
        except Exception as e:
            print(f"[ERROR] Ошибка при проверке is_first_run: {e}")
            return True
        finally:
            session.close()

    def create_admin_user(self, username: str, password: str, employee_name: str,
                          position: str = "Администратор") -> bool:
        session = db_manager.get_session()
        if not session:
            print("[ERROR] Нет соединения с базой данных")
            return False

        try:
            # Проверка на существующего пользователя
            existing_user = session.query(User).filter(User.username == username).first()
            if existing_user:
                raise ValueError("Пользователь с таким именем уже существует")

            # Создание сотрудника
            employee = Employee(
                name=employee_name,
                position=position,
                salary=0.0
            )
            session.add(employee)
            session.flush()  # Получаем ID

            # Создание пользователя
            user = User(
                employee_id=employee.id,
                username=username,
                password_hash=self.hash_password(password),
                role='admin'
            )
            session.add(user)
            session.commit()

            return True

        except Exception as e:
            session.rollback()
            print(f"[ERROR] Ошибка при создании администратора: {e}")
            raise  # пробрасываем исключение для UI
        finally:
            session.close()

    def authenticate(self, username: str, password: str) -> bool:
        session = db_manager.get_session()
        if not session:
            return False

        try:
            user = session.query(User).filter(User.username == username).first()
            if user and self.verify_password(password, user.password_hash):
                self.current_user = user
                self.current_employee = user.employee
                return True
        except Exception as e:
            print(f"[ERROR] Ошибка при аутентификации: {e}")
        finally:
            session.close()

        return False

    def logout(self):
        if self.current_user:
            session = db_manager.get_session()
            if session:
                try:
                    user = session.query(User).get(self.current_user.id)
                    if user:
                        user.remember_me = False
                        session.commit()
                except Exception as e:
                    print(f"[ERROR] Ошибка при выходе: {e}")
                finally:
                    session.close()

        self.current_user = None
        self.current_employee = None

    def create_user(self, username: str, password: str, employee_name: str,
                    position: str, salary: float = 0.0, role: str = 'user') -> bool:
        if not self.is_admin():
            return False

        session = db_manager.get_session()
        if not session:
            return False

        try:
            existing_user = session.query(User).filter(User.username == username).first()
            if existing_user:
                raise ValueError("Пользователь с таким именем уже существует")

            employee = Employee(
                name=employee_name,
                position=position,
                salary=salary
            )
            session.add(employee)
            session.flush()

            user = User(
                employee_id=employee.id,
                username=username,
                password_hash=self.hash_password(password),
                role=role
            )
            session.add(user)
            session.commit()

            return True

        except Exception as e:
            session.rollback()
            print(f"[ERROR] Ошибка при создании пользователя: {e}")
            return False
        finally:
            session.close()

    def get_all_users(self) -> list:
        if not self.is_admin():
            return []

        session = db_manager.get_session()
        if not session:
            return []

        try:
            users = session.query(User).join(Employee).all()
            return [(u.id, u.username, u.employee.name, u.employee.position, u.role)
                    for u in users]
        except Exception as e:
            print(f"[ERROR] Ошибка при получении списка пользователей: {e}")
            return []
        finally:
            session.close()

    def delete_user(self, user_id: int) -> bool:
        if not self.is_admin() or user_id == self.current_user.id:
            return False

        session = db_manager.get_session()
        if not session:
            return False

        try:
            user = session.query(User).get(user_id)
            if user:
                employee = user.employee
                session.delete(user)
                if employee:
                    session.delete(employee)
                session.commit()
                return True
        except Exception as e:
            session.rollback()
            print(f"[ERROR] Ошибка при удалении пользователя: {e}")
        finally:
            session.close()

        return False

    def is_authenticated(self) -> bool:
        return self.current_user is not None

    def is_admin(self) -> bool:
        return self.current_user and self.current_user.role == 'admin'

    def get_current_user_info(self) -> Optional[Tuple[str, str, str]]:
        if self.current_user and self.current_employee:
            return (self.current_user.username,
                    self.current_employee.name,
                    self.current_user.role)
        return None


# Глобальный экземпляр
auth_manager = AuthManager()
