from PyQt5 import QtWidgets


class ReportsWidget(QtWidgets.QWidget):
	def __init__(self, db, parent=None):
		super().__init__(parent)
		self.db = db
		self.setLayout(QtWidgets.QVBoxLayout())

		self.btn_daily = QtWidgets.QPushButton('Daily Sales Summary')
		self.btn_monthly = QtWidgets.QPushButton('Monthly Sales Summary')
		self.btn_yearly = QtWidgets.QPushButton('Yearly Sales Summary')
		self.btn_top = QtWidgets.QPushButton('Top Products')
		self.btn_inventory = QtWidgets.QPushButton('Inventory Report')
		self.btn_expenses = QtWidgets.QPushButton('Monthly Expense Summary')
		self.btn_category = QtWidgets.QPushButton('Category-wise Sales Summary')
		self.btn_profit_d = QtWidgets.QPushButton('Profit Report (Daily)')
		self.btn_profit_m = QtWidgets.QPushButton('Profit Report (Monthly)')
		self.btn_profit_y = QtWidgets.QPushButton('Profit Report (Yearly)')

		for b in [self.btn_daily, self.btn_monthly, self.btn_yearly, self.btn_top, self.btn_inventory, self.btn_expenses, self.btn_category, self.btn_profit_d, self.btn_profit_m, self.btn_profit_y]:
			self.layout().addWidget(b)

		self.text = QtWidgets.QPlainTextEdit(); self.text.setReadOnly(True)
		self.layout().addWidget(self.text)

		self.btn_daily.clicked.connect(lambda: self.show_sales('daily'))
		self.btn_monthly.clicked.connect(lambda: self.show_sales('monthly'))
		self.btn_yearly.clicked.connect(lambda: self.show_sales('yearly'))
		self.btn_top.clicked.connect(self.show_top)
		self.btn_inventory.clicked.connect(self.show_inventory)
		self.btn_expenses.clicked.connect(self.show_expenses)
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

	def show_category(self):
		rows = self.db.category_sales_summary()
		lines = [f"{r['category']}: Revenue {r['revenue']:.2f}, COGS {r['cogs']:.2f}, Invoices {r['invoices']}" for r in rows]
		self.text.setPlainText('\n'.join(lines) or 'No data')

	def show_profit(self, period: str):
		rows = self.db.profit_report(period)
		lines = [f"{r['period']}: Revenue {r['revenue']:.2f} - COGS {r['cogs']:.2f} - Expenses {r['expenses']:.2f} = Profit {r['profit']:.2f}" for r in rows]
		self.text.setPlainText('\n'.join(lines) or 'No data')

