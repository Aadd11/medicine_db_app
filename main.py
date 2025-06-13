#!/usr/bin/env python3
"""
Система управления аптекой
Главная точка входа
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTranslator, QLocale
from app.ui.login_window import LoginWindow
from app.config import AppSettings


def main():
    """Главная точка входа"""
    app = QApplication(sys.argv)
    app.setApplicationName("Pharmacy Management System")
    app.setApplicationVersion("1.0.0")

    app.setStyleSheet("""
           QMainWindow {
               background-color: #2b2b2b;
               color: #ffffff;
           }
           QPushButton {
               background-color: #4caf50;
               color: #ffffff;
               border: none;
               padding: 8px 16px;
               border-radius: 4px;
               font-weight: bold;
           }
           QPushButton:hover {
               background-color: #45a045;
           }
           QPushButton:pressed {
               background-color: #3c8e3c;
           }
           QTableWidget {
               gridline-color: #3c3c3c;
               background-color: #2b2b2b;
               alternate-background-color: #242424;
               color: #ffffff;
           }
           QHeaderView::section {
               background-color: #3c3c3c;
               color: #ffffff;
               padding: 8px;
               border: 1px solid #555555;
               font-weight: bold;
           }
           QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit {
               background-color: #3c3c3c;
               color: #ffffff;
               border: 1px solid #555555;
           }
           QTabBar::tab {
               background: #3c3c3c;
               color: #ffffff;
               padding: 6px;
           }
           QTabBar::tab:selected {
               background: #4caf50;
           }
       """)


    settings = AppSettings()


    login_window = LoginWindow()
    login_window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
