"""
Database setup window
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QCheckBox, QMessageBox,
                            QTabWidget, QGroupBox, QSpinBox, QFormLayout,
                            QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont

from app.database_manager import db_manager
from app.config import AppSettings


class DatabaseWorker(QThread):
    """Worker thread for database operations"""

    finished = pyqtSignal(bool, str)

    def __init__(self, operation, **kwargs):
        super().__init__()
        self.operation = operation
        self.kwargs = kwargs

    def run(self):
        try:
            if self.operation == 'connect':
                success = db_manager.connect(**self.kwargs)
                self.finished.emit(success, "Подключение" if success else "Ошибка подключения")
            elif self.operation == 'create':
                success = db_manager.create_database(**self.kwargs)
                self.finished.emit(success, "База данных создана" if success else "Ошибка создания")
        except Exception as e:
            self.finished.emit(False, str(e))


class DatabaseSetupWindow(QWidget):
    """Database setup window"""

    connection_successful = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.settings = AppSettings()
        self.worker = None
        self._admin_params = None  # Временное хранилище параметров администратора
        self.init_ui()
        self.load_saved_settings()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Настройка базы данных")
        self.setFixedSize(450, 400)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Настройка подключения к PostgreSQL")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # Connect tab
        connect_tab = QWidget()
        connect_layout = QVBoxLayout(connect_tab)
        
        connect_group = QGroupBox("Подключение к существующей базе данных")
        connect_form = QFormLayout(connect_group)
        
        self.connect_host_input = QLineEdit("localhost")
        connect_form.addRow("Хост:", self.connect_host_input)
        
        self.connect_port_input = QSpinBox()
        self.connect_port_input.setRange(1, 65535)
        self.connect_port_input.setValue(5432)
        connect_form.addRow("Порт:", self.connect_port_input)
        
        self.connect_database_input = QLineEdit()
        self.connect_database_input.setPlaceholderText("pharmacy_db")
        connect_form.addRow("База данных:", self.connect_database_input)
        
        self.connect_username_input = QLineEdit()
        self.connect_username_input.setPlaceholderText("postgres")
        connect_form.addRow("Пользователь:", self.connect_username_input)
        
        self.connect_password_input = QLineEdit()
        self.connect_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        connect_form.addRow("Пароль:", self.connect_password_input)
        
        self.connect_remember_checkbox = QCheckBox("Сохранить настройки подключения")
        connect_form.addWidget(self.connect_remember_checkbox)
        
        self.connect_button = QPushButton("Подключиться")
        self.connect_button.clicked.connect(self.connect_to_database)
        connect_form.addWidget(self.connect_button)
        
        connect_layout.addWidget(connect_group)
        
        tab_widget.addTab(connect_tab, "Подключение")
        
        # Create tab
        create_tab = QWidget()
        create_layout = QVBoxLayout(create_tab)
        
        create_group = QGroupBox("Создание новой базы данных")
        create_form = QFormLayout(create_group)
        
        self.create_host_input = QLineEdit("localhost")
        create_form.addRow("Хост:", self.create_host_input)
        
        self.create_port_input = QSpinBox()
        self.create_port_input.setRange(1, 65535)
        self.create_port_input.setValue(5432)
        create_form.addRow("Порт:", self.create_port_input)
        
        self.create_database_input = QLineEdit("pharmacy_db")
        create_form.addRow("Имя базы данных:", self.create_database_input)
        
        self.create_username_input = QLineEdit()
        self.create_username_input.setPlaceholderText("postgres")
        create_form.addRow("Пользователь:", self.create_username_input)
        
        self.create_password_input = QLineEdit()
        self.create_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        create_form.addRow("Пароль:", self.create_password_input)
        
        self.create_remember_checkbox = QCheckBox("Сохранить настройки подключения")
        create_form.addWidget(self.create_remember_checkbox)
        
        self.create_button = QPushButton("Создать базу данных")
        self.create_button.clicked.connect(self.create_database)
        create_form.addWidget(self.create_button)
        
        create_layout.addWidget(create_group)
        
        tab_widget.addTab(create_tab, "Создание")
        
        layout.addWidget(tab_widget)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.test_button = QPushButton("Тест подключения")
        self.test_button.clicked.connect(self.test_connection)
        button_layout.addWidget(self.test_button)
        
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.close)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_saved_settings(self):
        db_info = self.settings.get_db_connection_info()
        if db_info:
            self.connect_host_input.setText(db_info.get('host', 'localhost'))
            self.connect_port_input.setValue(db_info.get('port', 5432))
            self.connect_database_input.setText(db_info.get('database', ''))
            self.connect_username_input.setText(db_info.get('username', ''))
            self.connect_password_input.setText(db_info.get('password', ''))
            self.connect_remember_checkbox.setChecked(True)

    def get_connection_params(self, tab_type='connect'):
        if tab_type == 'connect':
            return {
                'host': self.connect_host_input.text().strip() or 'localhost',
                'port': self.connect_port_input.value(),
                'database': self.connect_database_input.text().strip(),
                'username': self.connect_username_input.text().strip(),
                'password': self.connect_password_input.text(),
                'remember': self.connect_remember_checkbox.isChecked()
            }
        else:
            return {
                'host': self.create_host_input.text().strip() or 'localhost',
                'port': self.create_port_input.value(),
                'database': self.create_database_input.text().strip(),
                'username': self.create_username_input.text().strip(),
                'password': self.create_password_input.text(),
                'remember': self.create_remember_checkbox.isChecked()
            }

    def validate_params(self, params):
        if not params['database']:
            QMessageBox.warning(self, "Ошибка", "Введите имя базы данных")
            return False
        if not params['username']:
            QMessageBox.warning(self, "Ошибка", "Введите имя пользователя")
            return False
        return True

    def start_operation(self, operation, params):
        if self.worker and self.worker.isRunning():
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("Подключение...")

        self.connect_button.setEnabled(False)
        self.create_button.setEnabled(False)
        self.test_button.setEnabled(False)

        self.worker = DatabaseWorker(operation, **params)
        self.worker.finished.connect(self.on_operation_finished)
        self.worker.start()

    def on_operation_finished(self, success, message):
        self.progress_bar.setVisible(False)
        self.status_label.setText(message)

        self.connect_button.setEnabled(True)
        self.create_button.setEnabled(True)
        self.test_button.setEnabled(True)

        if success:
            # При подключении сохраняем введённые данные (не admin!)
            if self._admin_params:
                params = self._admin_params
                readonly_user = 'pharmacy_user'
                readonly_pass = 'readonly123'
                if params.get('remember'):
                    self.settings.save_db_connection_info(
                        params['host'], params['port'], params['database'],
                        readonly_user, readonly_pass, True
                    )
                self._admin_params = None

            QMessageBox.information(self, "Успех", message)
            self.connection_successful.emit()
        else:
            QMessageBox.warning(self, "Ошибка", message)

    def connect_to_database(self):
        params = self.get_connection_params('connect')
        if not self.validate_params(params):
            return

        remember = params.pop('remember')  # убираем
        self._admin_params = params.copy()
        self._admin_params['remember'] = remember  # но сохраняем флаг отдельно
        self.start_operation('connect', params)

    def create_database(self):
        params = self.get_connection_params('create')
        if not self.validate_params(params):
            return

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Создать новую базу данных '{params['database']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            remember = params.pop('remember')
            self._admin_params = params.copy()
            self._admin_params['remember'] = remember
            self.start_operation('create', params)

    def test_connection(self):
        params = self.get_connection_params('connect')
        if not self.validate_params(params):
            return

        params.pop('remember')

        try:
            import psycopg2
            conn = psycopg2.connect(
                host=params['host'],
                port=params['port'],
                database=params['database'],
                user=params['username'],
                password=params['password']
            )
            conn.close()
            QMessageBox.information(self, "Успех", "Подключение успешно!")
            self.status_label.setText("Тест подключения: Успех")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось подключиться: {str(e)}")
            self.status_label.setText("Тест подключения: Ошибка")
