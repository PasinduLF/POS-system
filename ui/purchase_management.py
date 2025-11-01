from PyQt5 import QtWidgets


class EditPurchaseDialog(QtWidgets.QDialog):
	def __init__(self, db, purchase_id: int, parent=None):
		super().__init__(parent)
		self.db = db
		self.purchase_id = purchase_id
		self.setWindowTitle('Edit Purchase')
		self.table = QtWidgets.QTableWidget(0, 4)
		self.table.setHorizontalHeaderLabels(['Product', 'Product ID', 'Qty', 'Unit Cost'])
		self.table.horizontalHeader().setStretchLastSection(True)
		self.supplier_name = QtWidgets.QLineEdit(); self.supplier_name.setPlaceholderText('Supplier name')
		self.payment_type = QtWidgets.QComboBox(); self.payment_type.addItems(['Cash', 'Card', 'Cheque', 'Credit', 'Other'])
		self.paid_amount = QtWidgets.QDoubleSpinBox(); self.paid_amount.setPrefix('Paid: '); self.paid_amount.setMaximum(1_000_000)
		btn_save = QtWidgets.QPushButton('Save Changes')
		btn_save.clicked.connect(self.save)

		layout = QtWidgets.QVBoxLayout(self)
		layout.addWidget(self.table)
		form = QtWidgets.QHBoxLayout()
		form.addWidget(self.supplier_name)
		form.addWidget(self.payment_type)
		form.addWidget(self.paid_amount)
		layout.addLayout(form)
		layout.addWidget(btn_save)

		self.load()

	def load(self):
		conn = self.db.connection()
		row = conn.execute('SELECT supplier_name, payment_type, paid_amount FROM purchases WHERE id=?', (self.purchase_id,)).fetchone()
		if row:
			self.supplier_name.setText(row['supplier_name'] or '')
			idx = self.payment_type.findText(row['payment_type'])
			self.payment_type.setCurrentIndex(max(0, idx))
			self.paid_amount.setValue(float(row['paid_amount']))
		items = conn.execute(
			'SELECT pi.*, p.name AS product_name FROM purchase_items pi JOIN products p ON p.id=pi.product_id WHERE purchase_id=? ORDER BY pi.id',
			(self.purchase_id,)
		).fetchall()
		self.table.setRowCount(0)
		for it in items:
			row_idx = self.table.rowCount()
			self.table.insertRow(row_idx)
			self.table.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(it['product_name']))
			self.table.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(str(it['product_id'])))
			self.table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(str(it['quantity'])))
			self.table.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(f"{it['unit_cost']:.2f}"))

	def save(self):
		conn = self.db.connection()
		# collect new items
		items = []
		for r in range(self.table.rowCount()):
			pid = int(self.table.item(r, 1).text())
			qty = int(float(self.table.item(r, 2).text()))
			cost = float(self.table.item(r, 3).text())
			if qty <= 0:
				continue
			line_total = cost * qty
			items.append({'product_id': pid, 'quantity': qty, 'unit_cost': cost, 'line_total': line_total})
		
		supplier_name = self.supplier_name.text().strip() or None
		payment_type = self.payment_type.currentText()
		paid_amount = float(self.paid_amount.value())
		
		# transaction: restore old stock, replace items, adjust stock, update purchase header
		with conn:
			# Restore old stock (decrease by old quantities)
			old_items = conn.execute('SELECT product_id, quantity FROM purchase_items WHERE purchase_id=?', (self.purchase_id,)).fetchall()
			for r in old_items:
				conn.execute('UPDATE products SET stock_quantity = stock_quantity - ? WHERE id=?', (r['quantity'], r['product_id']))
			
			# Delete old items
			conn.execute('DELETE FROM purchase_items WHERE purchase_id=?', (self.purchase_id,))
			
			# Insert new items and update stock
			for it in items:
				conn.execute(
					'INSERT INTO purchase_items (purchase_id, product_id, quantity, unit_cost, line_total) VALUES (?, ?, ?, ?, ?)',
					(self.purchase_id, it['product_id'], it['quantity'], it['unit_cost'], it['line_total'])
				)
				conn.execute('UPDATE products SET stock_quantity = stock_quantity + ? WHERE id=?', (it['quantity'], it['product_id']))
				conn.execute('UPDATE products SET cost_price = ? WHERE id=?', (it['unit_cost'], it['product_id']))
			
			total_amount = sum(i['line_total'] for i in items)
			conn.execute(
				'UPDATE purchases SET total_amount=?, supplier_name=?, payment_type=?, paid_amount=? WHERE id=?',
				(total_amount, supplier_name, payment_type, paid_amount, self.purchase_id)
			)
		self.accept()


class PurchasesDialog(QtWidgets.QDialog):
	def __init__(self, db, parent=None):
		super().__init__(parent)
		self.db = db
		self.setWindowTitle('Purchase Management')
		self.table = QtWidgets.QTableWidget(0, 6)
		self.table.setHorizontalHeaderLabels(['ID', 'Bill ID', 'Supplier', 'Total', 'Payment', 'Date'])
		self.table.horizontalHeader().setStretchLastSection(True)

		btn_refresh = QtWidgets.QPushButton('Refresh')
		btn_edit = QtWidgets.QPushButton('View / Edit')
		btn_delete = QtWidgets.QPushButton('Delete Purchase')
		btn_refresh.clicked.connect(self.refresh)
		btn_edit.clicked.connect(self.edit_purchase)
		btn_delete.clicked.connect(self.delete_purchase)

		layout = QtWidgets.QVBoxLayout(self)
		layout.addWidget(self.table)
		bar = QtWidgets.QHBoxLayout()
		bar.addWidget(btn_refresh)
		bar.addWidget(btn_edit)
		bar.addWidget(btn_delete)
		bar.addStretch()
		layout.addLayout(bar)

		self.refresh()
		self.resize_to_fit_table()

	def resize_to_fit_table(self):
		# Resize window to fit table content
		self.table.resizeColumnsToContents()
		table_width = self.table.horizontalHeader().length() + 40
		table_height = min(self.table.verticalHeader().length() + 80, 600)
		self.resize(max(800, table_width), min(600, table_height))

	def refresh(self):
		purchases = self.db.list_purchases(limit=200)
		self.table.setRowCount(0)
		for p in purchases:
			row = self.table.rowCount()
			self.table.insertRow(row)
			self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(p['id'])))
			self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(p['bill_id']))
			self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(p.get('supplier_name') or ''))
			self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{p['total_amount']:.2f}"))
			self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(p['payment_type']))
			self.table.setItem(row, 5, QtWidgets.QTableWidgetItem(p['created_at']))
		self.resize_to_fit_table()

	def current_purchase_id(self):
		row = self.table.currentRow()
		if row < 0:
			return None
		return int(self.table.item(row, 0).text())

	def edit_purchase(self):
		pid = self.current_purchase_id()
		if not pid:
			return
		dlg = EditPurchaseDialog(self.db, pid, self)
		if dlg.exec_():
			self.refresh()

	def delete_purchase(self):
		pid = self.current_purchase_id()
		if not pid:
			return
		if QtWidgets.QMessageBox.question(self, 'Confirm', 'Delete this purchase and reduce stock?') != QtWidgets.QMessageBox.Yes:
			return
		conn = self.db.connection()
		try:
			with conn:
				# Reduce stock by the quantities purchased
				rows = conn.execute('SELECT product_id, quantity FROM purchase_items WHERE purchase_id=?', (pid,)).fetchall()
				for r in rows:
					conn.execute('UPDATE products SET stock_quantity = stock_quantity - ? WHERE id=?', (r['quantity'], r['product_id']))
				conn.execute('DELETE FROM purchase_items WHERE purchase_id=?', (pid,))
				conn.execute('DELETE FROM purchases WHERE id=?', (pid,))
			self.refresh()
		except Exception as e:
			QtWidgets.QMessageBox.critical(self, 'Delete Failed', str(e))


