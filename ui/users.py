from PyQt5 import QtWidgets


class UsersDialog(QtWidgets.QDialog):
	def __init__(self, db, parent=None):
		super().__init__(parent)
		self.db = db
		self.setWindowTitle('Manage Users')
		self.table = QtWidgets.QTableWidget(0, 3)
		self.table.setHorizontalHeaderLabels(['ID', 'Username', 'Role'])
		self.table.horizontalHeader().setStretchLastSection(True)

		self.username = QtWidgets.QLineEdit(); self.username.setPlaceholderText('username')
		self.password = QtWidgets.QLineEdit(); self.password.setPlaceholderText('password')
		self.role = QtWidgets.QComboBox(); self.role.addItems(['admin', 'cashier'])
		btn_add = QtWidgets.QPushButton('Add User')
		btn_reset = QtWidgets.QPushButton('Reset Password')
		btn_delete = QtWidgets.QPushButton('Delete User')
		btn_add.clicked.connect(self.add_user)
		btn_reset.clicked.connect(self.reset_password)
		btn_delete.clicked.connect(self.delete_user)

		layout = QtWidgets.QVBoxLayout(self)
		layout.addWidget(self.table)
		form = QtWidgets.QHBoxLayout()
		form.addWidget(self.username)
		form.addWidget(self.password)
		form.addWidget(self.role)
		form.addWidget(btn_add)
		layout.addLayout(form)
		layout.addWidget(btn_reset)
		layout.addWidget(btn_delete)

		self.refresh()

	def refresh(self):
		self.table.setRowCount(0)
		for u in self.db.list_users():
			row = self.table.rowCount(); self.table.insertRow(row)
			self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(u['id'])))
			self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(u['username']))
			self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(u['role']))

	def selected_user_id(self):
		row = self.table.currentRow()
		if row < 0:
			return None
		return int(self.table.item(row, 0).text())

	def add_user(self):
		uname = self.username.text().strip()
		pwd = self.password.text().strip()
		role = self.role.currentText()
		if not uname or not pwd:
			QtWidgets.QMessageBox.warning(self, 'Validation', 'Username and password are required')
			return
		try:
			self.db.create_user(uname, pwd, role)
			self.username.clear(); self.password.clear()
			self.refresh()
		except Exception as e:
			QtWidgets.QMessageBox.critical(self, 'Add Failed', str(e))

	def reset_password(self):
		uid = self.selected_user_id()
		if not uid:
			return
		pwd, ok = QtWidgets.QInputDialog.getText(self, 'Reset Password', 'New password:')
		if not ok or not pwd:
			return
		self.db.update_user_password(uid, pwd)
		QtWidgets.QMessageBox.information(self, 'Reset', 'Password updated')

	def delete_user(self):
		uid = self.selected_user_id()
		if not uid:
			return
		if QtWidgets.QMessageBox.question(self, 'Confirm', 'Delete user?') == QtWidgets.QMessageBox.Yes:
			self.db.delete_user(uid)
			self.refresh()









