"""
Настройки приложения
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any


class AppSettings:
    """Управление настройками"""

    def __init__(self):
        self.config_dir = Path.home() / '.pharmacy_manager'
        self.config_file = self.config_dir / 'config.json'
        self.config_dir.mkdir(exist_ok=True)
        self._settings = self._load_settings()

    def _load_settings(self) -> Dict[str, Any]:
        """Загрузить конфиг из файла"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def _save_settings(self):
        """Сохранить конфиг в файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except IOError:
            pass

    def get_db_connection_info(self) -> Optional[Dict[str, str]]:
        """Получить информацию о подключении"""
        return self._settings.get('database')

    def save_db_connection_info(self, host: str, port: int, database: str,
                                username: str, password: str, remember: bool = False):
        """Сохранить информацию о подключении"""
        if remember:
            self._settings['database'] = {
                'host': host,
                'port': port,
                'database': database,
                'username': username,
                'password': password
            }
        else:
            self._settings.pop('database', None)
        self._save_settings()

    def clear_db_connection_info(self):
        """Очистить информацию о подключении"""
        self._settings.pop('database', None)
        self._save_settings()

    def get_window_geometry(self, window_name: str) -> Optional[Dict[str, int]]:
        """Получить размеры окна"""
        return self._settings.get('windows', {}).get(window_name)

    def save_window_geometry(self, window_name: str, x: int, y: int, width: int, height: int):
        """Сохранить размеры окна"""
        if 'windows' not in self._settings:
            self._settings['windows'] = {}
        self._settings['windows'][window_name] = {
            'x': x, 'y': y, 'width': width, 'height': height
        }
        self._save_settings()

    def get_setting(self, key: str, default=None):
        """получить параметр настройки"""
        return self._settings.get(key, default)

    def set_setting(self, key: str, value):
        """установить параметр"""
        self._settings[key] = value
        self._save_settings()
