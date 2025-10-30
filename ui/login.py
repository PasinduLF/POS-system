from PyQt5 import QtWidgets


class LoginDialog(QtWidgets.QDialog):
	def __init__(self, db, parent=None):
		super().__init__(parent)
		self.db = db
		self._user = None
		self.setWindowTitle('Beauty P&C POS - Login')
		self.username = QtWidgets.QLineEdit()
		self.password = QtWidgets.QLineEdit()
		self.password.setEchoMode(QtWidgets.QLineEdit.Password)
		self.error_label = QtWidgets.QLabel('')
		self.error_label.setStyleSheet('color: red;')
		self.error_label.hide()
		btn = QtWidgets.QPushButton('Login')
		btn.clicked.connect(self.handle_login)
		self.username.returnPressed.connect(self.handle_login)
		self.password.returnPressed.connect(self.handle_login)

		layout = QtWidgets.QFormLayout()
		layout.addRow('Username', self.username)
		layout.addRow('Password', self.password)
		layout.addRow(self.error_label)
		layout.addRow(btn)
		self.setLayout(layout)

	def handle_login(self):
		self.error_label.hide()
		user = self.db.authenticate_user(self.username.text().strip(), self.password.text())
		if user:
			self._user = user
			self.accept()
		else:
			self.error_label.setText('Invalid username or password')
			self.error_label.show()
			QtWidgets.QMessageBox.warning(self, 'Login Failed', 'Invalid credentials')

	def get_authenticated_user(self):
		return self._user

