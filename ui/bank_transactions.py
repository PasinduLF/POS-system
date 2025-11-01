from PyQt5 import QtWidgets
from datetime import datetime


class BankTransactionDialog(QtWidgets.QDialog):
	def __init__(self, db, user, transaction_type: str, parent=None):
		super().__init__(parent)
		self.db = db
		self.user = user
		self.transaction_type = transaction_type  # 'Deposit' or 'Withdrawal'
		self.setWindowTitle(f'{transaction_type} - Bank Transaction')
		
		# Get current cash and bank balances
		cashbook = self.db.cashbook_report()
		bankbook = self.db.bankbook_report()
		
		self.amount = QtWidgets.QDoubleSpinBox()
		self.amount.setPrefix('Amount: ')
		self.amount.setMaximum(100_000_000)
		self.amount.setMinimum(0.01)
		self.description = QtWidgets.QLineEdit()
		self.description.setPlaceholderText('Description (optional)')
		
		# Show available balances
		info_label = QtWidgets.QLabel()
		if transaction_type == 'Deposit':
			available = cashbook['net_cash']
			info_label.setText(f"Available Cash: Rs. {available:.2f}\nDeposit cash to bank account.")
			info_label.setStyleSheet('color: green; font-weight: bold;')
		else:  # Withdrawal
			available = bankbook['net_bank']
			info_label.setText(f"Available Bank Balance: Rs. {available:.2f}\nWithdraw from bank to cash.")
			info_label.setStyleSheet('color: blue; font-weight: bold;')
		
		btn_save = QtWidgets.QPushButton(f'Record {transaction_type}')
		btn_save.clicked.connect(self.save)
		btn_cancel = QtWidgets.QPushButton('Cancel')
		btn_cancel.clicked.connect(self.reject)
		
		layout = QtWidgets.QVBoxLayout(self)
		layout.addWidget(info_label)
		layout.addWidget(QtWidgets.QLabel('Amount:'))
		layout.addWidget(self.amount)
		layout.addWidget(QtWidgets.QLabel('Description:'))
		layout.addWidget(self.description)
		
		buttons = QtWidgets.QHBoxLayout()
		buttons.addStretch()
		buttons.addWidget(btn_save)
		buttons.addWidget(btn_cancel)
		layout.addLayout(buttons)
		
		# Set focus on amount
		self.amount.setFocus()
		
	def save(self):
		amount = float(self.amount.value())
		if amount <= 0:
			QtWidgets.QMessageBox.warning(self, 'Invalid', 'Amount must be greater than 0')
			return
		
		description = self.description.text().strip() or None
		
		# Check available balance
		if self.transaction_type == 'Deposit':
			cashbook = self.db.cashbook_report()
			if amount > cashbook['net_cash']:
				if QtWidgets.QMessageBox.question(
					self, 'Confirm', 
					f"Available cash: Rs. {cashbook['net_cash']:.2f}\nYou are depositing Rs. {amount:.2f}\nThis will result in negative cash balance. Continue?",
					QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
				) != QtWidgets.QMessageBox.Yes:
					return
		else:  # Withdrawal
			bankbook = self.db.bankbook_report()
			if amount > bankbook['net_bank']:
				if QtWidgets.QMessageBox.question(
					self, 'Confirm', 
					f"Available bank balance: Rs. {bankbook['net_bank']:.2f}\nYou are withdrawing Rs. {amount:.2f}\nThis will result in negative bank balance. Continue?",
					QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
				) != QtWidgets.QMessageBox.Yes:
					return
		
		try:
			self.db.add_bank_transaction(self.user['id'], self.transaction_type, amount, description)
			QtWidgets.QMessageBox.information(self, 'Success', f'{self.transaction_type} recorded successfully')
			self.accept()
		except Exception as e:
			QtWidgets.QMessageBox.critical(self, 'Error', f'Failed to record transaction: {str(e)}')


class BankTransactionsDialog(QtWidgets.QDialog):
	def __init__(self, db, user, parent=None):
		super().__init__(parent)
		self.db = db
		self.user = user
		self.setWindowTitle('Bank Transactions')
		
		self.table = QtWidgets.QTableWidget(0, 5)
		self.table.setHorizontalHeaderLabels(['Type', 'Amount', 'Description', 'User', 'Date'])
		self.table.horizontalHeader().setStretchLastSection(True)
		
		btn_refresh = QtWidgets.QPushButton('Refresh')
		btn_deposit = QtWidgets.QPushButton('Deposit (Cash → Bank)')
		btn_withdrawal = QtWidgets.QPushButton('Withdrawal (Bank → Cash)')
		btn_refresh.clicked.connect(self.refresh)
		btn_deposit.clicked.connect(self.add_deposit)
		btn_withdrawal.clicked.connect(self.add_withdrawal)
		
		layout = QtWidgets.QVBoxLayout(self)
		layout.addWidget(self.table)
		bar = QtWidgets.QHBoxLayout()
		bar.addWidget(btn_deposit)
		bar.addWidget(btn_withdrawal)
		bar.addWidget(btn_refresh)
		bar.addStretch()
		layout.addLayout(bar)
		
		self.refresh()
		self.resize(800, 400)
		
	def refresh(self):
		transactions = self.db.list_bank_transactions()
		self.table.setRowCount(0)
		for t in transactions:
			row = self.table.rowCount()
			self.table.insertRow(row)
			self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(t['transaction_type']))
			self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(f"{t['amount']:.2f}"))
			self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(t.get('description') or ''))
			self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(t.get('username') or ''))
			self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(t['created_at']))
		
		# Color code rows
		for row in range(self.table.rowCount()):
			type_item = self.table.item(row, 0)
			if type_item and type_item.text() == 'Deposit':
				self.table.item(row, 1).setForeground(QtWidgets.QColor('green'))
			elif type_item and type_item.text() == 'Withdrawal':
				self.table.item(row, 1).setForeground(QtWidgets.QColor('red'))
	
	def add_deposit(self):
		dlg = BankTransactionDialog(self.db, self.user, 'Deposit', self)
		if dlg.exec_():
			self.refresh()
	
	def add_withdrawal(self):
		dlg = BankTransactionDialog(self.db, self.user, 'Withdrawal', self)
		if dlg.exec_():
			self.refresh()


