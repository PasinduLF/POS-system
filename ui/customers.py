from PyQt5 import QtWidgets


class CustomersDialog(QtWidgets.QDialog):
	def __init__(self, db, parent=None):
		super().__init__(parent)
		self.db = db
		self.setWindowTitle('Customers')
		self.table = QtWidgets.QTableWidget(0, 3)
		self.table.setHorizontalHeaderLabels(['Name', 'Phone', 'Created'])
		self.table.horizontalHeader().setStretchLastSection(True)

		self.name = QtWidgets.QLineEdit(); self.name.setPlaceholderText('Name (optional)')
		self.phone = QtWidgets.QLineEdit(); self.phone.setPlaceholderText('Phone (optional)')
		btn_add = QtWidgets.QPushButton('Add / Update')
		btn_add.clicked.connect(self.add_or_update)
		btn_delete = QtWidgets.QPushButton('Delete')
		btn_delete.clicked.connect(self.delete)

		layout = QtWidgets.QVBoxLayout(self)
		layout.addWidget(self.table)
		form = QtWidgets.QHBoxLayout(); form.addWidget(self.name); form.addWidget(self.phone); form.addWidget(btn_add); form.addWidget(btn_delete)
		layout.addLayout(form)

		self.refresh()

	def refresh(self):
		rows = self.db.list_customers()
		self.table.setRowCount(0)
		for r in rows:
			row = self.table.rowCount(); self.table.insertRow(row)
			self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(r.get('name') or ''))
			self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(r.get('phone') or ''))
			self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(r.get('created_at') or ''))

	def selected_customer(self):
		row = self.table.currentRow()
		if row < 0:
			return None
		name = self.table.item(row, 0).text()
		phone = self.table.item(row, 1).text()
		# Find id by matching phone first
		for c in self.db.list_customers():
			if (c.get('phone') or '') == phone and (c.get('name') or '') == name:
				return c
		return None

	def add_or_update(self):
		name = self.name.text().strip()
		phone = self.phone.text().strip()
		if not name and not phone:
			QtWidgets.QMessageBox.warning(self, 'Validation', 'Enter name or phone')
			return
		cid = self.db.upsert_customer(name, phone)
		QtWidgets.QMessageBox.information(self, 'Saved', 'Customer saved')
		self.refresh()

	def delete(self):
		c = self.selected_customer()
		if not c:
			return
		if QtWidgets.QMessageBox.question(self, 'Confirm', 'Delete selected customer?') != QtWidgets.QMessageBox.Yes:
			return
		self.db.delete_customer(c['id'])
		self.refresh()






