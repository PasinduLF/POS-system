from PyQt5 import QtWidgets, QtCore, QtGui


class ReportsWidget(QtWidgets.QWidget):
	def __init__(self, db, parent=None):
		super().__init__(parent)
		self.db = db
		main_layout = QtWidgets.QHBoxLayout(self)

		# Left panel: categorized buttons
		left_panel = QtWidgets.QVBoxLayout()

		# Sales Reports Group
		sales_group = QtWidgets.QGroupBox('📊 Sales Reports')
		sales_layout = QtWidgets.QGridLayout()
		self.btn_daily = QtWidgets.QPushButton('Daily Sales')
		self.btn_monthly = QtWidgets.QPushButton('Monthly Sales')
		self.btn_yearly = QtWidgets.QPushButton('Yearly Sales')
		self.btn_category = QtWidgets.QPushButton('Category-wise')
		self.btn_top = QtWidgets.QPushButton('Top Products')
		sales_layout.addWidget(self.btn_daily, 0, 0)
		sales_layout.addWidget(self.btn_monthly, 0, 1)
		sales_layout.addWidget(self.btn_yearly, 0, 2)
		sales_layout.addWidget(self.btn_category, 1, 0)
		sales_layout.addWidget(self.btn_top, 1, 1)
		sales_group.setLayout(sales_layout)
		left_panel.addWidget(sales_group)

		# Financial Reports Group
		financial_group = QtWidgets.QGroupBox('💰 Financial Reports')
		financial_layout = QtWidgets.QGridLayout()
		self.btn_profit_d = QtWidgets.QPushButton('Profit (Daily)')
		self.btn_profit_m = QtWidgets.QPushButton('Profit (Monthly)')
		self.btn_profit_y = QtWidgets.QPushButton('Profit (Yearly)')
		self.btn_expenses = QtWidgets.QPushButton('Expenses Summary')
		self.btn_income = QtWidgets.QPushButton('Income Summary')
		financial_layout.addWidget(self.btn_profit_d, 0, 0)
		financial_layout.addWidget(self.btn_profit_m, 0, 1)
		financial_layout.addWidget(self.btn_profit_y, 0, 2)
		financial_layout.addWidget(self.btn_expenses, 1, 0)
		financial_layout.addWidget(self.btn_income, 1, 1)
		financial_group.setLayout(financial_layout)
		left_panel.addWidget(financial_group)

		# Inventory Reports Group
		inventory_group = QtWidgets.QGroupBox('📦 Inventory Reports')
		inventory_layout = QtWidgets.QVBoxLayout()
		self.btn_inventory = QtWidgets.QPushButton('Current Inventory')
		inventory_layout.addWidget(self.btn_inventory)
		inventory_group.setLayout(inventory_layout)
		left_panel.addWidget(inventory_group)

		left_panel.addStretch()

		# Right panel: results display
		right_panel = QtWidgets.QVBoxLayout()
		results_label = QtWidgets.QLabel('Report Results:')
		results_label.setStyleSheet('font-weight: bold; font-size: 12pt; margin-bottom: 5px;')
		right_panel.addWidget(results_label)
		self.text = QtWidgets.QPlainTextEdit()
		self.text.setReadOnly(True)
		self.text.setFont(QtGui.QFont('Consolas', 10))
		right_panel.addWidget(self.text)

		main_layout.addLayout(left_panel, 1)
		main_layout.addLayout(right_panel, 2)

		self.btn_daily.clicked.connect(lambda: self.show_sales('daily'))
		self.btn_monthly.clicked.connect(lambda: self.show_sales('monthly'))
		self.btn_yearly.clicked.connect(lambda: self.show_sales('yearly'))
		self.btn_top.clicked.connect(self.show_top)
		self.btn_inventory.clicked.connect(self.show_inventory)
		self.btn_expenses.clicked.connect(self.show_expenses)
		self.btn_income.clicked.connect(self.show_income)
		self.btn_category.clicked.connect(self.show_category)
		self.btn_profit_d.clicked.connect(lambda: self.show_profit('daily'))
		self.btn_profit_m.clicked.connect(lambda: self.show_profit('monthly'))
		self.btn_profit_y.clicked.connect(lambda: self.show_profit('yearly'))

	def show_sales(self, period: str):
		rows = self.db.sales_summary(period)
		lines = [f"{r['period']}: {r['total']:.2f}" for r in rows]
		self.text.setPlainText('\n'.join(lines) or 'No data')

	def show_top(self):
		rows = self.db.top_products()
		lines = [f"{r['name']}: {r['qty']} units, Rs. {r['revenue']:.2f}" for r in rows]
		self.text.setPlainText('\n'.join(lines) or 'No data')

	def show_inventory(self):
		rows = self.db.inventory_report()
		lines = [f"{r['name']} ({r.get('brand') or ''}): {r['stock_quantity']} pcs (Cost {r['cost_price']:.2f}, Price {r['price']:.2f})" for r in rows]
		self.text.setPlainText('\n'.join(lines) or 'No data')

	def show_expenses(self):
		rows = self.db.monthly_expense_summary()
		lines = [f"{r['month']}: Rs. {r['total']:.2f}" for r in rows]
		self.text.setPlainText('\n'.join(lines) or 'No data')

	def show_income(self):
		rows = self.db.monthly_income_summary()
		lines = [f"{r['month']}: Rs. {r['total']:.2f}" for r in rows]
		self.text.setPlainText('\n'.join(lines) or 'No data')

	def show_category(self):
		rows = self.db.category_sales_summary()
		lines = [f"{r['category']}: Revenue {r['revenue']:.2f}, COGS {r['cogs']:.2f}, Invoices {r['invoices']}" for r in rows]
		self.text.setPlainText('\n'.join(lines) or 'No data')

	def show_profit(self, period: str):
		rows = self.db.profit_report(period)
		lines = [f"{r['period']}: Revenue {r['revenue']:.2f} - COGS {r['cogs']:.2f} - Expenses {r['expenses']:.2f} + Other Income {r.get('other_income', 0):.2f} = Profit {r['profit']:.2f}" for r in rows]
		self.text.setPlainText('\n'.join(lines) or 'No data')

