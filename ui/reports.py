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
		self.btn_customers = QtWidgets.QPushButton('Customer Details')
		sales_layout.addWidget(self.btn_daily, 0, 0)
		sales_layout.addWidget(self.btn_monthly, 0, 1)
		sales_layout.addWidget(self.btn_yearly, 0, 2)
		sales_layout.addWidget(self.btn_category, 1, 0)
		sales_layout.addWidget(self.btn_top, 1, 1)
		sales_layout.addWidget(self.btn_customers, 1, 2)
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
		self.btn_cashbook = QtWidgets.QPushButton('📗 Cashbook')
		self.btn_cashbook.setStyleSheet('font-weight: bold;')
		self.btn_bankbook = QtWidgets.QPushButton('🏦 Bankbook')
		self.btn_bankbook.setStyleSheet('font-weight: bold;')
		financial_layout.addWidget(self.btn_profit_d, 0, 0)
		financial_layout.addWidget(self.btn_profit_m, 0, 1)
		financial_layout.addWidget(self.btn_profit_y, 0, 2)
		financial_layout.addWidget(self.btn_expenses, 1, 0)
		financial_layout.addWidget(self.btn_income, 1, 1)
		financial_layout.addWidget(self.btn_cashbook, 1, 2)
		financial_layout.addWidget(self.btn_bankbook, 2, 0)
		financial_group.setLayout(financial_layout)
		left_panel.addWidget(financial_group)

		# Purchase Reports Group
		purchase_group = QtWidgets.QGroupBox('🛒 Purchase Reports')
		purchase_layout = QtWidgets.QGridLayout()
		self.btn_purchases_d = QtWidgets.QPushButton('Daily Purchases')
		self.btn_purchases_m = QtWidgets.QPushButton('Monthly Purchases')
		self.btn_purchases_y = QtWidgets.QPushButton('Yearly Purchases')
		self.btn_top_purchased = QtWidgets.QPushButton('Top Purchased')
		self.btn_suppliers = QtWidgets.QPushButton('Supplier Summary')
		purchase_layout.addWidget(self.btn_purchases_d, 0, 0)
		purchase_layout.addWidget(self.btn_purchases_m, 0, 1)
		purchase_layout.addWidget(self.btn_purchases_y, 0, 2)
		purchase_layout.addWidget(self.btn_top_purchased, 1, 0)
		purchase_layout.addWidget(self.btn_suppliers, 1, 1)
		purchase_group.setLayout(purchase_layout)
		left_panel.addWidget(purchase_group)

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
		self.table = QtWidgets.QTableWidget()
		self.table.setAlternatingRowColors(True)
		self.table.horizontalHeader().setStretchLastSection(True)
		try:
			self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
		except Exception:
			pass
		right_panel.addWidget(self.table)

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
		self.btn_cashbook.clicked.connect(self.show_cashbook)
		self.btn_bankbook.clicked.connect(self.show_bankbook)
		self.btn_purchases_d.clicked.connect(lambda: self.show_purchases('daily'))
		self.btn_purchases_m.clicked.connect(lambda: self.show_purchases('monthly'))
		self.btn_purchases_y.clicked.connect(lambda: self.show_purchases('yearly'))
		self.btn_top_purchased.clicked.connect(self.show_top_purchased)
		self.btn_suppliers.clicked.connect(self.show_suppliers)
		self.btn_customers.clicked.connect(self.show_customer_details)

	def _populate_table(self, headers: list, rows: list):
		self.table.setColumnCount(len(headers))
		self.table.setHorizontalHeaderLabels(headers)
		self.table.setRowCount(0)
		
		# Get theme to set proper text color for items
		theme = self.db.get_setting('theme', 'Light')
		is_dark = theme.lower() == 'dark'
		text_color = QtGui.QColor('#e0e0e0') if is_dark else QtGui.QColor('#333333')
		
		for r in rows:
			row_idx = self.table.rowCount()
			self.table.insertRow(row_idx)
			if isinstance(r, dict):
				for col_idx, header in enumerate(headers):
					val = r.get(header, '')
					item = QtWidgets.QTableWidgetItem(str(val) if val is not None else '')
					if isinstance(val, (int, float)) or (isinstance(val, str) and val.replace('.', '', 1).replace('-', '', 1).isdigit()):
						item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
					# Ensure text color respects theme
					item.setForeground(QtGui.QBrush(text_color))
					self.table.setItem(row_idx, col_idx, item)
			else:
				for col_idx, val in enumerate(r):
					item = QtWidgets.QTableWidgetItem(str(val) if val is not None else '')
					if isinstance(val, (int, float)):
						item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
					# Ensure text color respects theme
					item.setForeground(QtGui.QBrush(text_color))
					self.table.setItem(row_idx, col_idx, item)

	def show_sales(self, period: str):
		rows = self.db.sales_summary(period)
		if not rows:
			self.table.setColumnCount(2)
			self.table.setHorizontalHeaderLabels(['Period', 'Total'])
			self.table.setRowCount(0)
			return
		data = [{'Period': r['period'], 'Total (Rs.)': f"{r['total']:.2f}"} for r in rows]
		self._populate_table(['Period', 'Total (Rs.)'], data)

	def show_top(self):
		rows = self.db.top_products()
		if not rows:
			self.table.setColumnCount(3)
			self.table.setHorizontalHeaderLabels(['Product', 'Quantity', 'Revenue (Rs.)'])
			self.table.setRowCount(0)
			return
		data = [{'Product': r['name'], 'Quantity': r['qty'], 'Revenue (Rs.)': f"{r['revenue']:.2f}"} for r in rows]
		self._populate_table(['Product', 'Quantity', 'Revenue (Rs.)'], data)

	def show_inventory(self):
		rows = self.db.inventory_report()
		if not rows:
			self.table.setColumnCount(6)
			self.table.setHorizontalHeaderLabels(['Name', 'Brand', 'Stock', 'Cost Price', 'Selling Price', 'Value'])
			self.table.setRowCount(0)
			return
		data = []
		for r in rows:
			value = float(r['stock_quantity']) * float(r['cost_price'])
			data.append({
				'Name': r['name'],
				'Brand': r.get('brand') or '',
				'Stock': r['stock_quantity'],
				'Cost Price (Rs.)': f"{r['cost_price']:.2f}",
				'Selling Price (Rs.)': f"{r['price']:.2f}",
				'Stock Value (Rs.)': f"{value:.2f}"
			})
		self._populate_table(['Name', 'Brand', 'Stock', 'Cost Price (Rs.)', 'Selling Price (Rs.)', 'Stock Value (Rs.)'], data)

	def show_expenses(self):
		rows = self.db.monthly_expense_summary()
		if not rows:
			self.table.setColumnCount(2)
			self.table.setHorizontalHeaderLabels(['Month', 'Total (Rs.)'])
			self.table.setRowCount(0)
			return
		data = [{'Month': r['month'], 'Total (Rs.)': f"{r['total']:.2f}"} for r in rows]
		self._populate_table(['Month', 'Total (Rs.)'], data)

	def show_income(self):
		rows = self.db.monthly_income_summary()
		if not rows:
			self.table.setColumnCount(2)
			self.table.setHorizontalHeaderLabels(['Month', 'Total (Rs.)'])
			self.table.setRowCount(0)
			return
		data = [{'Month': r['month'], 'Total (Rs.)': f"{r['total']:.2f}"} for r in rows]
		self._populate_table(['Month', 'Total (Rs.)'], data)

	def show_category(self):
		rows = self.db.category_sales_summary()
		if not rows:
			self.table.setColumnCount(4)
			self.table.setHorizontalHeaderLabels(['Category', 'Revenue (Rs.)', 'COGS (Rs.)', 'Invoices'])
			self.table.setRowCount(0)
			return
		data = [{'Category': r['category'], 'Revenue (Rs.)': f"{r['revenue']:.2f}", 'COGS (Rs.)': f"{r['cogs']:.2f}", 'Invoices': r['invoices']} for r in rows]
		self._populate_table(['Category', 'Revenue (Rs.)', 'COGS (Rs.)', 'Invoices'], data)

	def show_profit(self, period: str):
		rows = self.db.profit_report(period)
		if not rows:
			self.table.setColumnCount(6)
			self.table.setHorizontalHeaderLabels(['Period', 'Revenue (Rs.)', 'COGS (Rs.)', 'Expenses (Rs.)', 'Other Income (Rs.)', 'Profit (Rs.)'])
			self.table.setRowCount(0)
			return
		data = []
		for r in rows:
			data.append({
				'Period': r['period'],
				'Revenue (Rs.)': f"{r['revenue']:.2f}",
				'COGS (Rs.)': f"{r['cogs']:.2f}",
				'Expenses (Rs.)': f"{r['expenses']:.2f}",
				'Other Income (Rs.)': f"{r.get('other_income', 0):.2f}",
				'Profit (Rs.)': f"{r['profit']:.2f}"
			})
		self._populate_table(['Period', 'Revenue (Rs.)', 'COGS (Rs.)', 'Expenses (Rs.)', 'Other Income (Rs.)', 'Profit (Rs.)'], data)

	def show_cashbook(self):
		data = self.db.cashbook_report()
		rows = [
			{'Item': 'Cash Sales', 'Amount (Rs.)': f"{data['cash_sales']:.2f}"},
			{'Item': 'Other Income', 'Amount (Rs.)': f"{data['other_income']:.2f}"},
			{'Item': 'Bank Withdrawals', 'Amount (Rs.)': f"{data['withdrawals']:.2f}"},
			{'Item': 'Total Received', 'Amount (Rs.)': f"{data['total_received']:.2f}"},
			{'Item': 'Cash Expenses', 'Amount (Rs.)': f"{data['cash_expenses']:.2f}"},
			{'Item': 'Cash Purchases', 'Amount (Rs.)': f"{data['cash_purchases']:.2f}"},
			{'Item': 'Bank Deposits', 'Amount (Rs.)': f"{data['deposits']:.2f}"},
			{'Item': 'Total Paid Out', 'Amount (Rs.)': f"{data['total_paid_out']:.2f}"},
			{'Item': 'Net Cash Balance', 'Amount (Rs.)': f"{data['net_cash']:.2f}"}
		]
		self._populate_table(['Item', 'Amount (Rs.)'], rows)

	def show_purchases(self, period: str):
		rows = self.db.purchases_summary(period)
		if not rows:
			self.table.setColumnCount(3)
			self.table.setHorizontalHeaderLabels(['Period', 'Total (Rs.)', 'Count'])
			self.table.setRowCount(0)
			return
		data = [
			{'Period': r['period'], 'Total (Rs.)': f"{r['total']:.2f}", 'Count': r['count']}
			for r in rows
		]
		self._populate_table(['Period', 'Total (Rs.)', 'Count'], data)

	def show_top_purchased(self):
		rows = self.db.top_purchased_products()
		if not rows:
			self.table.setColumnCount(3)
			self.table.setHorizontalHeaderLabels(['Product', 'Quantity', 'Total Cost (Rs.)'])
			self.table.setRowCount(0)
			return
		data = [
			{'Product': r['name'], 'Quantity': r['qty'], 'Total Cost (Rs.)': f"{r['total_cost']:.2f}"}
			for r in rows
		]
		self._populate_table(['Product', 'Quantity', 'Total Cost (Rs.)'], data)

	def show_suppliers(self):
		rows = self.db.supplier_summary()
		if not rows:
			self.table.setColumnCount(3)
			self.table.setHorizontalHeaderLabels(['Supplier', 'Total (Rs.)', 'Count'])
			self.table.setRowCount(0)
			return
		data = [
			{'Supplier': r['supplier'], 'Total (Rs.)': f"{r['total']:.2f}", 'Count': r['count']}
			for r in rows
		]
		self._populate_table(['Supplier', 'Total (Rs.)', 'Count'], data)

	def show_bankbook(self):
		data = self.db.bankbook_report()
		rows = [
			{'Item': 'Card Sales', 'Amount (Rs.)': f"{data['card_sales']:.2f}"},
			{'Item': 'Deposits', 'Amount (Rs.)': f"{data['deposits']:.2f}"},
			{'Item': 'Total Received', 'Amount (Rs.)': f"{data['total_received']:.2f}"},
			{'Item': 'Card Purchases', 'Amount (Rs.)': f"{data['card_purchases']:.2f}"},
			{'Item': 'Card Expenses', 'Amount (Rs.)': f"{data['card_expenses']:.2f}"},
			{'Item': 'Withdrawals', 'Amount (Rs.)': f"{data['withdrawals']:.2f}"},
			{'Item': 'Total Paid Out', 'Amount (Rs.)': f"{data['total_paid_out']:.2f}"},
			{'Item': 'Net Bank Balance', 'Amount (Rs.)': f"{data['net_bank']:.2f}"}
		]
		self._populate_table(['Item', 'Amount (Rs.)'], rows)

	def show_customer_details(self):
		rows = self.db.customer_details_report()
		if not rows:
			self.table.setColumnCount(5)
			self.table.setHorizontalHeaderLabels(['Customer', 'Phone', 'Total Sales (Rs.)', 'Invoice Count', 'Last Purchase'])
			self.table.setRowCount(0)
			return
		
		data = []
		for r in rows:
			data.append({
				'Customer': r['name'] or 'Unknown',
				'Phone': r['phone'] or '',
				'Total Sales (Rs.)': f"{r['total_sales']:.2f}",
				'Invoice Count': r['invoice_count'],
				'Last Purchase': r['last_purchase'] or ''
			})
		
		self._populate_table(['Customer', 'Phone', 'Total Sales (Rs.)', 'Invoice Count', 'Last Purchase'], data)

