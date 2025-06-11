import sys
import re
import psycopg2
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from app.db import init_db
from app.config import save_db_config

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 5432
DEFAULT_USER = 'postgres'
DEFAULT_PASSWORD = '1465'

class DBSetupWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Настройка базы данных")
        self.setMinimumWidth(300)

        layout = QVBoxLayout()

        self.db_name_input = QLineEdit()
        self.db_name_input.setPlaceholderText("Введите имя базы данных")

        self.create_button = QPushButton("Создать и подключиться")
        self.create_button.clicked.connect(self.create_and_connect)

        layout.addWidget(QLabel("Имя новой или существующей базы данных:"))
        layout.addWidget(self.db_name_input)
        layout.addWidget(self.create_button)

        self.setLayout(layout)

    def create_and_connect(self):
        db_name = self.db_name_input.text().strip()
        if not db_name:
            QMessageBox.warning(self, "Ошибка", "Введите имя базы данных")
            return

        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", db_name):
            QMessageBox.warning(
                self, "Ошибка",
                "Имя базы данных должно начинаться с буквы или подчёркивания и содержать только буквы, цифры или подчёркивания"
            )
            return

        try:
            conn = psycopg2.connect(
                dbname='postgres', user=DEFAULT_USER,
                password=DEFAULT_PASSWORD, host=DEFAULT_HOST, port=DEFAULT_PORT
            )
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            exists = cursor.fetchone()
            if not exists:
                cursor.execute(f'CREATE DATABASE "{db_name}"')
                QMessageBox.information(self, "Успех", f"База данных '{db_name}' создана")
            conn.close()

            db_url = f"postgresql://{DEFAULT_USER}:{DEFAULT_PASSWORD}@{DEFAULT_HOST}:{DEFAULT_PORT}/{db_name}"
            init_db(db_url)
            save_db_config(db_url)
            QMessageBox.information(self, "Готово", "Подключение выполнено и таблицы созданы")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DBSetupWindow()
    window.show()
    sys.exit(app.exec())
