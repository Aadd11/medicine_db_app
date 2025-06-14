"""
Main application window
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QMenuBar, QPushButton, QLabel, QMessageBox,
                            QStackedWidget, QFrame)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QAction

from app.auth.auth_manager import auth_manager
from app.database_manager import db_manager
from app.ui.view_window import ViewWindow
from app.ui.edit_window import EditWindow
from app.ui.user_management_window import UserManagementWindow

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.view_window = None
        self.edit_window = None
        self.user_management_window = None
        self.init_ui()
        self.start_auto_refresh()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Система управления аптекой")
        self.setMinimumSize(1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Top menu bar
        self.create_menu_bar()
        
        # User info and navigation
        nav_layout = QHBoxLayout()
        
        # Navigation buttons
        self.view_button = QPushButton("Просмотр")
        self.view_button.setCheckable(True)
        self.view_button.setChecked(True)
        self.view_button.clicked.connect(self.show_view_mode)
        nav_layout.addWidget(self.view_button)
        if auth_manager.is_admin():
            self.edit_button = QPushButton("Редактирование")
            self.edit_button.setCheckable(True)
            self.edit_button.clicked.connect(self.show_edit_mode)
            nav_layout.addWidget(self.edit_button)

        
        # Admin-only buttons
        if auth_manager.is_admin():
            self.users_button = QPushButton("Пользователи")
            self.users_button.clicked.connect(self.show_user_management)
            nav_layout.addWidget(self.users_button)
        
        nav_layout.addStretch()
        
        # User info
        user_info = auth_manager.get_current_user_info()
        if user_info:
            username, employee_name, role = user_info
            role_text = "Администратор" if role == 'admin' else "Пользователь"
            self.user_label = QLabel(f"{employee_name} ({role_text})")
            self.user_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            nav_layout.addWidget(self.user_label)
        
        # Logout button
        self.logout_button = QPushButton("Выход")
        self.logout_button.clicked.connect(self.logout)
        nav_layout.addWidget(self.logout_button)
        
        layout.addLayout(nav_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Content area
        self.content_widget = QStackedWidget()
        layout.addWidget(self.content_widget)
        
        # Initialize view mode by default
        self.show_view_mode()
        
        # Update button states

    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('Файл')
        
        refresh_action = QAction('Обновить', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_data)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        logout_action = QAction('Выход', self)
        logout_action.triggered.connect(self.logout)
        file_menu.addAction(logout_action)
        
        # Help menu
        help_menu = menubar.addMenu('Справка')
        
        about_action = QAction('О программе', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def show_view_mode(self):
        """Show view mode"""
        if not self.view_window:
            self.view_window = ViewWindow()
        
        self.content_widget.addWidget(self.view_window)
        self.content_widget.setCurrentWidget(self.view_window)

    def show_edit_mode(self):
        """Show edit mode (admin only)"""
        if not auth_manager.is_admin():
            QMessageBox.warning(self, "Доступ запрещен",
                              "Режим редактирования доступен только администраторам")
            return

        if not self.edit_window:
            self.edit_window = EditWindow()

        self.content_widget.addWidget(self.edit_window)
        self.content_widget.setCurrentWidget(self.edit_window)

        self.view_button.setChecked(False)
        self.edit_button.setChecked(True)
    def show_user_management(self):
        """Show user management window (admin only)"""
        if not auth_manager.is_admin():
            return

        if not self.user_management_window:
            self.user_management_window = UserManagementWindow()

        self.user_management_window.show()
        self.user_management_window.raise_()
    
    def refresh_data(self):
        """Refresh data in current view"""
        current_widget = self.content_widget.currentWidget()
        if hasattr(current_widget, 'refresh_data'):
            current_widget.refresh_data()
    
    def start_auto_refresh(self):
        """Start auto-refresh timer"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "О программе",
            "Система управления аптекой\n"
            "Версия 1.0.0\n\n"
            "Программа для управления аптечным бизнесом\n"
            "с функциями учета товаров, продаж и клиентов."
        )
    
    def logout(self):
        """Logout user"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Вы действительно хотите выйти из системы?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self, 'refresh_timer'):
                self.refresh_timer.stop()

            if self.user_management_window:
                self.user_management_window.close()

            auth_manager.logout()

            from app.ui.login_window import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()
            
            self.close()
    
    def closeEvent(self, event):
        """Handle window close event"""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()

        if self.user_management_window:
            self.user_management_window.close()
        
        event.accept()
