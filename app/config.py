from cryptography.fernet import Fernet
import json
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class PasswordEncryptor:
    def __init__(self, key_path: Path):
        self.key_path = key_path
        if not self.key_path.exists():
            key = Fernet.generate_key()
            with open(self.key_path, 'wb') as f:
                f.write(key)
            os.chmod(self.key_path, 0o600)
            logger.info(f"Сгенерирован новый ключ шифрования и сохранён в {self.key_path}")
        else:
            with open(self.key_path, 'rb') as f:
                key = f.read()
            logger.info(f"Загружен ключ шифрования из {self.key_path}")
        self.fernet = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        encrypted = self.fernet.encrypt(plaintext.encode()).decode()
        logger.info("Пароль зашифрован для хранения")
        return encrypted

    def decrypt(self, token: str) -> str:
        try:
            decrypted = self.fernet.decrypt(token.encode()).decode()
            logger.info("Пароль успешно расшифрован")
            return decrypted
        except Exception as e:
            logger.warning(f"Ошибка при расшифровке пароля: {e}")
            raise


class AppSettings:
    """Управление настройками"""

    def __init__(self):
        self.config_dir = Path.home() / '.pharmacy_manager'
        self.config_file = self.config_dir / 'config.json'
        self.key_file = self.config_dir / 'secret.key'
        self.config_dir.mkdir(exist_ok=True)
        self._encryptor = PasswordEncryptor(self.key_file)
        self._settings = self._load_settings()

    def _load_settings(self) -> Dict[str, Any]:
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Загружены настройки из {self.config_file}")
                    return data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Ошибка при загрузке настроек: {e}")
        return {}

    def _save_settings(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
            logger.info(f"Настройки успешно сохранены в {self.config_file}")
        except IOError as e:
            logger.warning(f"Ошибка при сохранении настроек: {e}")

    def get_db_connection_info(self) -> Optional[Dict[str, str]]:
        db_info = self._settings.get('database')
        if db_info and 'password' in db_info:
            try:
                db_info['password'] = self._encryptor.decrypt(db_info['password'])
            except Exception:
                db_info['password'] = ''
        return db_info

    def save_db_connection_info(self, host: str, port: int, database: str,
                                username: str, password: str, remember: bool = False):
        if remember:
            encrypted_password = self._encryptor.encrypt(password)
            self._settings['database'] = {
                'host': host,
                'port': port,
                'database': database,
                'username': username,
                'password': encrypted_password
            }
            logger.info("Информация о подключении к БД сохранена")
        else:
            self._settings.pop('database', None)
            logger.info("Информация о подключении к БД удалена")
        self._save_settings()

    def clear_db_connection_info(self):
        self._settings.pop('database', None)
        self._save_settings()
        logger.info("Информация о подключении к БД очищена")

    def get_window_geometry(self, window_name: str) -> Optional[Dict[str, int]]:
        return self._settings.get('windows', {}).get(window_name)

    def save_window_geometry(self, window_name: str, x: int, y: int, width: int, height: int):
        if 'windows' not in self._settings:
            self._settings['windows'] = {}
        self._settings['windows'][window_name] = {
            'x': x, 'y': y, 'width': width, 'height': height
        }
        self._save_settings()
        logger.info(f"Геометрия окна '{window_name}' сохранена")

    def get_setting(self, key: str, default=None):
        return self._settings.get(key, default)

    def set_setting(self, key: str, value):
        self._settings[key] = value
        self._save_settings()
        logger.info(f"Настройка '{key}' обновлена")
