from PyQt5 import QtWidgets


class EditSaleDialog(QtWidgets.QDialog):
	def __init__(self, db, sale_id: int, parent=None):
		super().__init__(parent)
		self.db = db
		self.sale_id = sale_id
		self.setWindowTitle('Edit Sale')
		self.table = QtWidgets.QTableWidget(0, 5)
		self.table.setHorizontalHeaderLabels(['Product', 'Product ID', 'Qty', 'Unit Price', 'Discount'])
		self.table.horizontalHeader().setStretchLastSection(True)
		self.discount_total = QtWidgets.QDoubleSpinBox(); self.discount_total.setPrefix('Total Discount: '); self.discount_total.setMaximum(1_000_000)
		self.payment_type = QtWidgets.QComboBox(); self.payment_type.addItems(['Cash', 'Card', 'QR', 'Other'])
		self.paid_amount = QtWidgets.QDoubleSpinBox(); self.paid_amount.setPrefix('Paid: '); self.paid_amount.setMaximum(1_000_000)
		self.change_amount = QtWidgets.QDoubleSpinBox(); self.change_amount.setPrefix('Change: '); self.change_amount.setMaximum(1_000_000)
		btn_save = QtWidgets.QPushButton('Save Changes')
		btn_save.clicked.connect(self.save)

		layout = QtWidgets.QVBoxLayout(self)
		layout.addWidget(self.table)
		form = QtWidgets.QHBoxLayout()
		form.addWidget(self.discount_total)
		form.addWidget(self.payment_type)
		form.addWidget(self.paid_amount)
		form.addWidget(self.change_amount)
		layout.addLayout(form)
		layout.addWidget(btn_save)

		self.load()

	def load(self):
		conn = self.db.connection()
		row = conn.execute('SELECT discount_amount, payment_type, paid_amount, change_amount FROM sales WHERE id=?', (self.sale_id,)).fetchone()
		if row:
			self.discount_total.setValue(float(row['discount_amount']))
			idx = self.payment_type.findText(row['payment_type'])
			self.payment_type.setCurrentIndex(max(0, idx))
			self.paid_amount.setValue(float(row['paid_amount']))
			self.change_amount.setValue(float(row['change_amount']))
		items = conn.execute('SELECT si.*, p.name AS product_name FROM sale_items si JOIN products p ON p.id=si.product_id WHERE sale_id=? ORDER BY si.id', (self.sale_id,)).fetchall()
		self.table.setRowCount(0)
		for it in items:
			row_idx = self.table.rowCount(); self.table.insertRow(row_idx)
			self.table.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(it['product_name']))
			self.table.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(str(it['product_id'])))
			self.table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(str(it['quantity'])))
			self.table.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(f"{it['unit_price']:.2f}"))
			self.table.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(f"{it['discount']:.2f}"))

	def save(self):
		conn = self.db.connection()
		# collect new items
		items = []
		for r in range(self.table.rowCount()):
			pid = int(self.table.item(r, 1).text())
			qty = int(float(self.table.item(r, 2).text()))
			price = float(self.table.item(r, 3).text())
			disc = float(self.table.item(r, 4).text())
			if qty <= 0:
				continue
			line_total = (price * qty) - disc
			items.append({'product_id': pid, 'quantity': qty, 'unit_price': price, 'discount': disc, 'line_total': line_total})
		discount_amount = float(self.discount_total.value())
		payment_type = self.payment_type.currentText()
		paid_amount = float(self.paid_amount.value())
		change_amount = float(self.change_amount.value())
		# transaction: restock old, replace items, adjust stock, update sale header
		with conn:
			old_items = conn.execute('SELECT product_id, quantity FROM sale_items WHERE sale_id=?', (self.sale_id,)).fetchall()
			for r in old_items:
				conn.execute('UPDATE products SET stock_quantity = stock_quantity + ? WHERE id=?', (r['quantity'], r['product_id']))
			conn.execute('DELETE FROM sale_items WHERE sale_id=?', (self.sale_id,))
			for it in items:
				conn.execute('INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, discount, line_total) VALUES (?, ?, ?, ?, ?, ?)', (self.sale_id, it['product_id'], it['quantity'], it['unit_price'], it['discount'], it['line_total']))
				conn.execute('UPDATE products SET stock_quantity = stock_quantity - ? WHERE id=?', (it['quantity'], it['product_id']))
			total_amount = sum(i['line_total'] for i in items)
			conn.execute('UPDATE sales SET total_amount=?, discount_amount=?, payment_type=?, paid_amount=?, change_amount=? WHERE id=?', (total_amount, discount_amount, payment_type, paid_amount, change_amount, self.sale_id))
		self.accept()


class SalesDialog(QtWidgets.QDialog):
	def __init__(self, db, parent=None):
		super().__init__(parent)
		self.db = db
		self.setWindowTitle('Sales Management')
		self.table = QtWidgets.QTableWidget(0, 6)
		self.table.setHorizontalHeaderLabels(['ID', 'Invoice', 'Total', 'Discount', 'Payment', 'Date'])
		self.table.horizontalHeader().setStretchLastSection(True)

		btn_refresh = QtWidgets.QPushButton('Refresh')
		btn_edit = QtWidgets.QPushButton('View / Edit')
		btn_delete = QtWidgets.QPushButton('Delete Sale')
		btn_refresh.clicked.connect(self.refresh)
		btn_edit.clicked.connect(self.edit_sale)
		btn_delete.clicked.connect(self.delete_sale)

		layout = QtWidgets.QVBoxLayout(self)
		layout.addWidget(self.table)
		bar = QtWidgets.QHBoxLayout(); bar.addWidget(btn_refresh); bar.addWidget(btn_edit); bar.addWidget(btn_delete); bar.addStretch()
		layout.addLayout(bar)

		self.refresh()

	def refresh(self):
		rows = self.db.connection().execute('SELECT id, invoice_id, total_amount, discount_amount, payment_type, created_at FROM sales ORDER BY datetime(created_at) DESC LIMIT 200').fetchall()
		self.table.setRowCount(0)
		for r in rows:
			row = self.table.rowCount(); self.table.insertRow(row)
			self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(r['id'])))
			self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(r['invoice_id']))
			self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(f"{r['total_amount']:.2f}"))
			self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{r['discount_amount']:.2f}"))
			self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(r['payment_type']))
			self.table.setItem(row, 5, QtWidgets.QTableWidgetItem(r['created_at']))

	def current_sale_id(self):
		row = self.table.currentRow()
		if row < 0:
			return None
		return int(self.table.item(row, 0).text())

	def edit_sale(self):
		sid = self.current_sale_id()
		if not sid:
			return
		dlg = EditSaleDialog(self.db, sid, self)
		if dlg.exec_():
			self.refresh()

	def delete_sale(self):
		sid = self.current_sale_id()
		if not sid:
			return
		if QtWidgets.QMessageBox.question(self, 'Confirm', 'Delete this sale and restock items?') != QtWidgets.QMessageBox.Yes:
			return
		conn = self.db.connection()
		try:
			with conn:
				rows = conn.execute('SELECT product_id, quantity FROM sale_items WHERE sale_id=?', (sid,)).fetchall()
				for r in rows:
					conn.execute('UPDATE products SET stock_quantity = stock_quantity + ? WHERE id=?', (r['quantity'], r['product_id']))
				conn.execute('DELETE FROM sale_items WHERE sale_id=?', (sid,))
				conn.execute('DELETE FROM sales WHERE id=?', (sid,))
			self.refresh()
		except Exception as e:
			QtWidgets.QMessageBox.critical(self, 'Delete Failed', str(e))





