from PyQt5 import QtCore, QtWidgets
from utils.printer import format_receipt_lines, print_receipt_text
import os


class PurchaseWidget(QtWidgets.QWidget):
	def __init__(self, db, user, parent=None):
		super().__init__(parent)
		self.db = db
		self.user = user
		self.cart = []
		self.app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
		
		# Left panel: category filter + products list
		self.category_filter = QtWidgets.QComboBox()
		self.category_filter.addItem('All Categories', None)
		for c in self.db.list_categories():
			self.category_filter.addItem(c['name'], c['id'])
		self.category_filter.currentIndexChanged.connect(self.load_product_list)
		self.products_list = QtWidgets.QListWidget()
		self.products_list.itemDoubleClicked.connect(self.add_from_list)

		# Search and cart
		self.search = QtWidgets.QLineEdit()
		self.search.setPlaceholderText('Search product or scan barcode... (F2 focus)')
		try:
			self.search.setClearButtonEnabled(True)
		except Exception:
			pass
		self.search.returnPressed.connect(self.add_search_item)
		self.search.textChanged.connect(self.on_search_text_changed)

		self.table = QtWidgets.QTableWidget(0, 4)
		self.table.setHorizontalHeaderLabels(['Product', 'Qty', 'Unit Cost', 'Total'])
		self.table.horizontalHeader().setStretchLastSection(True)
		try:
			self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
		except Exception:
			pass
		self.table.itemDoubleClicked.connect(self.edit_cell)

		self.btn_remove = QtWidgets.QPushButton('Remove Selected (Del)')
		self.btn_remove.clicked.connect(self.remove_selected)

		self.supplier_name = QtWidgets.QLineEdit()
		self.supplier_name.setPlaceholderText('Supplier name (optional)')

		self.payment_type = QtWidgets.QComboBox()
		self.payment_type.addItems(['Cash', 'Card', 'Cheque', 'Credit', 'Other'])
		self.paid_amount = QtWidgets.QDoubleSpinBox()
		self.paid_amount.setPrefix('Paid: ')
		self.paid_amount.setMaximum(1_000_000)
		self.paid_amount.valueChanged.connect(self.update_totals)

		self.total_label = QtWidgets.QLabel('Total: 0.00')
		self.balance_label = QtWidgets.QLabel('Balance: 0.00')

		# Quick pay buttons
		self.btn_exact = QtWidgets.QPushButton('Exact')
		self.btn_1000 = QtWidgets.QPushButton('1000')
		self.btn_500 = QtWidgets.QPushButton('500')
		self.btn_exact.clicked.connect(self.set_exact_pay)
		self.btn_1000.clicked.connect(lambda: self.bump_pay(1000))
		self.btn_500.clicked.connect(lambda: self.bump_pay(500))

		self.checkout = QtWidgets.QPushButton('Save Purchase (F9)')
		self.checkout.clicked.connect(self.handle_checkout)

		# Layouts
		root = QtWidgets.QHBoxLayout(self)
		left_panel = QtWidgets.QVBoxLayout()
		left_panel.addWidget(self.category_filter)
		left_panel.addWidget(self.products_list)

		main_panel = QtWidgets.QVBoxLayout()
		main_panel.addWidget(self.search)
		main_panel.addWidget(self.table)

		bottom = QtWidgets.QHBoxLayout()
		left = QtWidgets.QVBoxLayout()
		left.addWidget(self.btn_remove)
		left.addWidget(self.supplier_name)

		mid = QtWidgets.QVBoxLayout()
		mid.addWidget(self.total_label)
		mid.addWidget(self.balance_label)

		right = QtWidgets.QVBoxLayout()
		r1 = QtWidgets.QHBoxLayout()
		r1.addWidget(self.payment_type)
		r1.addWidget(self.paid_amount)
		r2 = QtWidgets.QHBoxLayout()
		r2.addWidget(self.btn_exact)
		r2.addWidget(self.btn_500)
		r2.addWidget(self.btn_1000)
		right.addLayout(r1)
		right.addLayout(r2)
		right.addWidget(self.checkout)

		bottom.addLayout(left)
		bottom.addLayout(mid)
		bottom.addLayout(right)
		main_panel.addLayout(bottom)

		root.addLayout(left_panel, 1)
		root.addLayout(main_panel, 2)

		# Hotkeys
		self.shortcut_search = QtWidgets.QShortcut(QtCore.Qt.Key_F2, self)
		self.shortcut_search.activated.connect(lambda: self.search.setFocus())
		self.shortcut_checkout = QtWidgets.QShortcut(QtCore.Qt.Key_F9, self)
		self.shortcut_checkout.activated.connect(self.handle_checkout)
		self.shortcut_delete = QtWidgets.QShortcut(QtCore.Qt.Key_Delete, self)
		self.shortcut_delete.activated.connect(self.remove_selected)
		self.shortcut_clear = QtWidgets.QShortcut(QtCore.Qt.Key_Escape, self)
		self.shortcut_clear.activated.connect(lambda: self.search.clear())

		self.load_product_list()

	def refresh_all(self):
		# Reload products and refresh cart/totals
		self.load_product_list()
		self.refresh_table()
		self.update_totals()

	def on_search_text_changed(self, text: str):
		q = (text or '').strip()
		if not q:
			self.load_product_list()
			return
		# Live search suggestions
		self.products_list.clear()
		results = self.db.search_products(q)
		for p in results[:200]:
			item = QtWidgets.QListWidgetItem(f"{p['name']}  ({p.get('brand_name') or p.get('brand') or ''})  Cost: Rs.{float(p.get('cost_price', 0)):.2f}  Stock: {p.get('stock_quantity', 0)}")
			item.setData(QtCore.Qt.UserRole, p)
			self.products_list.addItem(item)

	def load_product_list(self):
		self.products_list.clear()
		cat_id = self.category_filter.currentData()
		products = self.db.list_products()
		for p in products:
			if cat_id is None or p.get('category_id') == cat_id:
				item = QtWidgets.QListWidgetItem(f"{p['name']}  ({p.get('brand_name') or p.get('brand') or ''})  Cost: Rs.{p.get('cost_price', 0):.2f}  Stock: {p.get('stock_quantity', 0)}")
				item.setData(QtCore.Qt.UserRole, p)
				self.products_list.addItem(item)

	def add_from_list(self, item):
		p = item.data(QtCore.Qt.UserRole)
		if p:
			self.add_to_cart(p, 1)

	def add_search_item(self):
		q = self.search.text().strip()
		if not q:
			return
		# barcode exact first
		prod = self.db.get_product_by_barcode(q)
		if not prod:
			res = self.db.search_products(q)
			prod = res[0] if res else None
		if not prod:
			QtWidgets.QMessageBox.information(self, 'Not found', 'Product not found')
			return
		self.add_to_cart(prod, 1)
		self.search.clear()

	def add_to_cart(self, product, quantity):
		for it in self.cart:
			if it['product_id'] == product['id']:
				it['quantity'] += quantity
				it['line_total'] = it['unit_cost'] * it['quantity']
				self.refresh_table()
				return
		# Use cost_price as default, or prompt for cost if not set
		cost = float(product.get('cost_price', 0))
		if cost == 0:
			# Prompt for cost price if not set
			cost, ok = QtWidgets.QInputDialog.getDouble(
				self, 'Unit Cost', 
				f"Enter unit cost for {product['name']}:", 
				value=0.0, min=0.0, max=1_000_000, decimals=2
			)
			if not ok:
				return
		item = {
			'product_id': product['id'],
			'name': product['name'],
			'quantity': quantity,
			'unit_cost': cost,
			'line_total': cost * quantity,
		}
		self.cart.append(item)
		self.refresh_table()

	def refresh_table(self):
		self.table.setRowCount(0)
		for it in self.cart:
			row = self.table.rowCount()
			self.table.insertRow(row)
			self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(it['name']))
			self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(it['quantity'])))
			self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(f"{it['unit_cost']:.2f}"))
			self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{it['line_total']:.2f}"))
		self.update_totals()

	def update_totals(self):
		total = sum(it['line_total'] for it in self.cart)
		paid = self.paid_amount.value()
		balance = max(0.0, total - paid)  # Amount still owed
		self.total_label.setText(f"Total: {total:.2f}")
		self.balance_label.setText(f"Balance: {balance:.2f}")

	def remove_selected(self):
		row = self.table.currentRow()
		if row >= 0:
			self.cart.pop(row)
			self.refresh_table()

	def edit_cell(self, item):
		row = item.row()
		col = item.column()
		if row < 0:
			return
		if col == 1:  # Qty
			qty, ok = QtWidgets.QInputDialog.getInt(
				self, 'Quantity', 'Enter quantity:', 
				value=int(self.cart[row]['quantity']), min=1, max=100000
			)
			if ok:
				self.cart[row]['quantity'] = qty
				self.cart[row]['line_total'] = self.cart[row]['unit_cost'] * qty
				self.refresh_table()
		elif col == 2:  # Unit Cost
			cost, ok = QtWidgets.QInputDialog.getDouble(
				self, 'Unit Cost', 'Enter unit cost:', 
				value=float(self.cart[row]['unit_cost']), min=0.0, max=1_000_000, decimals=2
			)
			if ok:
				self.cart[row]['unit_cost'] = cost
				self.cart[row]['line_total'] = cost * self.cart[row]['quantity']
				self.refresh_table()

	def set_exact_pay(self):
		# set paid to exact total
		total = sum(it['line_total'] for it in self.cart)
		self.paid_amount.setValue(total)
		self.update_totals()

	def bump_pay(self, amount):
		self.paid_amount.setValue(self.paid_amount.value() + amount)
		self.update_totals()

	def handle_checkout(self):
		if not self.cart:
			QtWidgets.QMessageBox.information(self, 'Empty', 'Cart is empty')
			return
		total = sum(it['line_total'] for it in self.cart)
		paid = self.paid_amount.value()
		if paid < 0:
			QtWidgets.QMessageBox.warning(self, 'Invalid', 'Paid amount cannot be negative')
			return

		items_payload = []
		for it in self.cart:
			items_payload.append({
				'product_id': it['product_id'],
				'variant_id': it.get('variant_id'),
				'quantity': it['quantity'],
				'unit_cost': it['unit_cost'],
				'line_total': it['line_total']
			})

		supplier_name = self.supplier_name.text().strip() or None
		bill_id = self.db.create_purchase(
			self.user['id'], 
			items_payload, 
			supplier_name, 
			self.payment_type.currentText(), 
			paid
		)

		# Generate receipt text
		receipt_lines = []
		receipt_lines.append('Beauty P&C - Purchase Bill')
		receipt_lines.append(f'Bill ID: {bill_id}')
		receipt_lines.append('-' * 40)
		if supplier_name:
			receipt_lines.append(f'Supplier: {supplier_name}')
			receipt_lines.append('-' * 40)
		for it in self.cart:
			name = it['name'][:20]
			qty = it['quantity']
			cost = it['unit_cost']
			line_total = it['line_total']
			receipt_lines.append(f"{name:<20} {qty:>3} x {cost:>8.2f}")
			receipt_lines.append(f"{'':<20} {'':>3}   {line_total:>8.2f}")
		receipt_lines.append('-' * 40)
		receipt_lines.append(f"Total:    {total:>8.2f}")
		receipt_lines.append(f"Paid:     {paid:>8.2f}")
		if paid < total:
			receipt_lines.append(f"Balance:  {total - paid:>8.2f}")
		receipt_lines.append('Thank you!')
		receipt_text = '\n'.join(receipt_lines)
		
		# Print receipt
		print_receipt_text(receipt_text)

		# Clear cart and reset
		self.cart.clear()
		self.refresh_table()
		self.paid_amount.setValue(0)
		self.supplier_name.clear()
		QtWidgets.QMessageBox.information(self, 'Success', f'Purchase saved. Bill ID: {bill_id}\nStock updated automatically.')


