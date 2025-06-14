"""
User Management Window — управление пользователями базы данных
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QLineEdit, QMessageBox, QComboBox, QInputDialog
)
from PyQt6.QtCore import Qt

from app.auth.auth_manager import auth_manager
from app.database_manager import db_manager

logger = logging.getLogger(__name__)


class UserManagementWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление пользователями")
        self.setMinimumSize(600, 400)

        self.init_ui()
        self.load_users()

    def init_ui(self):
        layout = QVBoxLayout()


        title = QLabel("Пользователи")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)


        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Логин", "Имя", "Роль"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        # Форма добавления/редактирования
        form_layout = QHBoxLayout()
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Логин")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Имя")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.role_input = QComboBox()
        self.role_input.addItems(["user", "admin"])

        form_layout.addWidget(self.username_input)
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(self.role_input)

        layout.addLayout(form_layout)


        btn_layout = QHBoxLayout()

        self.add_btn = QPushButton("Добавить")
        self.edit_btn = QPushButton("Редактировать")
        self.delete_btn = QPushButton("Удалить")
        self.update_rights_btn = QPushButton("Обновить права pharmacy_user")

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.update_rights_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)


        self.add_btn.clicked.connect(self.create_user)
        self.edit_btn.clicked.connect(self.edit_user)
        self.delete_btn.clicked.connect(self.delete_user)
        self.update_rights_btn.clicked.connect(self.refresh_readonly_rights)

    def load_users(self):
        try:
            users = auth_manager.get_all_users()
            self.table.setRowCount(len(users))
            for row, user in enumerate(users):
                self.table.setItem(row, 0, QTableWidgetItem(str(user[0])))  # username
                self.table.setItem(row, 1, QTableWidgetItem(str(user[1])))  # employee_name
                self.table.setItem(row, 2, QTableWidgetItem(str(user[2])))  # role
            logger.info("Загружены пользователи: %d", len(users))
        except Exception as e:
            logger.exception("Ошибка загрузки пользователей: %s", e)

    def create_user(self):
        username = self.username_input.text().strip()
        name = self.name_input.text().strip()
        password = self.password_input.text()
        role = self.role_input.currentText()

        if not username or not name or not password:
            QMessageBox.warning(self, "Ошибка", "Все поля обязательны")
            return

        try:
            success = auth_manager.create_user(username, password, name, role)
            if success:
                QMessageBox.information(self, "Успех", "Пользователь добавлен")
                logger.info("Создан пользователь: %s", username)
                self.load_users()
            else:
                logger.warning("Не удалось создать пользователя: %s", username)
                QMessageBox.warning(self, "Ошибка", "Не удалось создать пользователя")
        except Exception as e:
            logger.exception("Ошибка создания пользователя: %s", e)
            QMessageBox.critical(self, "Ошибка", f"{e}")

    def edit_user(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя")
            return

        username = self.table.item(row, 0).text()
        name = self.name_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_input.currentText()

        if not name:
            QMessageBox.warning(self, "Ошибка", "Имя не может быть пустым")
            return

        try:
            success = auth_manager.update_user(username, name, password, role)
            if success:
                QMessageBox.information(self, "Успех", "Пользователь обновлён")
                logger.info("Пользователь обновлён: %s", username)
                self.load_users()
            else:
                QMessageBox.warning(self, "Ошибка", "Ошибка обновления")
        except Exception as e:
            logger.exception("Ошибка при обновлении пользователя: %s", e)
            QMessageBox.critical(self, "Ошибка", f"{e}")

    def delete_user(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя")
            return

        username = self.table.item(row, 0).text()
        confirm = QMessageBox.question(self, "Удаление", f"Удалить пользователя {username}?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                if auth_manager.delete_user(username):
                    QMessageBox.information(self, "Удалено", "Пользователь удалён")
                    logger.info("Пользователь удалён: %s", username)
                    self.load_users()
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось удалить пользователя")
            except Exception as e:
                logger.exception("Ошибка при удалении пользователя: %s", e)
                QMessageBox.critical(self, "Ошибка", f"{e}")

    def refresh_readonly_rights(self):
        admin_user, ok1 = QInputDialog.getText(self, "Имя администратора", "Введите логин администратора PostgreSQL:")
        if not ok1 or not admin_user:
            return

        admin_pass, ok2 = QInputDialog.getText(self, "Пароль администратора", "Введите пароль:", QLineEdit.EchoMode.Password)
        if not ok2 or not admin_pass:
            return

        try:
            if db_manager.create_readonly_user(admin_username=admin_user, admin_password=admin_pass):
                logger.info("Права pharmacy_user обновлены")
                QMessageBox.information(self, "Успех", "Права для pharmacy_user обновлены")
            else:
                logger.warning("Не удалось обновить права pharmacy_user")
                QMessageBox.warning(self, "Ошибка", "Не удалось обновить права")
        except Exception as e:
            logger.exception("Ошибка обновления прав pharmacy_user: %s", e)
            QMessageBox.critical(self, "Ошибка", f"{e}")
