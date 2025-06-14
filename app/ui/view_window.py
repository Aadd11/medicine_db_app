"""
Окно просмотра
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QTableWidget, QTableWidgetItem, QHeaderView,
                            QLineEdit, QComboBox, QPushButton, QLabel,
                            QCheckBox, QSpinBox, QDoubleSpinBox, QDateEdit,
                            QGroupBox, QScrollArea, QFrame, QMessageBox,
                            QDialog, QDialogButtonBox, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QFont
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, or_, func

from app.database_manager import db_manager
from app.models import (Medicine, MedicineType, Supplier, Customer, Employee, 
                       Sale, Prescription, ActionLog, User)

#Table items default logic overrides: read only and numbers inseat of strings
class ReadOnlyTableWidgetItem(QTableWidgetItem):
    def __init__(self, text):
        super().__init__(str(text))
        self.setFlags(self.flags() & ~Qt.ItemFlag.ItemIsEditable)
"""Numeric data handling for column sorting"""
class NumericTableWidgetItem(ReadOnlyTableWidgetItem):
    def __init__(self, value):
        super().__init__(f"{float(value):.2f}")
        self.numeric_value = float(str(value).replace(',', '.'))

    def __lt__(self, other):
        if isinstance(other, NumericTableWidgetItem):
            return self.numeric_value < other.numeric_value
        return super().__lt__(other)
def make_item(value):
    try:
        return NumericTableWidgetItem(value)
    except:
        return ReadOnlyTableWidgetItem(value)




class FilterDialog(QDialog):
    """Dialog for advanced column filtering"""
    def __init__(self, column_name, unique_values, parent=None):
        super().__init__(parent)
        self.column_name = column_name
        self.unique_values = unique_values
        self.selected_values = set(unique_values)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"Фильтр: {self.column_name}")
        self.setModal(True)
        self.resize(300, 400)

        layout = QVBoxLayout(self)
        # Search box
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self.filter_list)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # Select all / none buttons
        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("Выбрать все")
        select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(select_all_btn)
        select_none_btn = QPushButton("Снять все")
        select_none_btn.clicked.connect(self.select_none)
        button_layout.addWidget(select_none_btn)
        layout.addLayout(button_layout)

        # Values list
        self.values_list = QListWidget()
        self.populate_list()
        layout.addWidget(self.values_list)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def populate_list(self):
        """Populate list of values"""
        self.values_list.clear()
        for value in sorted(self.unique_values):
            item = QListWidgetItem(str(value))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if value in self.selected_values else Qt.CheckState.Unchecked)
            self.values_list.addItem(item)

    def filter_list(self):
        """Filter list by search"""
        search_text = self.search_edit.text().lower()
        for i in range(self.values_list.count()):
            item = self.values_list.item(i)
            item.setHidden(search_text not in item.text().lower())

    def select_all(self):
        for i in range(self.values_list.count()):
            item = self.values_list.item(i)
            if not item.isHidden():
                item.setCheckState(Qt.CheckState.Checked)

    def select_none(self):
        for i in range(self.values_list.count()):
            item = self.values_list.item(i)
            if not item.isHidden():
                item.setCheckState(Qt.CheckState.Unchecked)

    def get_selected_values(self):
        selected = set()
        for i in range(self.values_list.count()):
            item = self.values_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.add(item.text())
        return selected

class ViewWindow(QWidget):
    """Main viewing window with advanced filtering"""
    
    def __init__(self):
        super().__init__()
        self.current_filters = {}
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)

        # Search and filter controls
        self.create_search_controls(layout)

        # Main content tabs
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs
        self.create_medicines_tab()
        self.create_suppliers_tab()
        self.create_customers_tab()
        self.create_employees_tab()
        self.create_sales_tab()
        self.create_prescriptions_tab()
        self.create_logs_tab()

    
    def create_search_controls(self, layout):
        """Create search and filter controls"""
        search_group = QGroupBox("Поиск и фильтры")
        search_layout = QVBoxLayout(search_group)
        
        # Global search
        global_search_layout = QHBoxLayout()
        global_search_layout.addWidget(QLabel("Глобальный поиск:"))
        self.global_search = QLineEdit()
        self.global_search.setPlaceholderText("Например: Парацетамол или обезболивающее")
        self.global_search.returnPressed.connect(self.apply_global_search)
        global_search_layout.addWidget(self.global_search)
        
        search_btn = QPushButton("Найти")
        search_btn.clicked.connect(self.apply_global_search)
        global_search_layout.addWidget(search_btn)
        
        clear_btn = QPushButton("Очистить")
        clear_btn.clicked.connect(self.clear_filters)
        global_search_layout.addWidget(clear_btn)
        
        search_layout.addLayout(global_search_layout)
        
        # Quick filters
        quick_filters_layout = QHBoxLayout()
        
        # Price range
        price_group = QGroupBox("Цена")
        price_layout = QHBoxLayout(price_group)
        price_layout.addWidget(QLabel("от"))
        self.price_from = QDoubleSpinBox()
        self.price_from.setMaximum(999999.99)
        self.price_from.valueChanged.connect(self.apply_filters)
        price_layout.addWidget(self.price_from)
        
        price_layout.addWidget(QLabel("до"))
        self.price_to = QDoubleSpinBox()
        self.price_to.setMaximum(999999.99)
        self.price_to.setValue(999999.99)
        self.price_to.valueChanged.connect(self.apply_filters)
        price_layout.addWidget(self.price_to)
        quick_filters_layout.addWidget(price_group)
        
        # Quantity range
        qty_group = QGroupBox("Количество")
        qty_layout = QHBoxLayout(qty_group)
        qty_layout.addWidget(QLabel("от"))
        self.qty_from = QSpinBox()
        self.qty_from.setMaximum(999999)
        self.qty_from.valueChanged.connect(self.apply_filters)
        qty_layout.addWidget(self.qty_from)
        
        qty_layout.addWidget(QLabel("до"))
        self.qty_to = QSpinBox()
        self.qty_to.setMaximum(999999)
        self.qty_to.setValue(999999)
        self.qty_to.valueChanged.connect(self.apply_filters)
        qty_layout.addWidget(self.qty_to)
        quick_filters_layout.addWidget(qty_group)
        
        # Prescription required
        self.prescription_filter = QCheckBox("Только рецептурные")
        self.prescription_filter.stateChanged.connect(self.apply_filters)
        quick_filters_layout.addWidget(self.prescription_filter)
        
        quick_filters_layout.addStretch()
        search_layout.addLayout(quick_filters_layout)
        
        layout.addWidget(search_group)
    
    def create_medicines_tab(self):
        """Create medicines tab"""
        medicines_widget = QWidget()
        layout = QVBoxLayout(medicines_widget)
        
        # Table
        self.medicines_table = QTableWidget()
        self.medicines_table.setAlternatingRowColors(True)
        self.medicines_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.medicines_table.setSortingEnabled(True)
        
        # Setup columns
        columns = ["ID", "Название", "Цена", "Количество", "Рецептурный", "Поставщик", "Типы"]
        self.medicines_table.setColumnCount(len(columns))
        self.medicines_table.setHorizontalHeaderLabels(columns)
        
        # Enable column filtering
        header = self.medicines_table.horizontalHeader()
        header.sectionClicked.connect(lambda col: self.show_column_filter(self.medicines_table, col))
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        # Auto-resize columns
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Name column
        
        layout.addWidget(self.medicines_table)
        self.tab_widget.addTab(medicines_widget, "Лекарства")
    
    def create_suppliers_tab(self):
        """Create suppliers tab"""
        suppliers_widget = QWidget()
        layout = QVBoxLayout(suppliers_widget)
        
        self.suppliers_table = QTableWidget()
        self.suppliers_table.setAlternatingRowColors(True)
        self.suppliers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.suppliers_table.setSortingEnabled(True)
        
        columns = ["ID", "Название", "Адрес", "Телефон", "Количество препаратов"]
        self.suppliers_table.setColumnCount(len(columns))
        self.suppliers_table.setHorizontalHeaderLabels(columns)
        
        header = self.suppliers_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.suppliers_table)
        self.tab_widget.addTab(suppliers_widget, "Поставщики")
    
    def create_customers_tab(self):
        """Create customers tab"""
        customers_widget = QWidget()
        layout = QVBoxLayout(customers_widget)
        
        self.customers_table = QTableWidget()
        self.customers_table.setAlternatingRowColors(True)
        self.customers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.customers_table.setSortingEnabled(True)
        
        columns = ["ID", "Имя", "Адрес", "Телефон", "Количество покупок", "Количество рецептов"]
        self.customers_table.setColumnCount(len(columns))
        self.customers_table.setHorizontalHeaderLabels(columns)
        
        header = self.customers_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.customers_table)
        self.tab_widget.addTab(customers_widget, "Клиенты")
    
    def create_employees_tab(self):
        """Create employees tab"""
        employees_widget = QWidget()
        layout = QVBoxLayout(employees_widget)
        
        self.employees_table = QTableWidget()
        self.employees_table.setAlternatingRowColors(True)
        self.employees_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.employees_table.setSortingEnabled(True)
        
        columns = ["ID", "Имя", "Должность", "Зарплата", "Пользователь", "Продаж", "Рецептов"]
        self.employees_table.setColumnCount(len(columns))
        self.employees_table.setHorizontalHeaderLabels(columns)
        
        header = self.employees_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.employees_table)
        self.tab_widget.addTab(employees_widget, "Сотрудники")
    
    def create_sales_tab(self):
        """Create sales tab"""
        sales_widget = QWidget()
        layout = QVBoxLayout(sales_widget)
        
        self.sales_table = QTableWidget()
        self.sales_table.setAlternatingRowColors(True)
        self.sales_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sales_table.setSortingEnabled(True)
        
        columns = ["ID", "Дата", "Клиент", "Лекарство", "Сотрудник", "Количество", "Цена", "Сумма"]
        self.sales_table.setColumnCount(len(columns))
        self.sales_table.setHorizontalHeaderLabels(columns)
        
        header = self.sales_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.sales_table)
        self.tab_widget.addTab(sales_widget, "Продажи")
    
    def create_prescriptions_tab(self):
        """Create prescriptions tab"""
        prescriptions_widget = QWidget()
        layout = QVBoxLayout(prescriptions_widget)
        
        self.prescriptions_table = QTableWidget()
        self.prescriptions_table.setAlternatingRowColors(True)
        self.prescriptions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.prescriptions_table.setSortingEnabled(True)
        
        columns = ["ID", "Дата", "Клиент", "Лекарство", "Сотрудник", "Количество"]
        self.prescriptions_table.setColumnCount(len(columns))
        self.prescriptions_table.setHorizontalHeaderLabels(columns)
        
        header = self.prescriptions_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.prescriptions_table)
        self.tab_widget.addTab(prescriptions_widget, "Рецепты")
    
    def create_logs_tab(self):
        """Create action logs tab"""
        logs_widget = QWidget()
        layout = QVBoxLayout(logs_widget)
        
        self.logs_table = QTableWidget()
        self.logs_table.setAlternatingRowColors(True)
        self.logs_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.logs_table.setSortingEnabled(True)
        
        columns = ["ID", "Пользователь", "Действие", "Таблица", "Запись ID", "Время", "Детали"]
        self.logs_table.setColumnCount(len(columns))
        self.logs_table.setHorizontalHeaderLabels(columns)
        
        header = self.logs_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)  # Details column
        
        layout.addWidget(self.logs_table)
        self.tab_widget.addTab(logs_widget, "Журнал действий")
    
    def show_column_filter(self, table, column):
        """Show column filter dialog"""
        if not hasattr(self, 'current_data'):
            return
        
        # Get unique values for the column
        unique_values = set()
        for row in range(table.rowCount()):
            item = table.item(row, column)
            if item:
                unique_values.add(item.text())
        
        if not unique_values:
            return
        
        # Show filter dialog
        column_name = table.horizontalHeaderItem(column).text()
        dialog = FilterDialog(column_name, unique_values, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_values = dialog.get_selected_values()
            self.apply_column_filter(table, column, selected_values)

    def apply_column_filter(self, table, column, selected_values):
        """Apply column filter to table with numeric support"""
        is_numeric = all(self.is_number(v) for v in selected_values)

        for row in range(table.rowCount()):
            item = table.item(row, column)
            if not item:
                table.setRowHidden(row, True)
                continue

            cell_value = item.text()

            if is_numeric:
                try:
                    num_val = float(cell_value.replace(',', '.'))
                    should_show = str(num_val) in {str(float(v)) for v in selected_values}
                except ValueError:
                    should_show = False
            else:
                should_show = cell_value in selected_values

            table.setRowHidden(row, not should_show)

    def is_number(self, value):
        try:
            float(value.replace(',', '.'))
            return True
        except ValueError:
            return False

    def apply_global_search(self):
        """Apply global search across all relevant fields"""
        search_text = self.global_search.text().lower()
        if not search_text:
            self.clear_filters()
            return
        
        # Parse search query for smart search
        # Handle patterns like "препараты от горла дешевле 500 рублей"
        price_keywords = ["дешевле", "дороже", "цена", "стоимость"]
        prescription_keywords = ["рецептурные", "без рецепта", "рецепт"]
        
        # Apply search to current table
        current_table = self.get_current_table()
        if current_table:
            self.filter_table_by_search(current_table, search_text)
    
    def get_current_table(self):
        """Get currently active table"""
        current_index = self.tab_widget.currentIndex()
        tables = [
            self.medicines_table,
            self.suppliers_table,
            self.customers_table,
            self.employees_table,
            self.sales_table,
            self.prescriptions_table,
            self.logs_table
        ]
        return tables[current_index] if current_index < len(tables) else None
    
    def filter_table_by_search(self, table, search_text):
        """Filter table rows based on search text"""
        for row in range(table.rowCount()):
            row_text = ""
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item:
                    row_text += item.text().lower() + " "
            
            should_show = search_text in row_text
            table.setRowHidden(row, not should_show)
    
    def apply_filters(self):
        """Apply all active filters"""
        self.load_medicines_data()  # Reload with filters
    
    def clear_filters(self):
        """Clear all filters"""
        self.global_search.clear()
        self.price_from.setValue(0)
        self.price_to.setValue(999999.99)
        self.qty_from.setValue(0)
        self.qty_to.setValue(999999)
        self.prescription_filter.setChecked(False)
        self.current_filters.clear()
        self.load_data()
        #clears hidden elements after global search
        current_table = self.get_current_table()
        if current_table:
            for row in range(current_table.rowCount()):
                current_table.setRowHidden(row, False)
    
    def load_data(self):
        """Load all data into tables"""
        self.load_medicines_data()
        self.load_suppliers_data()
        self.load_customers_data()
        self.load_employees_data()
        self.load_sales_data()
        self.load_prescriptions_data()
        self.load_logs_data()

    def load_medicines_data(self):
        """Load medicines data with filters"""
        try:
            session = db_manager.get_session()

            # Build query with filters
            query = session.query(Medicine).options(
                joinedload(Medicine.supplier),
                joinedload(Medicine.types)
            )

            # Apply price filter
            if self.price_from.value() > 0 or self.price_to.value() < 999999.99:
                query = query.filter(
                    and_(
                        Medicine.price >= self.price_from.value(),
                        Medicine.price <= self.price_to.value()
                    )
                )

            # Apply quantity filter
            if self.qty_from.value() > 0 or self.qty_to.value() < 999999:
                query = query.filter(
                    and_(
                        Medicine.quantity >= self.qty_from.value(),
                        Medicine.quantity <= self.qty_to.value()
                    )
                )

            # Apply prescription filter
            if self.prescription_filter.isChecked():
                query = query.filter(Medicine.prescription_required == True)

            medicines = query.all()

            # Populate table
            self.medicines_table.setRowCount(len(medicines))
            for row, medicine in enumerate(medicines):
                self.medicines_table.setItem(row, 0, NumericTableWidgetItem(str(medicine.id)))
                self.medicines_table.setItem(row, 1, make_item(medicine.name))
                self.medicines_table.setItem(row, 2, NumericTableWidgetItem(f"{medicine.price:.2f}"))
                self.medicines_table.setItem(row, 3, NumericTableWidgetItem(str(medicine.quantity)))
                self.medicines_table.setItem(row, 4, make_item("Да" if medicine.prescription_required else "Нет"))
                self.medicines_table.setItem(row, 5, make_item(medicine.supplier.name if medicine.supplier else ""))

                # Medicine types
                types_text = ", ".join([t.name for t in medicine.types])
                self.medicines_table.setItem(row, 6, QTableWidgetItem(types_text))

            session.close()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных о лекарствах: {str(e)}")

    def load_suppliers_data(self):
        """Load suppliers data"""
        try:
            session = db_manager.get_session()

            # Get suppliers with medicine count
            suppliers = session.query(Supplier).options(joinedload(Supplier.medicines)).all()

            self.suppliers_table.setRowCount(len(suppliers))
            for row, supplier in enumerate(suppliers):
                self.suppliers_table.setItem(row, 0, NumericTableWidgetItem(str(supplier.id)))
                self.suppliers_table.setItem(row, 1, make_item(supplier.name))
                self.suppliers_table.setItem(row, 2, make_item(supplier.address or ""))
                self.suppliers_table.setItem(row, 3, make_item(supplier.phone or ""))
                self.suppliers_table.setItem(row, 4, NumericTableWidgetItem(str(len(supplier.medicines))))

            session.close()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных о поставщиках: {str(e)}")

    def load_customers_data(self):
        """Load customers data"""
        try:
            session = db_manager.get_session()

            customers = session.query(Customer).options(
                joinedload(Customer.sales),
                joinedload(Customer.prescriptions)
            ).all()

            self.customers_table.setRowCount(len(customers))
            for row, customer in enumerate(customers):
                self.customers_table.setItem(row, 0, NumericTableWidgetItem(str(customer.id)))
                self.customers_table.setItem(row, 1, make_item(customer.name))
                self.customers_table.setItem(row, 2, make_item(customer.address or ""))
                self.customers_table.setItem(row, 3, make_item(customer.phone or ""))
                self.customers_table.setItem(row, 4, NumericTableWidgetItem(str(len(customer.sales))))
                self.customers_table.setItem(row, 5, NumericTableWidgetItem(str(len(customer.prescriptions))))

            session.close()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных о клиентах: {str(e)}")

    def load_employees_data(self):
        """Load employees data"""
        try:
            session = db_manager.get_session()

            employees = session.query(Employee).options(
                joinedload(Employee.user),
                joinedload(Employee.sales),
                joinedload(Employee.prescriptions)
            ).all()

            self.employees_table.setRowCount(len(employees))
            for row, employee in enumerate(employees):
                self.employees_table.setItem(row, 0, NumericTableWidgetItem(str(employee.id)))
                self.employees_table.setItem(row, 1, make_item(employee.name))
                self.employees_table.setItem(row, 2, make_item(employee.position or ""))
                self.employees_table.setItem(row, 3, make_item(f"{employee.salary:.2f}" if employee.salary else ""))
                self.employees_table.setItem(row, 4, make_item(employee.user.username if employee.user else ""))
                self.employees_table.setItem(row, 5, NumericTableWidgetItem(str(len(employee.sales))))
                self.employees_table.setItem(row, 6, NumericTableWidgetItem(str(len(employee.prescriptions))))

            session.close()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных о сотрудниках: {str(e)}")

    def load_sales_data(self):
        """Load sales data"""
        try:
            session = db_manager.get_session()

            sales = session.query(Sale).options(
                joinedload(Sale.customer),
                joinedload(Sale.medicine),
                joinedload(Sale.employee)
            ).order_by(Sale.date.desc()).limit(1000).all()  # Limit for performance

            self.sales_table.setRowCount(len(sales))
            for row, sale in enumerate(sales):
                self.sales_table.setItem(row, 0, NumericTableWidgetItem(str(sale.id)))
                self.sales_table.setItem(row, 1, make_item(sale.date.strftime("%d.%m.%Y")))
                self.sales_table.setItem(row, 2, make_item(sale.customer.name if sale.customer else ""))
                self.sales_table.setItem(row, 3, make_item(sale.medicine.name if sale.medicine else ""))
                self.sales_table.setItem(row, 4, make_item(sale.employee.name if sale.employee else ""))
                self.sales_table.setItem(row, 5, NumericTableWidgetItem(str(sale.quantity)))
                self.sales_table.setItem(row, 6, NumericTableWidgetItem(f"{sale.price:.2f}"))
                self.sales_table.setItem(row, 7, NumericTableWidgetItem(f"{sale.price * sale.quantity:.2f}"))

            session.close()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных о продажах: {str(e)}")

    def load_prescriptions_data(self):
        """Load prescriptions data"""
        try:
            session = db_manager.get_session()

            prescriptions = session.query(Prescription).options(
                joinedload(Prescription.customer),
                joinedload(Prescription.medicine),
                joinedload(Prescription.employee)
            ).order_by(Prescription.date.desc()).limit(1000).all()

            self.prescriptions_table.setRowCount(len(prescriptions))
            for row, prescription in enumerate(prescriptions):
                self.prescriptions_table.setItem(row, 0, NumericTableWidgetItem(str(prescription.id)))
                self.prescriptions_table.setItem(row, 1, make_item(prescription.date.strftime("%d.%m.%Y")))
                self.prescriptions_table.setItem(row, 2, make_item(prescription.customer.name if prescription.customer else ""))
                self.prescriptions_table.setItem(row, 3, make_item(prescription.medicine.name if prescription.medicine else ""))
                self.prescriptions_table.setItem(row, 4, make_item(prescription.employee.name if prescription.employee else ""))
                self.prescriptions_table.setItem(row, 5, NumericTableWidgetItem(str(prescription.quantity)))

            session.close()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных о рецептах: {str(e)}")

    def load_logs_data(self):
        """Load action logs data"""
        try:
            session = db_manager.get_session()

            logs = session.query(ActionLog).options(
                joinedload(ActionLog.user).joinedload(User.employee)
            ).order_by(ActionLog.timestamp.desc()).limit(500).all()

            self.logs_table.setRowCount(len(logs))
            for row, log in enumerate(logs):
                self.logs_table.setItem(row, 0, NumericTableWidgetItem(str(log.id)))

                # User info
                user_info = ""
                if log.user:
                    if log.user.employee:
                        user_info = f"{log.user.employee.name} ({log.user.username})"
                    else:
                        user_info = log.user.username
                self.logs_table.setItem(row, 1, make_item(user_info))

                self.logs_table.setItem(row, 2, make_item(log.action or ""))
                self.logs_table.setItem(row, 3, make_item(log.table_name or ""))
                self.logs_table.setItem(row, 4, make_item(str(log.record_id) if log.record_id else ""))
                self.logs_table.setItem(row, 5, make_item(log.timestamp.strftime("%d.%m.%Y %H:%M:%S")))
                self.logs_table.setItem(row, 6, make_item(log.details or ""))

            session.close()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки журнала действий: {str(e)}")

    def refresh_current_tab(self):
        """Refresh data for current tab"""
        current_index = self.tab_widget.currentIndex()

        refresh_methods = [
            self.load_medicines_data,
            self.load_suppliers_data,
            self.load_customers_data,
            self.load_employees_data,
            self.load_sales_data,
            self.load_prescriptions_data,
            self.load_logs_data
        ]

        if current_index < len(refresh_methods):
            refresh_methods[current_index]()

    def export_current_table(self):
        """Export current table data to CSV"""
        current_table = self.get_current_table()
        if not current_table:
            return

        try:
            from PyQt6.QtWidgets import QFileDialog
            import csv

            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Экспорт данных",
                "",
                "CSV files (*.csv)"
            )

            if filename:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)

                    # Write headers
                    headers = []
                    for col in range(current_table.columnCount()):
                        headers.append(current_table.horizontalHeaderItem(col).text())
                    writer.writerow(headers)

                    # Write data
                    for row in range(current_table.rowCount()):
                        if not current_table.isRowHidden(row):  # Only export visible rows
                            row_data = []
                            for col in range(current_table.columnCount()):
                                item = current_table.item(row, col)
                                row_data.append(item.text() if item else "")
                            writer.writerow(row_data)

                QMessageBox.information(self, "Успех", f"Данные экспортированы в {filename}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта: {str(e)}")

    def show_row_details(self, table, row):
        """Show detailed information for selected row"""
        if row < 0 or row >= table.rowCount():
            return

        # Get row data
        row_data = {}
        for col in range(table.columnCount()):
            header = table.horizontalHeaderItem(col).text()
            item = table.item(row, col)
            row_data[header] = item.text() if item else ""

        # Create detail dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Детали записи")
        dialog.setModal(True)
        dialog.resize(400, 300)

        layout = QVBoxLayout(dialog)

        # Create scroll area for details
        scroll = QScrollArea()
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)

        for key, value in row_data.items():
            row_layout = QHBoxLayout()

            label = QLabel(f"{key}:")
            label.setFont(QFont("", 9, QFont.Weight.Bold))
            label.setMinimumWidth(100)
            row_layout.addWidget(label)

            value_label = QLabel(value)
            value_label.setWordWrap(True)
            row_layout.addWidget(value_label)

            detail_layout.addLayout(row_layout)

        detail_layout.addStretch()
        scroll.setWidget(detail_widget)
        layout.addWidget(scroll)

        # Close button
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def setup_table_context_menus(self):
        """Setup context menus for all tables"""
        tables = [
            self.medicines_table,
            self.suppliers_table,
            self.customers_table,
            self.employees_table,
            self.sales_table,
            self.prescriptions_table,
            self.logs_table
        ]

        for table in tables:
            table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            table.customContextMenuRequested.connect(
                lambda pos, t=table: self.show_table_context_menu(t, pos)
            )
            table.doubleClicked.connect(
                lambda index, t=table: self.show_row_details(t, index.row())
            )

    def show_table_context_menu(self, table, position):
        """Show context menu for table"""
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction

        menu = QMenu(self)

        # Show details action
        if table.itemAt(position):
            details_action = QAction("Показать детали", self)
            details_action.triggered.connect(
                lambda: self.show_row_details(table, table.rowAt(position.y()))
            )
            menu.addAction(details_action)
            menu.addSeparator()

        # Export action
        export_action = QAction("Экспорт в CSV", self)
        export_action.triggered.connect(self.export_current_table)
        menu.addAction(export_action)

        # Refresh action
        refresh_action = QAction("Обновить", self)
        refresh_action.triggered.connect(self.refresh_current_tab)
        menu.addAction(refresh_action)

        menu.addSeparator()

        # Clear filters action
        clear_filters_action = QAction("Очистить фильтры", self)
        clear_filters_action.triggered.connect(self.clear_filters)
        menu.addAction(clear_filters_action)

        menu.exec(table.mapToGlobal(position))

    def setup_auto_refresh(self):
        """Setup auto-refresh timer"""
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.refresh_current_tab)
        # Auto-refresh every 30 seconds (can be made configurable)
        self.auto_refresh_timer.start(30000)

    def closeEvent(self, event):
        """Handle window close event"""
        if hasattr(self, 'auto_refresh_timer'):
            self.auto_refresh_timer.stop()
        event.accept()

    def showEvent(self, event):
        """Handle window show event"""
        super().showEvent(event)
        # Setup context menus after window is shown
        self.setup_table_context_menus()
        # Setup auto-refresh
        self.setup_auto_refresh()