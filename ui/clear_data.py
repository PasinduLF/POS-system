from PyQt5 import QtWidgets
import sqlite3


class ClearDataDialog(QtWidgets.QDialog):
	def __init__(self, db, parent=None):
		super().__init__(parent)
		self.db = db
		self.setWindowTitle('Clear Data')
		self.setModal(True)
		self.resize(500, 450)
		
		warning_label = QtWidgets.QLabel(
			'⚠️ WARNING: Selected data will be PERMANENTLY DELETED!\n\n'
			'This action CANNOT be undone!\n\n'
			'Select the data types you want to clear:'
		)
		warning_label.setStyleSheet('color: red; font-weight: bold; padding: 10px;')
		
		# Checkboxes for data selection
		checkbox_group = QtWidgets.QGroupBox('Select Data to Clear')
		checkbox_layout = QtWidgets.QVBoxLayout()
		
		self.chk_sales = QtWidgets.QCheckBox('Sales & Sale Items')
		self.chk_purchases = QtWidgets.QCheckBox('Purchases & Purchase Items')
		self.chk_products = QtWidgets.QCheckBox('Products')
		self.chk_categories = QtWidgets.QCheckBox('Categories')
		self.chk_brands = QtWidgets.QCheckBox('Brands')
		self.chk_customers = QtWidgets.QCheckBox('Customers')
		self.chk_expenses = QtWidgets.QCheckBox('Expenses')
		self.chk_income = QtWidgets.QCheckBox('Other Income')
		self.chk_bank = QtWidgets.QCheckBox('Bank Transactions')
		
		checkbox_layout.addWidget(self.chk_sales)
		checkbox_layout.addWidget(self.chk_purchases)
		checkbox_layout.addWidget(self.chk_products)
		checkbox_layout.addWidget(self.chk_categories)
		checkbox_layout.addWidget(self.chk_brands)
		checkbox_layout.addWidget(self.chk_customers)
		checkbox_layout.addWidget(self.chk_expenses)
		checkbox_layout.addWidget(self.chk_income)
		checkbox_layout.addWidget(self.chk_bank)
		
		# Select All / Deselect All buttons
		select_buttons = QtWidgets.QHBoxLayout()
		btn_select_all = QtWidgets.QPushButton('Select All')
		btn_deselect_all = QtWidgets.QPushButton('Deselect All')
		btn_select_all.clicked.connect(self._select_all)
		btn_deselect_all.clicked.connect(self._deselect_all)
		select_buttons.addWidget(btn_select_all)
		select_buttons.addWidget(btn_deselect_all)
		select_buttons.addStretch()
		checkbox_layout.addLayout(select_buttons)
		
		checkbox_group.setLayout(checkbox_layout)
		
		# Password field
		self.password = QtWidgets.QLineEdit()
		self.password.setEchoMode(QtWidgets.QLineEdit.Password)
		self.password.setPlaceholderText('Enter admin password to confirm')
		
		form_layout = QtWidgets.QFormLayout()
		form_layout.addRow('Admin Password:', self.password)
		
		btn_clear = QtWidgets.QPushButton('Clear Selected Data')
		btn_clear.setStyleSheet('background: red; color: white; font-weight: bold;')
		btn_clear.clicked.connect(self.clear_data)
		btn_cancel = QtWidgets.QPushButton('Cancel')
		btn_cancel.clicked.connect(self.reject)
		
		layout = QtWidgets.QVBoxLayout(self)
		layout.addWidget(warning_label)
		layout.addWidget(checkbox_group)
		layout.addLayout(form_layout)
		
		buttons = QtWidgets.QHBoxLayout()
		buttons.addStretch()
		buttons.addWidget(btn_clear)
		buttons.addWidget(btn_cancel)
		layout.addLayout(buttons)
		
		# Set focus on password field
		self.password.setFocus()
	
	def _select_all(self):
		self.chk_sales.setChecked(True)
		self.chk_purchases.setChecked(True)
		self.chk_products.setChecked(True)
		self.chk_categories.setChecked(True)
		self.chk_brands.setChecked(True)
		self.chk_customers.setChecked(True)
		self.chk_expenses.setChecked(True)
		self.chk_income.setChecked(True)
		self.chk_bank.setChecked(True)
	
	def _deselect_all(self):
		self.chk_sales.setChecked(False)
		self.chk_purchases.setChecked(False)
		self.chk_products.setChecked(False)
		self.chk_categories.setChecked(False)
		self.chk_brands.setChecked(False)
		self.chk_customers.setChecked(False)
		self.chk_expenses.setChecked(False)
		self.chk_income.setChecked(False)
		self.chk_bank.setChecked(False)
	
	def _get_selected_items(self):
		selected = []
		if self.chk_sales.isChecked():
			selected.append('Sales & Sale Items')
		if self.chk_purchases.isChecked():
			selected.append('Purchases & Purchase Items')
		if self.chk_products.isChecked():
			selected.append('Products')
		if self.chk_categories.isChecked():
			selected.append('Categories')
		if self.chk_brands.isChecked():
			selected.append('Brands')
		if self.chk_customers.isChecked():
			selected.append('Customers')
		if self.chk_expenses.isChecked():
			selected.append('Expenses')
		if self.chk_income.isChecked():
			selected.append('Other Income')
		if self.chk_bank.isChecked():
			selected.append('Bank Transactions')
		return selected
	
	def clear_data(self):
		selected = self._get_selected_items()
		if not selected:
			QtWidgets.QMessageBox.warning(self, 'Nothing Selected', 'Please select at least one data type to clear.')
			return
		
		password = self.password.text().strip()
		if not password:
			QtWidgets.QMessageBox.warning(self, 'Password Required', 'Please enter admin password')
			return
		
		# Verify admin password
		admin_user = self.db.authenticate_user('admin', password)
		if not admin_user:
			QtWidgets.QMessageBox.warning(self, 'Invalid Password', 'Incorrect admin password. Data was not cleared.')
			self.password.clear()
			return
		
		# Build confirmation message
		items_text = '\n'.join([f'  • {item}' for item in selected])
		reply = QtWidgets.QMessageBox.question(
			self, 
			'Final Confirmation',
			f'Are you absolutely sure you want to delete the following data?\n\n{items_text}\n\n'
			'This action CANNOT be undone!\n\n'
			'Click "Yes" to proceed.',
			QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
			QtWidgets.QMessageBox.No
		)
		
		if reply != QtWidgets.QMessageBox.Yes:
			return
		
		try:
			conn = self.db.connection()
			with conn:
				# Disable foreign keys temporarily for easier deletion
				conn.execute('PRAGMA foreign_keys = OFF')
				
				# Clear selected data tables
				if self.chk_sales.isChecked():
					conn.execute('DELETE FROM sale_items')
					conn.execute('DELETE FROM sales')
				
				if self.chk_purchases.isChecked():
					conn.execute('DELETE FROM purchase_items')
					conn.execute('DELETE FROM purchases')
				
				if self.chk_bank.isChecked():
					conn.execute('DELETE FROM bank_transactions')
				
				if self.chk_expenses.isChecked():
					conn.execute('DELETE FROM expenses')
				
				if self.chk_income.isChecked():
					conn.execute('DELETE FROM other_income')
				
				if self.chk_customers.isChecked():
					conn.execute('DELETE FROM customers')
				
				if self.chk_products.isChecked():
					conn.execute('DELETE FROM products')
				
				if self.chk_categories.isChecked():
					conn.execute('DELETE FROM categories')
				
				if self.chk_brands.isChecked():
					conn.execute('DELETE FROM brands')
				
				# Re-enable foreign keys
				conn.execute('PRAGMA foreign_keys = ON')
			
			QtWidgets.QMessageBox.information(
				self, 
				'Data Cleared', 
				f'Selected data has been successfully cleared.\n\nCleared: {", ".join(selected)}'
			)
			self.accept()
		except Exception as e:
			QtWidgets.QMessageBox.critical(self, 'Clear Data Failed', f'Failed to clear data: {str(e)}')

