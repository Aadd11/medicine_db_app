"""
Edit window with CRUD operations for all entities (Admin only)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QTableWidget, QTableWidgetItem, QPushButton, QLabel,
                            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
                            QCheckBox, QDateEdit, QTextEdit, QFormLayout,
                            QDialog, QDialogButtonBox, QMessageBox, QGroupBox,
                            QScrollArea, QFrame, QHeaderView, QMenu)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QAction

from datetime import date, datetime
import re
from typing import Optional, List, Dict, Any

from app.auth.auth_manager import auth_manager
from app.database_manager import db_manager
from app.models import *
from sqlalchemy.orm import joinedload
from sqlalchemy import func, or_

class FormDialog(QDialog):
    """Generic form dialog for CRUD operations"""

    def __init__(self, title: str, fields: List[Dict], parent=None, existing_data: Dict = None):
        super().__init__(parent)
        self.fields = fields
        self.existing_data = existing_data or {}
        self.field_widgets = {}
        self.init_ui(title)

    def init_ui(self, title: str):
        """Initialize form UI"""
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)

        # Create scroll area for form
        scroll = QScrollArea()
        scroll_widget = QWidget()
        form_layout = QFormLayout(scroll_widget)

        # Create form fields
        for field in self.fields:
            label = QLabel(field['label'])
            widget = self.create_field_widget(field)
            self.field_widgets[field['name']] = widget
            form_layout.addRow(label, widget)

        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def create_field_widget(self, field: Dict) -> QWidget:
        """Create appropriate widget for field type"""
        field_type = field['type']
        name = field['name']

        if field_type == 'text':
            widget = QLineEdit()
            if name in self.existing_data:
                widget.setText(str(self.existing_data[name]))
            if field.get('placeholder'):
                widget.setPlaceholderText(field['placeholder'])

        elif field_type == 'number':
            widget = QSpinBox()
            widget.setMinimum(field.get('min', 0))
            widget.setMaximum(field.get('max', 999999))
            if name in self.existing_data:
                widget.setValue(int(self.existing_data[name] or 0))

        elif field_type == 'decimal':
            widget = QDoubleSpinBox()
            widget.setMinimum(field.get('min', 0.0))
            widget.setMaximum(field.get('max', 999999.99))
            widget.setDecimals(2)
            if name in self.existing_data:
                widget.setValue(float(self.existing_data[name] or 0))

        elif field_type == 'checkbox':
            widget = QCheckBox()
            if name in self.existing_data:
                widget.setChecked(bool(self.existing_data[name]))

        elif field_type == 'date':
            widget = QDateEdit()
            widget.setCalendarPopup(True)
            if name in self.existing_data and self.existing_data[name]:
                if isinstance(self.existing_data[name], str):
                    date_obj = datetime.strptime(self.existing_data[name], '%Y-%m-%d').date()
                else:
                    date_obj = self.existing_data[name]
                widget.setDate(QDate.fromString(date_obj.strftime('%Y-%m-%d'), 'yyyy-MM-dd'))
            else:
                widget.setDate(QDate.currentDate())

        elif field_type == 'combo':
            widget = QComboBox()
            items = field.get('items', [])
            for item in items:
                if isinstance(item, tuple):
                    widget.addItem(item[1], item[0])  # (value, text)
                else:
                    widget.addItem(str(item), item)

            if name in self.existing_data and self.existing_data[name] is not None:
                index = widget.findData(self.existing_data[name])
                if index >= 0:
                    widget.setCurrentIndex(index)

        elif field_type == 'textarea':
            widget = QTextEdit()
            widget.setMaximumHeight(100)
            if name in self.existing_data:
                widget.setPlainText(str(self.existing_data[name] or ''))
        else:
            widget = QLineEdit()

        return widget

    def get_field_value(self, name: str) -> Any:
        """Get value from field widget"""
        widget = self.field_widgets[name]
        field = next(f for f in self.fields if f['name'] == name)

        if field['type'] == 'text':
            return widget.text().strip()
        elif field['type'] in ['number']:
            return widget.value()
        elif field['type'] == 'decimal':
            return widget.value()
        elif field['type'] == 'checkbox':
            return widget.isChecked()
        elif field['type'] == 'date':
            return widget.date().toPyDate()
        elif field['type'] == 'combo':
            return widget.currentData()
        elif field['type'] == 'textarea':
            return widget.toPlainText().strip()
        else:
            return widget.text().strip()

    def validate_field(self, field: Dict, value: Any) -> Optional[str]:
        """Validate field value"""
        if field.get('required', False) and (value is None or value == ''):
            return f"Поле '{field['label']}' обязательно для заполнения"

        if field['type'] == 'text' and field.get('email', False):
            if value and not re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
                return f"Некорректный email в поле '{field['label']}'"

        if field['type'] == 'text' and field.get('phone', False):
            if value and not re.match(r'^[\d\s\-\+\(\)]+$', value):
                return f"Некорректный телефон в поле '{field['label']}'"

        if field['type'] in ['number', 'decimal'] and field.get('min') is not None:
            if value < field['min']:
                return f"Значение поля '{field['label']}' не может быть меньше {field['min']}"

        return None

    def validate_and_accept(self):
        """Validate form and accept if valid"""
        errors = []

        for field in self.fields:
            value = self.get_field_value(field['name'])
            error = self.validate_field(field, value)
            if error:
                errors.append(error)

        if errors:
            QMessageBox.warning(self, "Ошибки валидации", "\n".join(errors))
            return

        self.accept()

    def get_form_data(self) -> Dict[str, Any]:
        """Get all form data"""
        data = {}
        for field in self.fields:
            data[field['name']] = self.get_field_value(field['name'])
        return data

class EditWindow(QWidget):
    """Edit window with CRUD operations"""

    def __init__(self):
        super().__init__()
        self.current_medicines = []
        self.current_suppliers = []
        self.current_customers = []
        self.current_employees = []
        self.current_sales = []
        self.current_prescriptions = []
        self.current_types = []
        self.init_ui()
        self.load_all_data()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Редактирование данных")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Tab widget
        self.tab_widget = QTabWidget()

        # Create tabs
        self.create_medicines_tab()
        self.create_suppliers_tab()
        self.create_customers_tab()
        self.create_employees_tab()
        self.create_sales_tab()
        self.create_prescriptions_tab()
        self.create_types_tab()

        layout.addWidget(self.tab_widget)

    def create_medicines_tab(self):
        """Create medicines tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Buttons
        button_layout = QHBoxLayout()

        add_btn = QPushButton("Добавить лекарство")
        add_btn.clicked.connect(self.add_medicine)
        button_layout.addWidget(add_btn)

        edit_btn = QPushButton("Редактировать")
        edit_btn.clicked.connect(self.edit_medicine)
        button_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(self.delete_medicine)
        button_layout.addWidget(delete_btn)

        button_layout.addStretch()

        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_medicines_data)
        button_layout.addWidget(refresh_btn)

        layout.addLayout(button_layout)

        # Table
        self.medicines_table = QTableWidget()
        self.medicines_table.setColumnCount(6)
        self.medicines_table.setHorizontalHeaderLabels([
            "ID", "Название", "Цена", "Количество", "Рецептурное", "Поставщик"
        ])
        self.medicines_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.medicines_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.medicines_table.setAlternatingRowColors(True)
        self.medicines_table.doubleClicked.connect(self.edit_medicine)

        layout.addWidget(self.medicines_table)

        self.tab_widget.addTab(tab, "Лекарства")

    def create_suppliers_tab(self):
        """Create suppliers tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Buttons
        button_layout = QHBoxLayout()

        add_btn = QPushButton("Добавить поставщика")
        add_btn.clicked.connect(self.add_supplier)
        button_layout.addWidget(add_btn)

        edit_btn = QPushButton("Редактировать")
        edit_btn.clicked.connect(self.edit_supplier)
        button_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(self.delete_supplier)
        button_layout.addWidget(delete_btn)

        button_layout.addStretch()

        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_suppliers_data)
        button_layout.addWidget(refresh_btn)

        layout.addLayout(button_layout)

        # Table
        self.suppliers_table = QTableWidget()
        self.suppliers_table.setColumnCount(4)
        self.suppliers_table.setHorizontalHeaderLabels([
            "ID", "Название", "Адрес", "Телефон"
        ])
        self.suppliers_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.suppliers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.suppliers_table.setAlternatingRowColors(True)
        self.suppliers_table.doubleClicked.connect(self.edit_supplier)

        layout.addWidget(self.suppliers_table)

        self.tab_widget.addTab(tab, "Поставщики")

    def create_customers_tab(self):
        """Create customers tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Buttons
        button_layout = QHBoxLayout()

        add_btn = QPushButton("Добавить клиента")
        add_btn.clicked.connect(self.add_customer)
        button_layout.addWidget(add_btn)

        edit_btn = QPushButton("Редактировать")
        edit_btn.clicked.connect(self.edit_customer)
        button_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(self.delete_customer)
        button_layout.addWidget(delete_btn)

        button_layout.addStretch()

        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_customers_data)
        button_layout.addWidget(refresh_btn)

        layout.addLayout(button_layout)

        # Table
        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(4)
        self.customers_table.setHorizontalHeaderLabels([
            "ID", "Имя", "Адрес", "Телефон"
        ])
        self.customers_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.customers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.customers_table.setAlternatingRowColors(True)
        self.customers_table.doubleClicked.connect(self.edit_customer)

        layout.addWidget(self.customers_table)

        self.tab_widget.addTab(tab, "Клиенты")

    def create_employees_tab(self):
        """Create employees tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Buttons
        button_layout = QHBoxLayout()

        add_btn = QPushButton("Добавить сотрудника")
        add_btn.clicked.connect(self.add_employee)
        button_layout.addWidget(add_btn)

        edit_btn = QPushButton("Редактировать")
        edit_btn.clicked.connect(self.edit_employee)
        button_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(self.delete_employee)
        button_layout.addWidget(delete_btn)

        button_layout.addStretch()

        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_employees_data)
        button_layout.addWidget(refresh_btn)

        layout.addLayout(button_layout)

        # Table
        self.employees_table = QTableWidget()
        self.employees_table.setColumnCount(4)
        self.employees_table.setHorizontalHeaderLabels([
            "ID", "Имя", "Должность", "Зарплата"
        ])
        self.employees_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.employees_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.employees_table.setAlternatingRowColors(True)
        self.employees_table.doubleClicked.connect(self.edit_employee)

        layout.addWidget(self.employees_table)

        self.tab_widget.addTab(tab, "Сотрудники")

    def create_sales_tab(self):
        """Create sales tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Buttons
        button_layout = QHBoxLayout()

        add_btn = QPushButton("Добавить продажу")
        add_btn.clicked.connect(self.add_sale)
        button_layout.addWidget(add_btn)

        edit_btn = QPushButton("Редактировать")
        edit_btn.clicked.connect(self.edit_sale)
        button_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(self.delete_sale)
        button_layout.addWidget(delete_btn)

        button_layout.addStretch()

        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_sales_data)
        button_layout.addWidget(refresh_btn)

        layout.addLayout(button_layout)

        # Table
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(7)
        self.sales_table.setHorizontalHeaderLabels([
            "ID", "Дата", "Лекарство", "Клиент", "Сотрудник", "Количество", "Цена"
        ])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sales_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sales_table.setAlternatingRowColors(True)
        self.sales_table.doubleClicked.connect(self.edit_sale)

        layout.addWidget(self.sales_table)

        self.tab_widget.addTab(tab, "Продажи")

    def create_prescriptions_tab(self):
        """Create prescriptions tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Buttons
        button_layout = QHBoxLayout()

        add_btn = QPushButton("Добавить рецепт")
        add_btn.clicked.connect(self.add_prescription)
        button_layout.addWidget(add_btn)

        edit_btn = QPushButton("Редактировать")
        edit_btn.clicked.connect(self.edit_prescription)
        button_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(self.delete_prescription)
        button_layout.addWidget(delete_btn)

        button_layout.addStretch()

        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_prescriptions_data)
        button_layout.addWidget(refresh_btn)

        layout.addLayout(button_layout)

        # Table
        self.prescriptions_table = QTableWidget()
        self.prescriptions_table.setColumnCount(6)
        self.prescriptions_table.setHorizontalHeaderLabels([
            "ID", "Дата", "Лекарство", "Клиент", "Сотрудник", "Количество"
        ])
        self.prescriptions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.prescriptions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.prescriptions_table.setAlternatingRowColors(True)
        self.prescriptions_table.doubleClicked.connect(self.edit_prescription)

        layout.addWidget(self.prescriptions_table)

        self.tab_widget.addTab(tab, "Рецепты")

    def create_types_tab(self):
        """Create medicine types tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Buttons
        button_layout = QHBoxLayout()

        add_btn = QPushButton("Добавить тип")
        add_btn.clicked.connect(self.add_medicine_type)
        button_layout.addWidget(add_btn)

        edit_btn = QPushButton("Редактировать")
        edit_btn.clicked.connect(self.edit_medicine_type)
        button_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(self.delete_medicine_type)
        button_layout.addWidget(delete_btn)

        button_layout.addStretch()

        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_types_data)
        button_layout.addWidget(refresh_btn)

        layout.addLayout(button_layout)

        # Table
        self.types_table = QTableWidget()
        self.types_table.setColumnCount(2)
        self.types_table.setHorizontalHeaderLabels([
            "ID", "Название"
        ])
        self.types_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.types_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.types_table.setAlternatingRowColors(True)
        self.types_table.doubleClicked.connect(self.edit_medicine_type)

        layout.addWidget(self.types_table)

        self.tab_widget.addTab(tab, "Типы лекарств")

    def load_all_data(self):
        """Load all data"""
        self.load_medicines_data()
        self.load_suppliers_data()
        self.load_customers_data()
        self.load_employees_data()
        self.load_sales_data()
        self.load_prescriptions_data()
        self.load_types_data()

    def load_medicines_data(self):
        """Load medicines data"""
        session = db_manager.get_session()
        if not session:
            return

        try:
            medicines = session.query(Medicine).options(joinedload(Medicine.supplier)).all()
            self.current_medicines = medicines

            self.medicines_table.setRowCount(len(medicines))

            for row, medicine in enumerate(medicines):
                self.medicines_table.setItem(row, 0, QTableWidgetItem(str(medicine.id)))
                self.medicines_table.setItem(row, 1, QTableWidgetItem(medicine.name))
                self.medicines_table.setItem(row, 2, QTableWidgetItem(f"{medicine.price:.2f}"))
                self.medicines_table.setItem(row, 3, QTableWidgetItem(str(medicine.quantity)))
                self.medicines_table.setItem(row, 4, QTableWidgetItem("Да" if medicine.prescription_required else "Нет"))
                supplier_name = medicine.supplier.name if medicine.supplier else "Не указан"
                self.medicines_table.setItem(row, 5, QTableWidgetItem(supplier_name))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки лекарств: {str(e)}")
        finally:
            session.close()

    def load_suppliers_data(self):
        """Load suppliers data"""
        session = db_manager.get_session()
        if not session:
            return

        try:
            suppliers = session.query(Supplier).all()
            self.current_suppliers = suppliers

            self.suppliers_table.setRowCount(len(suppliers))

            for row, supplier in enumerate(suppliers):
                self.suppliers_table.setItem(row, 0, QTableWidgetItem(str(supplier.id)))
                self.suppliers_table.setItem(row, 1, QTableWidgetItem(supplier.name))
                self.suppliers_table.setItem(row, 2, QTableWidgetItem(supplier.address or ""))
                self.suppliers_table.setItem(row, 3, QTableWidgetItem(supplier.phone or ""))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки поставщиков: {str(e)}")
        finally:
            session.close()

    def load_customers_data(self):
        """Load customers data"""
        session = db_manager.get_session()
        if not session:
            return

        try:
            customers = session.query(Customer).all()
            self.current_customers = customers

            self.customers_table.setRowCount(len(customers))

            for row, customer in enumerate(customers):
                self.customers_table.setItem(row, 0, QTableWidgetItem(str(customer.id)))
                self.customers_table.setItem(row, 1, QTableWidgetItem(customer.name))
                self.customers_table.setItem(row, 2, QTableWidgetItem(customer.address or ""))
                self.customers_table.setItem(row, 3, QTableWidgetItem(customer.phone or ""))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки клиентов: {str(e)}")
        finally:
            session.close()

    def load_employees_data(self):
        """Load employees data"""
        session = db_manager.get_session()
        if not session:
            return

        try:
            employees = session.query(Employee).all()
            self.current_employees = employees

            self.employees_table.setRowCount(len(employees))

            for row, employee in enumerate(employees):
                self.employees_table.setItem(row, 0, QTableWidgetItem(str(employee.id)))
                self.employees_table.setItem(row, 1, QTableWidgetItem(employee.name))
                self.employees_table.setItem(row, 2, QTableWidgetItem(employee.position or ""))
                self.employees_table.setItem(row, 3, QTableWidgetItem(f"{employee.salary:.2f}" if employee.salary else "0.00"))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки сотрудников: {str(e)}")
        finally:
            session.close()

    def load_sales_data(self):
        """Load sales data"""
        session = db_manager.get_session()
        if not session:
            return

        try:
            sales = session.query(Sale).options(
                joinedload(Sale.medicine),
                joinedload(Sale.customer),
                joinedload(Sale.employee)
            ).all()
            self.current_sales = sales

            self.sales_table.setRowCount(len(sales))

            for row, sale in enumerate(sales):
                self.sales_table.setItem(row, 0, QTableWidgetItem(str(sale.id)))
                self.sales_table.setItem(row, 1, QTableWidgetItem(sale.date.strftime('%Y-%m-%d')))
                self.sales_table.setItem(row, 2, QTableWidgetItem(sale.medicine.name if sale.medicine else ""))
                self.sales_table.setItem(row, 3, QTableWidgetItem(sale.customer.name if sale.customer else ""))
                self.sales_table.setItem(row, 4, QTableWidgetItem(sale.employee.name if sale.employee else ""))
                self.sales_table.setItem(row, 5, QTableWidgetItem(str(sale.quantity)))
                self.sales_table.setItem(row, 6, QTableWidgetItem(f"{sale.price:.2f}"))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки продаж: {str(e)}")
        finally:
            session.close()

    def load_prescriptions_data(self):
        """Load prescriptions data"""
        session = db_manager.get_session()
        if not session:
            return

        try:
            prescriptions = session.query(Prescription).options(
                joinedload(Prescription.medicine),
                joinedload(Prescription.customer),
                joinedload(Prescription.employee)
            ).all()
            self.current_prescriptions = prescriptions

            self.prescriptions_table.setRowCount(len(prescriptions))

            for row, prescription in enumerate(prescriptions):
                self.prescriptions_table.setItem(row, 0, QTableWidgetItem(str(prescription.id)))
                self.prescriptions_table.setItem(row, 1, QTableWidgetItem(prescription.date.strftime('%Y-%m-%d')))
                self.prescriptions_table.setItem(row, 2, QTableWidgetItem(prescription.medicine.name if prescription.medicine else ""))
                self.prescriptions_table.setItem(row, 3, QTableWidgetItem(prescription.customer.name if prescription.customer else ""))
                self.prescriptions_table.setItem(row, 4, QTableWidgetItem(prescription.employee.name if prescription.employee else ""))
                self.prescriptions_table.setItem(row, 5, QTableWidgetItem(str(prescription.quantity)))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки рецептов: {str(e)}")
        finally:
            session.close()

    def load_types_data(self):
        """Load medicine types data"""
        session = db_manager.get_session()
        if not session:
            return

        try:
            types = session.query(MedicineType).all()
            self.current_types = types

            self.types_table.setRowCount(len(types))

            for row, med_type in enumerate(types):
                self.types_table.setItem(row, 0, QTableWidgetItem(str(med_type.id)))
                self.types_table.setItem(row, 1, QTableWidgetItem(med_type.name))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки типов лекарств: {str(e)}")
        finally:
            session.close()

    def add_medicine(self):
        """Add new medicine"""
        session = db_manager.get_session()
        if not session:
            return

        try:
            # Get suppliers for combo
            suppliers = session.query(Supplier).all()
            supplier_items = [(s.id, s.name) for s in suppliers]
            supplier_items.insert(0, (None, "Не указан"))

            # Get medicine types for multiselect
            types = session.query(MedicineType).all()
            type_items = [(t.id, t.name) for t in types]

            fields = [
                {'name': 'name', 'label': 'Название', 'type': 'text', 'required': True},
                {'name': 'price', 'label': 'Цена', 'type': 'decimal', 'required': True, 'min': 0.0},
                {'name': 'quantity', 'label': 'Количество', 'type': 'number', 'required': True, 'min': 0},
                {'name': 'prescription_required', 'label': 'Рецептурное', 'type': 'checkbox'},
                {'name': 'supplier_id', 'label': 'Поставщик', 'type': 'combo', 'items': supplier_items},
                {'name': 'types', 'label': 'Типы лекарства', 'type': 'multicheck', 'items': type_items}
            ]

            dialog = FormDialog("Добавить лекарство", fields, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_form_data()

                medicine = Medicine(
                    name=data['name'],
                    price=data['price'],
                    quantity=data['quantity'],
                    prescription_required=data['prescription_required'],
                    supplier_id=data['supplier_id'],
                    types=session.query(MedicineType).filter(MedicineType.id.in_(data['types'])).all()
                )

                session.add(medicine)
                session.commit()
                self.load_medicines_data()
                QMessageBox.information(self, "Успех", "Лекарство добавлено")

        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка добавления лекарства: {str(e)}")
        finally:
            session.close()

    def edit_medicine(self):
        """Edit selected medicine"""
        row = self.medicines_table.currentRow()
        if row < 0 or row >= len(self.current_medicines):
            QMessageBox.warning(self, "Предупреждение", "Выберите лекарство для редактирования")
            return

        medicine = self.current_medicines[row]
        session = db_manager.get_session()
        if not session:
            return

        try:
            # Get suppliers for combo
            suppliers = session.query(Supplier).all()
            supplier_items = [(s.id, s.name) for s in suppliers]
            supplier_items.insert(0, (None, "Не указан"))

            fields = [
                {'name': 'name', 'label': 'Название', 'type': 'text', 'required': True},
                {'name': 'price', 'label': 'Цена', 'type': 'decimal', 'required': True, 'min': 0.0},
                {'name': 'quantity', 'label': 'Количество', 'type': 'number', 'required': True, 'min': 0},
                {'name': 'prescription_required', 'label': 'Рецептурное', 'type': 'checkbox'},
                {'name': 'supplier_id', 'label': 'Поставщик', 'type': 'combo', 'items': supplier_items}
            ]

            existing_data = {
                'name': medicine.name,
                'price': medicine.price,
                'quantity': medicine.quantity,
                'prescription_required': medicine.prescription_required,
                'supplier_id': medicine.supplier_id
            }

            dialog = FormDialog("Редактировать лекарство", fields, self, existing_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_form_data()

                # Update medicine
                med_to_update = session.query(Medicine).get(medicine.id)
                med_to_update.name = data['name']
                med_to_update.price = data['price']
                med_to_update.quantity = data['quantity']
                med_to_update.prescription_required = data['prescription_required']
                med_to_update.supplier_id = data['supplier_id']

                session.commit()
                self.load_medicines_data()
                QMessageBox.information(self, "Успех", "Лекарство обновлено")

        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка редактирования лекарства: {str(e)}")
        finally:
            session.close()

    def delete_medicine(self):
        """Delete selected medicine"""
        row = self.medicines_table.currentRow()
        if row < 0 or row >= len(self.current_medicines):
            QMessageBox.warning(self, "Предупреждение", "Выберите лекарство для удаления")
            return

        medicine = self.current_medicines[row]

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы уверены, что хотите удалить лекарство '{medicine.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            session = db_manager.get_session()
            if not session:
                return

            try:
                med_to_delete = session.query(Medicine).get(medicine.id)
                session.delete(med_to_delete)
                session.commit()
                self.load_medicines_data()
                QMessageBox.information(self, "Успех", "Лекарство удалено")

            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Ошибка удаления лекарства: {str(e)}")
            finally:
                session.close()

    # Supplier CRUD operations
    def add_supplier(self):
        """Add new supplier"""
        fields = [
            {'name': 'name', 'label': 'Название', 'type': 'text', 'required': True},
            {'name': 'address', 'label': 'Адрес', 'type': 'text'},
            {'name': 'phone', 'label': 'Телефон', 'type': 'text', 'phone': True}
        ]

        dialog = FormDialog("Добавить поставщика", fields, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_form_data()

            session = db_manager.get_session()
            if not session:
                return

            try:
                supplier = Supplier(
                    name=data['name'],
                    address=data['address'] or None,
                    phone=data['phone'] or None
                )

                session.add(supplier)
                session.commit()
                self.load_suppliers_data()
                QMessageBox.information(self, "Успех", "Поставщик добавлен")

            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Ошибка добавления поставщика: {str(e)}")
            finally:
                session.close()

    def edit_supplier(self):
        """Edit selected supplier"""
        row = self.suppliers_table.currentRow()
        if row < 0 or row >= len(self.current_suppliers):
            QMessageBox.warning(self, "Предупреждение", "Выберите поставщика для редактирования")
            return

        supplier = self.current_suppliers[row]

        fields = [
            {'name': 'name', 'label': 'Название', 'type': 'text', 'required': True},
            {'name': 'address', 'label': 'Адрес', 'type': 'text'},
            {'name': 'phone', 'label': 'Телефон', 'type': 'text', 'phone': True}
        ]

        existing_data = {
            'name': supplier.name,
            'address': supplier.address,
            'phone': supplier.phone
        }

        dialog = FormDialog("Редактировать поставщика", fields, self, existing_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_form_data()

            session = db_manager.get_session()
            if not session:
                return

            try:
                supp_to_update = session.query(Supplier).get(supplier.id)
                supp_to_update.name = data['name']
                supp_to_update.address = data['address'] or None
                supp_to_update.phone = data['phone'] or None

                session.commit()
                self.load_suppliers_data()
                QMessageBox.information(self, "Успех", "Поставщик обновлен")

            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Ошибка редактирования поставщика: {str(e)}")
            finally:
                session.close()

    def delete_supplier(self):
        """Delete selected supplier"""
        row = self.suppliers_table.currentRow()
        if row < 0 or row >= len(self.current_suppliers):
            QMessageBox.warning(self, "Предупреждение", "Выберите поставщика для удаления")
            return

        supplier = self.current_suppliers[row]

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы уверены, что хотите удалить поставщика '{supplier.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            session = db_manager.get_session()
            if not session:
                return

            try:
                supp_to_delete = session.query(Supplier).get(supplier.id)
                session.delete(supp_to_delete)
                session.commit()
                self.load_suppliers_data()
                QMessageBox.information(self, "Успех", "Поставщик удален")

            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Ошибка удаления поставщика: {str(e)}")
            finally:
                session.close()

    # Customer CRUD operations
    def add_customer(self):
        """Add new customer"""
        fields = [
            {'name': 'name', 'label': 'Имя', 'type': 'text', 'required': True},
            {'name': 'address', 'label': 'Адрес', 'type': 'text'},
            {'name': 'phone', 'label': 'Телефон', 'type': 'text', 'phone': True}
        ]

        dialog = FormDialog("Добавить клиента", fields, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_form_data()

            session = db_manager.get_session()
            if not session:
                return

            try:
                customer = Customer(
                    name=data['name'],
                    address=data['address'] or None,
                    phone=data['phone'] or None
                )

                session.add(customer)
                session.commit()
                self.load_customers_data()
                QMessageBox.information(self, "Успех", "Клиент добавлен")

            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Ошибка добавления клиента: {str(e)}")
            finally:
                session.close()

    def edit_customer(self):
        """Edit selected customer"""
        row = self.customers_table.currentRow()
        if row < 0 or row >= len(self.current_customers):
            QMessageBox.warning(self, "Предупреждение", "Выберите клиента для редактирования")
            return

        customer = self.current_customers[row]

        fields = [
            {'name': 'name', 'label': 'Имя', 'type': 'text', 'required': True},
            {'name': 'address', 'label': 'Адрес', 'type': 'text'},
            {'name': 'phone', 'label': 'Телефон', 'type': 'text', 'phone': True}
        ]

        existing_data = {
            'name': customer.name,
            'address': customer.address,
            'phone': customer.phone
        }

        dialog = FormDialog("Редактировать клиента", fields, self, existing_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_form_data()

            session = db_manager.get_session()
            if not session:
                return

            try:
                cust_to_update = session.query(Customer).get(customer.id)
                cust_to_update.name = data['name']
                cust_to_update.address = data['address'] or None
                cust_to_update.phone = data['phone'] or None

                session.commit()
                self.load_customers_data()
                QMessageBox.information(self, "Успех", "Клиент обновлен")

            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Ошибка редактирования клиента: {str(e)}")
            finally:
                session.close()

    def delete_customer(self):
        """Delete selected customer"""
        row = self.customers_table.currentRow()
        if row < 0 or row >= len(self.current_customers):
            QMessageBox.warning(self, "Предупреждение", "Выберите клиента для удаления")
            return

        customer = self.current_customers[row]

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы уверены, что хотите удалить клиента '{customer.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            session = db_manager.get_session()
            if not session:
                return

            try:
                cust_to_delete = session.query(Customer).get(customer.id)
                session.delete(cust_to_delete)
                session.commit()
                self.load_customers_data()
                QMessageBox.information(self, "Успех", "Клиент удален")

            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Ошибка удаления клиента: {str(e)}")
            finally:
                session.close()

    # Employee CRUD operations
    def add_employee(self):
        """Add new employee"""
        fields = [
            {'name': 'name', 'label': 'Имя', 'type': 'text', 'required': True},
            {'name': 'position', 'label': 'Должность', 'type': 'text'},
            {'name': 'salary', 'label': 'Зарплата', 'type': 'decimal', 'min': 0.0}
        ]

        dialog = FormDialog("Добавить сотрудника", fields, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_form_data()

            session = db_manager.get_session()
            if not session:
                return

            try:
                employee = Employee(
                    name=data['name'],
                    position=data['position'] or None,
                    salary=data['salary'] if data['salary'] > 0 else None
                )

                session.add(employee)
                session.commit()
                self.load_employees_data()
                QMessageBox.information(self, "Успех", "Сотрудник добавлен")

            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Ошибка добавления сотрудника: {str(e)}")
            finally:
                session.close()

    def edit_employee(self):
        """Edit selected employee"""
        row = self.employees_table.currentRow()
        if row < 0 or row >= len(self.current_employees):
            QMessageBox.warning(self, "Предупреждение", "Выберите сотрудника для редактирования")
            return

        employee = self.current_employees[row]

        fields = [
            {'name': 'name', 'label': 'Имя', 'type': 'text', 'required': True},
            {'name': 'position', 'label': 'Должность', 'type': 'text'},
            {'name': 'salary', 'label': 'Зарплата', 'type': 'decimal', 'min': 0.0}
        ]

        existing_data = {
            'name': employee.name,
            'position': employee.position,
            'salary': employee.salary or 0.0
        }

        dialog = FormDialog("Редактировать сотрудника", fields, self, existing_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_form_data()

            session = db_manager.get_session()
            if not session:
                return

            try:
                emp_to_update = session.query(Employee).get(employee.id)
                emp_to_update.name = data['name']
                emp_to_update.position = data['position'] or None
                emp_to_update.salary = data['salary'] if data['salary'] > 0 else None

                session.commit()
                self.load_employees_data()
                QMessageBox.information(self, "Успех", "Сотрудник обновлен")

            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Ошибка редактирования сотрудника: {str(e)}")
            finally:
                session.close()

    def delete_employee(self):
        """Delete selected employee"""
        row = self.employees_table.currentRow()
        if row < 0 or row >= len(self.current_employees):
            QMessageBox.warning(self, "Предупреждение", "Выберите сотрудника для удаления")
            return

        employee = self.current_employees[row]

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы уверены, что хотите удалить сотрудника '{employee.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            session = db_manager.get_session()
            if not session:
                return

            try:
                emp_to_delete = session.query(Employee).get(employee.id)
                session.delete(emp_to_delete)
                session.commit()
                self.load_employees_data()
                QMessageBox.information(self, "Успех", "Сотрудник удален")

            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Ошибка удаления сотрудника: {str(e)}")
            finally:
                session.close()

    # Sale CRUD operations
    def add_sale(self):
        """Add new sale"""
        session = db_manager.get_session()
        if not session:
            return

        try:
            # Get options for combos
            medicines = session.query(Medicine).all()
            customers = session.query(Customer).all()
            employees = session.query(Employee).all()

            medicine_items = [(m.id, f"{m.name} - {m.price:.2f}₽") for m in medicines]
            customer_items = [(c.id, c.name) for c in customers]
            employee_items = [(e.id, e.name) for e in employees]

            fields = [
                {'name': 'date', 'label': 'Дата', 'type': 'date', 'required': True},
                {'name': 'medicine_id', 'label': 'Лекарство', 'type': 'combo', 'items': medicine_items, 'required': True},
                {'name': 'customer_id', 'label': 'Клиент', 'type': 'combo', 'items': customer_items, 'required': True},
                {'name': 'employee_id', 'label': 'Сотрудник', 'type': 'combo', 'items': employee_items, 'required': True},
                {'name': 'quantity', 'label': 'Количество', 'type': 'number', 'required': True, 'min': 1},
                {'name': 'price', 'label': 'Цена', 'type': 'decimal', 'required': True, 'min': 0.0}
            ]

            dialog = FormDialog("Добавить продажу", fields, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_form_data()

                sale = Sale(
                    date=data['date'],
                    medicine_id=data['medicine_id'],
                    customer_id=data['customer_id'],
                    employee_id=data['employee_id'],
                    quantity=data['quantity'],
                    price=data['price']
                )

                session.add(sale)
                session.commit()
                self.load_sales_data()
                QMessageBox.information(self, "Успех", "Продажа добавлена")

        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка добавления продажи: {str(e)}")
        finally:
            session.close()

    def edit_sale(self):
        """Edit selected sale"""
        row = self.sales_table.currentRow()
        if row < 0 or row >= len(self.current_sales):
            QMessageBox.warning(self, "Предупреждение", "Выберите продажу для редактирования")
            return

        sale = self.current_sales[row]
        session = db_manager.get_session()
        if not session:
            return

        try:
            # Get options for combos
            medicines = session.query(Medicine).all()
            customers = session.query(Customer).all()
            employees = session.query(Employee).all()

            medicine_items = [(m.id, f"{m.name} - {m.price:.2f}₽") for m in medicines]
            customer_items = [(c.id, c.name) for c in customers]
            employee_items = [(e.id, e.name) for e in employees]

            fields = [
                {'name': 'date', 'label': 'Дата', 'type': 'date', 'required': True},
                {'name': 'medicine_id', 'label': 'Лекарство', 'type': 'combo', 'items': medicine_items, 'required': True},
                {'name': 'customer_id', 'label': 'Клиент', 'type': 'combo', 'items': customer_items, 'required': True},
                {'name': 'employee_id', 'label': 'Сотрудник', 'type': 'combo', 'items': employee_items, 'required': True},
                {'name': 'quantity', 'label': 'Количество', 'type': 'number', 'required': True, 'min': 1},
                {'name': 'price', 'label': 'Цена', 'type': 'decimal', 'required': True, 'min': 0.0}
            ]

            existing_data = {
                'date': sale.date,
                'medicine_id': sale.medicine_id,
                'customer_id': sale.customer_id,
                'employee_id': sale.employee_id,
                'quantity': sale.quantity,
                'price': sale.price
            }

            dialog = FormDialog("Редактировать продажу", fields, self, existing_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_form_data()

                sale_to_update = session.query(Sale).get(sale.id)
                sale_to_update.date = data['date']
                sale_to_update.medicine_id = data['medicine_id']
                sale_to_update.customer_id = data['customer_id']
                sale_to_update.employee_id = data['employee_id']
                sale_to_update.quantity = data['quantity']
                sale_to_update.price = data['price']

                session.commit()
                self.load_sales_data()
                QMessageBox.information(self, "Успех", "Продажа обновлена")

        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка редактирования продажи: {str(e)}")
        finally:
            session.close()

    def delete_sale(self):
        """Delete selected sale"""
        row = self.sales_table.currentRow()
        if row < 0 or row >= len(self.current_sales):
            QMessageBox.warning(self, "Предупреждение", "Выберите продажу для удаления")
            return

        sale = self.current_sales[row]

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы уверены, что хотите удалить продажу №{sale.id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            session = db_manager.get_session()
            if not session:
                return

            try:
                sale_to_delete = session.query(Sale).get(sale.id)
                session.delete(sale_to_delete)
                session.commit()
                self.load_sales_data()
                QMessageBox.information(self, "Успех", "Продажа удалена")

            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Ошибка удаления продажи: {str(e)}")
            finally:
                session.close()

    # Prescription CRUD operations
    def add_prescription(self):
        """Add new prescription"""
        session = db_manager.get_session()
        if not session:
            return

        try:
            # Get options for combos
            medicines = session.query(Medicine).filter(Medicine.prescription_required == True).all()
            customers = session.query(Customer).all()
            employees = session.query(Employee).all()

            medicine_items = [(m.id, m.name) for m in medicines]
            customer_items = [(c.id, c.name) for c in customers]
            employee_items = [(e.id, e.name) for e in employees]

            fields = [
                {'name': 'date', 'label': 'Дата', 'type': 'date', 'required': True},
                {'name': 'medicine_id', 'label': 'Лекарство', 'type': 'combo', 'items': medicine_items, 'required': True},
                {'name': 'customer_id', 'label': 'Клиент', 'type': 'combo', 'items': customer_items, 'required': True},
                {'name': 'employee_id', 'label': 'Сотрудник', 'type': 'combo', 'items': employee_items, 'required': True},
                {'name': 'quantity', 'label': 'Количество', 'type': 'number', 'required': True, 'min': 1}
            ]

            dialog = FormDialog("Добавить рецепт", fields, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_form_data()

                prescription = Prescription(
                    date=data['date'],
                    medicine_id=data['medicine_id'],
                    customer_id=data['customer_id'],
                    employee_id=data['employee_id'],
                    quantity=data['quantity']
                )

                session.add(prescription)
                session.commit()
                self.load_prescriptions_data()
                QMessageBox.information(self, "Успех", "Рецепт добавлен")

        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка добавления рецепта: {str(e)}")
        finally:
            session.close()

    # === PRESCRIPTIONS ===

    def edit_prescription(self):
        selected = self.prescription_table.currentRow()
        if selected < 0:
            return

        prescription_id = int(self.prescription_table.item(selected, 0).text())
        prescription = self.session.query(Prescription).get(prescription_id)

        medicines = self.session.query(Medicine).filter(Medicine.prescription_required == True).all()
        customers = self.session.query(Customer).all()
        employees = self.session.query(Employee).all()

        dialog = FormDialog(
            ("Дата", "Лекарство", "Клиент", "Сотрудник", "Количество"),
            [
                prescription.date,
                prescription.medicine_id,
                prescription.customer_id,
                prescription.employee_id,
                prescription.quantity
            ],
            [
                None,
                [f"{m.id}: {m.name}" for m in medicines],
                [f"{c.id}: {c.name}" for c in customers],
                [f"{e.id}: {e.full_name}" for e in employees],
                None
            ]
        )
        if dialog.exec():
            try:
                date, med_idx, cust_idx, emp_idx, qty = dialog.get_data()
                prescription.date = date
                prescription.medicine_id = medicines[med_idx].id
                prescription.customer_id = customers[cust_idx].id
                prescription.employee_id = employees[emp_idx].id
                prescription.quantity = qty
                self.session.commit()
                self.load_prescriptions_data()
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Ошибка", str(e))

    def delete_prescription(self):
        selected = self.prescription_table.currentRow()
        if selected < 0:
            return

        prescription_id = int(self.prescription_table.item(selected, 0).text())
        try:
            prescription = self.session.query(Prescription).get(prescription_id)
            self.session.delete(prescription)
            self.session.commit()
            self.load_prescriptions_data()
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Ошибка удаления", str(e))

    # === MEDICINE TYPES ===

    def add_medicine_type(self):
        fields = [
            {'name': 'name', 'label': 'Название', 'type': 'text', 'required': True}
        ]

        dialog = FormDialog("Добавить тип лекарства", fields, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_form_data()

            session = db_manager.get_session()
            if not session:
                return

            try:
                new_type = MedicineType(name=data['name'])
                session.add(new_type)
                session.commit()
                self.load_types_data()
                QMessageBox.information(self, "Успех", "Тип лекарства добавлен")
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Ошибка добавления: {str(e)}")
            finally:
                session.close()

    def edit_medicine_type(self):
        row = self.types_table.currentRow()
        if row < 0 or row >= len(self.current_types):
            QMessageBox.warning(self, "Предупреждение", "Выберите тип лекарства для редактирования")
            return

        mtype = self.current_types[row]

        fields = [
            {'name': 'name', 'label': 'Название', 'type': 'text', 'required': True}
        ]

        existing_data = {
            'name': mtype.name
        }

        dialog = FormDialog("Редактировать тип лекарства", fields, self, existing_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_form_data()

            session = db_manager.get_session()
            if not session:
                return

            try:
                mtype_to_update = session.query(MedicineType).get(mtype.id)
                mtype_to_update.name = data['name']

                session.commit()
                self.load_types_data()
                QMessageBox.information(self, "Успех", "Тип лекарства обновлён")
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Ошибка редактирования: {str(e)}")
            finally:
                session.close()

    def delete_medicine_type(self):
        row = self.types_table.currentRow()
        if row < 0 or row >= len(self.current_types):
            QMessageBox.warning(self, "Предупреждение", "Выберите тип лекарства для удаления")
            return

        mtype = self.current_types[row]

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить тип лекарства '{mtype.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            session = db_manager.get_session()
            if not session:
                return

            try:
                mtype_to_delete = session.query(MedicineType).get(mtype.id)
                session.delete(mtype_to_delete)
                session.commit()
                self.load_types_data()
                QMessageBox.information(self, "Успех", "Тип лекарства удалён")
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Ошибка удаления: {str(e)}")
            finally:
                session.close()
