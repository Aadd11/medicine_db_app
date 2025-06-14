"""
Login window UI
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QCheckBox, QMessageBox,
                            QTabWidget, QGroupBox, QSpinBox, QFormLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from app.auth.auth_manager import auth_manager
from app.database_manager import db_manager
from app.config import AppSettings
from app.ui.database_setup_window import DatabaseSetupWindow
from app.ui.main_window import MainWindow


class LoginWindow(QWidget):
    """Login window"""

    login_successful = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.settings = AppSettings()
        self.main_window = None
        self.db_setup_window = None
        self.user_role = None  # 'admin' или 'user'
        self.init_ui()
        self.load_saved_connection()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Система управления аптекой - Вход")
        self.setFixedSize(400, 500)
        
        # Center window
        self.move(100, 100)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Система управления аптекой")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Tab widget for login/first setup
        self.tab_widget = QTabWidget()
        
        # Login tab
        login_tab = QWidget()
        login_layout = QVBoxLayout(login_tab)
        
        # Database connection group
        db_group = QGroupBox("Подключение к базе данных")
        db_layout = QVBoxLayout(db_group)
        
        self.db_status_label = QLabel("Не подключено")
        self.db_status_label.setStyleSheet("color: red;")
        db_layout.addWidget(self.db_status_label)
        
        self.setup_db_button = QPushButton("Настроить подключение")
        self.setup_db_button.clicked.connect(self.show_database_setup)
        db_layout.addWidget(self.setup_db_button)
        
        login_layout.addWidget(db_group)
        
        # Login form
        login_group = QGroupBox("Вход в систему")
        form_layout = QFormLayout(login_group)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Имя пользователя")
        form_layout.addRow("Пользователь:", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.returnPressed.connect(self.login)
        form_layout.addRow("Пароль:", self.password_input)
        
        self.remember_checkbox = QCheckBox("Запомнить меня")
        form_layout.addWidget(self.remember_checkbox)
        
        self.login_button = QPushButton("Войти")
        self.login_button.clicked.connect(self.login)
        self.login_button.setEnabled(False)
        form_layout.addWidget(self.login_button)
        
        login_layout.addWidget(login_group)
        
        self.tab_widget.addTab(login_tab, "Вход")
        
        # First setup tab
        setup_tab = QWidget()
        setup_layout = QVBoxLayout(setup_tab)
        
        setup_info = QLabel("Первый запуск системы. Создайте учетную запись администратора.")
        setup_info.setWordWrap(True)
        setup_layout.addWidget(setup_info)
        
        setup_group = QGroupBox("Создание администратора")
        setup_form = QFormLayout(setup_group)
        
        self.admin_username_input = QLineEdit()
        self.admin_username_input.setPlaceholderText("admin")
        setup_form.addRow("Имя пользователя:", self.admin_username_input)
        
        self.admin_password_input = QLineEdit()
        self.admin_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        setup_form.addRow("Пароль:", self.admin_password_input)
        
        self.admin_password_confirm = QLineEdit()
        self.admin_password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        setup_form.addRow("Подтвердить пароль:", self.admin_password_confirm)
        
        self.admin_name_input = QLineEdit()
        self.admin_name_input.setPlaceholderText("Имя администратора")
        setup_form.addRow("Имя сотрудника:", self.admin_name_input)
        
        self.create_admin_button = QPushButton("Создать администратора")
        self.create_admin_button.clicked.connect(self.create_admin)
        self.create_admin_button.setEnabled(False)
        setup_form.addWidget(self.create_admin_button)
        
        setup_layout.addWidget(setup_group)
        
        self.tab_widget.addTab(setup_tab, "Первая настройка")
        
        layout.addWidget(self.tab_widget)
        
        self.setLayout(layout)
        
        # Check if first run
        self.check_first_run()

    def load_saved_connection(self):
        db_info = self.settings.get_db_connection_info()
        if db_info:
            success = db_manager.connect(
                db_info['host'], db_info['port'], db_info['database'],
                db_info['username'], db_info['password']
            )
            if success:
                self.update_db_status(True)
                self.check_first_run()

                if db_info['username'] == 'pharmacy_user':
                    self.user_role = 'user'
                else:
                    self.user_role = 'admin'

    def show_database_setup(self):
        if not self.db_setup_window:
            self.db_setup_window = DatabaseSetupWindow()
            self.db_setup_window.connection_successful.connect(self.on_db_connected)
        self.db_setup_window.show()
        self.db_setup_window.raise_()

    def on_db_connected(self):
        self.update_db_status(True)
        self.check_first_run()
        db_info = self.settings.get_db_connection_info()
        if db_info:
            if db_info['username'] == 'pharmacy_user':
                self.user_role = 'user'
            else:
                self.user_role = 'admin'
        if self.db_setup_window:
            self.db_setup_window.close()

    def update_db_status(self, connected: bool):
        if connected:
            self.db_status_label.setText("Подключено")
            self.db_status_label.setStyleSheet("color: green;")
            self.login_button.setEnabled(True)
            self.create_admin_button.setEnabled(True)
        else:
            self.db_status_label.setText("Не подключено")
            self.db_status_label.setStyleSheet("color: red;")
            self.login_button.setEnabled(False)
            self.create_admin_button.setEnabled(False)

    def check_first_run(self):
        if db_manager.is_connected:
            if auth_manager.is_first_run():
                self.tab_widget.setCurrentIndex(1)
            else:
                self.tab_widget.setCurrentIndex(0)

    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        remember_me = self.remember_checkbox.isChecked()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Введите имя пользователя и пароль")
            return

        if auth_manager.authenticate(username, password, remember_me):
            self.open_main_window()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверное имя пользователя или пароль")

    def create_admin(self):
        username = self.admin_username_input.text().strip()
        password = self.admin_password_input.text()
        confirm_password = self.admin_password_confirm.text()
        employee_name = self.admin_name_input.text().strip()

        if not all([username, password, confirm_password, employee_name]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")
            return

        if len(password) < 6:
            QMessageBox.warning(self, "Ошибка", "Пароль должен содержать минимум 6 символов")
            return

        if auth_manager.create_admin_user(username, password, employee_name):
            QMessageBox.information(self, "Успех", "Администратор создан успешно!")
            self.tab_widget.setCurrentIndex(0)
            self.admin_username_input.clear()
            self.admin_password_input.clear()
            self.admin_password_confirm.clear()
            self.admin_name_input.clear()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось создать администратора")

    def open_main_window(self):
        if not self.main_window:
            self.main_window = MainWindow()
        self.main_window.show()
        self.hide()

    def closeEvent(self, event):
        if self.main_window:
            self.main_window.close()
        event.accept()
