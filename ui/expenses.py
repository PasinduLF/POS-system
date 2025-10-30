from PyQt5 import QtWidgets


class ExpensesDialog(QtWidgets.QDialog):
	def __init__(self, db, parent=None):
		super().__init__(parent)
		self.db = db
		self.setWindowTitle('Expenses')
		self.table = QtWidgets.QTableWidget(0, 4)
		self.table.setHorizontalHeaderLabels(['Description', 'Category', 'Amount', 'Date'])
		self.table.horizontalHeader().setStretchLastSection(True)

		self.desc = QtWidgets.QLineEdit(); self.desc.setPlaceholderText('Description')
		self.cat = QtWidgets.QLineEdit(); self.cat.setPlaceholderText('Category')
		self.amount = QtWidgets.QDoubleSpinBox(); self.amount.setMaximum(10_000_000)
		self.date = QtWidgets.QDateEdit(); self.date.setCalendarPopup(True)
		self.date.setDate(self.date.date().currentDate())
		btn_add = QtWidgets.QPushButton('Add Expense')
		btn_add.clicked.connect(self.add_expense)

		self.summary = QtWidgets.QPlainTextEdit(); self.summary.setReadOnly(True)

		layout = QtWidgets.QVBoxLayout(self)
		layout.addWidget(self.table)
		form = QtWidgets.QHBoxLayout()
		form.addWidget(self.desc)
		form.addWidget(self.cat)
		form.addWidget(self.amount)
		form.addWidget(self.date)
		form.addWidget(btn_add)
		layout.addLayout(form)
		layout.addWidget(QtWidgets.QLabel('Monthly Summary'))
		layout.addWidget(self.summary)

		self.refresh()

	def refresh(self):
		# Show latest expenses
		conn = self.db.connection()
		rows = conn.execute('SELECT description, category, amount, incurred_on FROM expenses ORDER BY incurred_on DESC, id DESC LIMIT 200').fetchall()
		self.table.setRowCount(0)
		for r in rows:
			row = self.table.rowCount(); self.table.insertRow(row)
			self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(r['description']))
			self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(r['category'] or ''))
			self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(f"{r['amount']:.2f}"))
			self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(r['incurred_on']))
		# Summary
		sumrows = self.db.monthly_expense_summary()
		self.summary.setPlainText('\n'.join([f"{r['month']}: {r['total']:.2f}" for r in sumrows]) or 'No data')

	def add_expense(self):
		d = self.desc.text().strip()
		if not d:
			QtWidgets.QMessageBox.warning(self, 'Validation', 'Description required')
			return
		c = self.cat.text().strip()
		a = float(self.amount.value())
		incurred = self.date.date().toString('yyyy-MM-dd')
		self.db.add_expense(d, c, a, incurred)
		self.desc.clear(); self.cat.clear(); self.amount.setValue(0)
		self.refresh()



