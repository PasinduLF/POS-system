from PyQt5 import QtCore, QtWidgets
from utils.printer import format_receipt_lines, print_receipt_text, generate_invoice_pdf
import os


class POSWidget(QtWidgets.QWidget):
	def __init__(self, db, user, parent=None):
		super().__init__(parent)
		self.db = db
		self.user = user
		self.cart = []
		self.app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
		self.invoices_dir = os.path.join(self.app_dir, 'invoices')
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
		self.search.setPlaceholderText('Search name or scan barcode... (F2 focus)')
		try:
			self.search.setClearButtonEnabled(True)
		except Exception:
			pass
		self.search.returnPressed.connect(self.add_search_item)
		self.search.textChanged.connect(self.on_search_text_changed)

		self.table = QtWidgets.QTableWidget(0, 5)
		self.table.setHorizontalHeaderLabels(['Product', 'Qty', 'Price', 'Discount', 'Total'])
		self.table.horizontalHeader().setStretchLastSection(True)
		try:
			self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
		except Exception:
			pass
		self.table.itemDoubleClicked.connect(self.edit_cell)

		self.btn_remove = QtWidgets.QPushButton('Remove Selected (Del)')
		self.btn_remove.clicked.connect(self.remove_selected)

		self.discount_total = QtWidgets.QDoubleSpinBox()
		self.discount_total.setPrefix('Total Discount: ')
		self.discount_total.setMaximum(1_000_000)
		self.discount_total.valueChanged.connect(self.update_totals)

		self.payment_type = QtWidgets.QComboBox()
		self.payment_type.addItems(['Cash', 'Card', 'QR', 'Other'])
		# Set default payment method from settings
		default_payment = db.get_setting('default_payment_method', 'Cash')
		idx = self.payment_type.findText(default_payment)
		if idx >= 0:
			self.payment_type.setCurrentIndex(idx)
		self.paid_amount = QtWidgets.QDoubleSpinBox()
		self.paid_amount.setPrefix('Paid: ')
		self.paid_amount.setMaximum(1_000_000)
		self.checkout = QtWidgets.QPushButton('Checkout & Print (F9)')
		self.checkout.clicked.connect(self.handle_checkout)

		# Optional customer info
		self.customer_name = QtWidgets.QLineEdit(); self.customer_name.setPlaceholderText('Customer name (optional)')
		self.customer_phone = QtWidgets.QLineEdit(); self.customer_phone.setPlaceholderText('Customer phone (optional)')
		self._setup_customer_completers()

		self.total_label = QtWidgets.QLabel('Total: 0.00')
		self.subtotal_label = QtWidgets.QLabel('Subtotal: 0.00')
		self.change_label = QtWidgets.QLabel('Change: 0.00')

		# Quick pay buttons
		self.btn_exact = QtWidgets.QPushButton('Exact')
		self.btn_1000 = QtWidgets.QPushButton('1000')
		self.btn_500 = QtWidgets.QPushButton('500')
		self.btn_exact.clicked.connect(self.set_exact_pay)
		self.btn_1000.clicked.connect(lambda: self.bump_pay(1000))
		self.btn_500.clicked.connect(lambda: self.bump_pay(500))

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
		left.addWidget(self.discount_total)

		mid = QtWidgets.QVBoxLayout()
		mid.addWidget(self.subtotal_label)
		mid.addWidget(self.total_label)
		mid.addWidget(self.change_label)

		right = QtWidgets.QVBoxLayout()
		r1 = QtWidgets.QHBoxLayout(); r1.addWidget(self.payment_type); r1.addWidget(self.paid_amount)
		r2 = QtWidgets.QHBoxLayout(); r2.addWidget(self.btn_exact); r2.addWidget(self.btn_500); r2.addWidget(self.btn_1000)
		r3 = QtWidgets.QHBoxLayout(); r3.addWidget(self.customer_name); r3.addWidget(self.customer_phone)
		right.addLayout(r1)
		right.addLayout(r2)
		right.addLayout(r3)
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
		self._setup_customer_completers()

	def _setup_customer_completers(self):
		# Build autocomplete lists from customers table
		try:
			customers = self.db.list_customers()
		except Exception:
			customers = []
		names = [c.get('name') for c in customers if (c.get('name') or '').strip()]
		phones = [c.get('phone') for c in customers if (c.get('phone') or '').strip()]
		name_completer = QtWidgets.QCompleter(names)
		name_completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
		self.customer_name.setCompleter(name_completer)
		phone_completer = QtWidgets.QCompleter(phones)
		phone_completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
		self.customer_phone.setCompleter(phone_completer)

	def on_search_text_changed(self, text: str):
		q = (text or '').strip()
		if not q:
			self.load_product_list()
			return
		# Live search suggestions
		self.products_list.clear()
		results = self.db.search_products(q)
		for p in results[:200]:
			item = QtWidgets.QListWidgetItem(f"{p['name']}  ({p.get('brand_name') or p.get('brand') or ''})  Rs.{float(p['price']):.2f}")
			item.setData(QtCore.Qt.UserRole, p)
			self.products_list.addItem(item)

	def load_product_list(self):
		self.products_list.clear()
		cat_id = self.category_filter.currentData()
		products = self.db.list_products()
		for p in products:
			if cat_id is None or p.get('category_id') == cat_id:
				item = QtWidgets.QListWidgetItem(f"{p['name']}  ({p.get('brand_name') or p.get('brand') or ''})  Rs.{p['price']:.2f}")
				item.setData(QtCore.Qt.UserRole, p)
				self.products_list.addItem(item)

	def add_from_list(self, item):
		p = item.data(QtCore.Qt.UserRole)
		if p:
			self._add_product_to_cart(p, 1)

	def add_search_item(self):
		q = self.search.text().strip()
		if not q:
			return
		# Check for variant barcode first
		variant_info = self.db.get_variant_by_barcode(q)
		if variant_info:
			# This is a variant barcode
			product = {k: v for k, v in variant_info.items() if not k.startswith('variant_') and k != 'variant_id'}
			product['id'] = variant_info.get('id')
			variant = self.db.get_variant(variant_info['variant_id'])
			self.add_to_cart(product, 1, variant)
			self.search.clear()
			return
		
		# barcode exact first (product barcode)
		prod = self.db.get_product_by_barcode(q)
		if not prod:
			res = self.db.search_products(q)
			prod = res[0] if res else None
		if not prod:
			QtWidgets.QMessageBox.information(self, 'Not found', 'Product not found')
			return
		self._add_product_to_cart(prod, 1)
		self.search.clear()

	def _add_product_to_cart(self, product, quantity):
		"""Internal method to handle adding product (with variant selection if needed)."""
		variants = self.db.list_variants(product['id'])
		if variants:
			# Product has variants, show selector
			from ui.variant_selector import VariantSelectorDialog
			dlg = VariantSelectorDialog(self.db, product, self)
			if dlg.exec_() == QtWidgets.QDialog.Accepted:
				selected_variant = dlg.get_selection()
				self.add_to_cart(product, quantity, selected_variant)
		else:
			# No variants, use base product
			self.add_to_cart(product, quantity, None)

	def add_to_cart(self, product, quantity, variant=None):
		# Check if same product and variant combination exists
		for it in self.cart:
			if it['product_id'] == product['id'] and it.get('variant_id') == (variant['id'] if variant else None):
				it['quantity'] += quantity
				it['line_total'] = (it['unit_price'] * it['quantity']) - it.get('discount', 0)
				self.refresh_table()
				return
		
		# Determine price - use variant price if available, otherwise product price
		if variant and variant.get('price'):
			price = float(variant['price'])
		else:
			price = float(product['price'])
		
		# Build display name with variant info
		name = product['name']
		variant_info = []
		if variant:
			if variant.get('size'):
				variant_info.append(f"Size: {variant['size']}")
			if variant.get('color'):
				variant_info.append(f"Color: {variant['color']}")
			if variant_info:
				name += f" ({', '.join(variant_info)})"
		
		item = {
			'product_id': product['id'],
			'variant_id': variant['id'] if variant else None,
			'name': name,
			'quantity': quantity,
			'unit_price': price,
			'discount': 0.0,
			'line_total': price * quantity,
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
			self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(f"{it['unit_price']:.2f}"))
			self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{it.get('discount', 0):.2f}"))
			self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(f"{it['line_total']:.2f}"))
		self.update_totals()

	def update_totals(self):
		subtotal = sum((it['unit_price'] * it['quantity']) - it.get('discount', 0.0) for it in self.cart)
		discount_total = self.discount_total.value()
		total = max(0.0, subtotal - discount_total)
		paid = self.paid_amount.value()
		change = max(0.0, paid - total)
		self.subtotal_label.setText(f"Subtotal: {subtotal:.2f}")
		self.total_label.setText(f"Total: {total:.2f}")
		self.change_label.setText(f"Change: {change:.2f}")

	def remove_selected(self):
		row = self.table.currentRow()
		if row >= 0:
			self.cart.pop(row)
			self.refresh_table()

	def edit_cell(self, item):
		row = item.row(); col = item.column()
		if row < 0:
			return
		if col == 1:  # Qty
			qty, ok = QtWidgets.QInputDialog.getInt(self, 'Quantity', 'Enter quantity:', value=int(self.cart[row]['quantity']), min=1, max=100000)
			if ok:
				self.cart[row]['quantity'] = qty
				self.cart[row]['line_total'] = (self.cart[row]['unit_price'] * qty) - self.cart[row].get('discount', 0.0)
				self.refresh_table()
		elif col == 3:  # Discount per line
			disc, ok = QtWidgets.QInputDialog.getDouble(self, 'Discount', 'Enter discount amount:', value=float(self.cart[row].get('discount', 0.0)), min=0.0, max=1_000_000, decimals=2)
			if ok:
				self.cart[row]['discount'] = disc
				self.cart[row]['line_total'] = (self.cart[row]['unit_price'] * self.cart[row]['quantity']) - disc
				self.refresh_table()

	def set_exact_pay(self):
		# set paid to exact total
		subtotal = sum((it['unit_price'] * it['quantity']) - it.get('discount', 0.0) for it in self.cart)
		total = max(0.0, subtotal - self.discount_total.value())
		self.paid_amount.setValue(total)
		self.update_totals()

	def bump_pay(self, amount):
		self.paid_amount.setValue(self.paid_amount.value() + amount)
		self.update_totals()

	def handle_checkout(self):
		if not self.cart:
			QtWidgets.QMessageBox.information(self, 'Empty', 'Cart is empty')
			return
		
		# Check if customer is required
		require_customer = self.db.get_setting('require_customer', 'false').lower() == 'true'
		if require_customer:
			if not self.customer_name.text().strip() and not self.customer_phone.text().strip():
				QtWidgets.QMessageBox.warning(self, 'Customer Required', 'Customer name or phone is required for sales.')
				return
		
		subtotal = sum((it['unit_price'] * it['quantity']) - it.get('discount', 0.0) for it in self.cart)
		discount_total = self.discount_total.value()
		
		# Apply tax if enabled
		tax_enabled = self.db.get_setting('tax_enabled', 'false').lower() == 'true'
		tax_percentage = float(self.db.get_setting('tax_percentage', '0.0'))
		tax_method = self.db.get_setting('tax_method', 'Inclusive')
		
		if tax_enabled and tax_percentage > 0:
			if tax_method == 'Inclusive':
				# Tax is included in prices, calculate from subtotal
				tax_amount = subtotal * (tax_percentage / (100 + tax_percentage))
				total = subtotal - discount_total
			else:
				# Tax is exclusive, add to subtotal
				tax_amount = (subtotal - discount_total) * (tax_percentage / 100)
				total = subtotal - discount_total + tax_amount
		else:
			tax_amount = 0.0
			total = max(0.0, subtotal - discount_total)
		
		# Apply cash rounding
		cash_rounding = self.db.get_setting('cash_rounding', 'No Rounding')
		if cash_rounding != 'No Rounding':
			rounding_map = {'Round to 0.05': 0.05, 'Round to 0.50': 0.50, 'Round to 1.00': 1.00}
			round_to = rounding_map.get(cash_rounding, 0.01)
			import math
			total = round(math.ceil(total / round_to) * round_to, 2)
		
		paid = self.paid_amount.value()
		allow_partial = self.db.get_setting('allow_partial_payment', 'false').lower() == 'true'
		
		if not allow_partial and paid < total:
			QtWidgets.QMessageBox.warning(self, 'Insufficient', 'Paid amount is less than total')
			return
		change = max(0.0, paid - total)

		items_payload = []
		for it in self.cart:
			items_payload.append({
				'product_id': it['product_id'],
				'variant_id': it.get('variant_id'),
				'quantity': it['quantity'],
				'unit_price': it['unit_price'],
				'discount': it.get('discount', 0.0),
				'line_total': (it['unit_price'] * it['quantity']) - it.get('discount', 0.0)
			})

		# Upsert customer if provided or auto-create is enabled
		auto_create_customer = self.db.get_setting('auto_create_customer', 'true').lower() == 'true'
		customer_id = None
		if auto_create_customer or self.customer_name.text().strip() or self.customer_phone.text().strip():
			customer_id = self.db.upsert_customer(self.customer_name.text(), self.customer_phone.text())
		
		invoice_id = self.db.create_sale(self.user['id'], items_payload, discount_total, self.payment_type.currentText(), paid, change, customer_id)

		# Get shop settings from database
		shop_name = self.db.get_setting('shop_name', 'Beauty P&C')
		shop_phone = self.db.get_setting('shop_phone', '0785993262')
		shop_email = self.db.get_setting('shop_email', 'beautypandc@gmail.com')
		shop_address = self.db.get_setting('shop_address', '')
		business_reg = self.db.get_setting('business_reg', '')
		currency_symbol = self.db.get_setting('currency_symbol', 'Rs.')
		receipt_footer = self.db.get_setting('receipt_footer', 'Thank you!')
		show_address = self.db.get_setting('show_address_on_receipt', 'false').lower() == 'true'
		show_customer = self.db.get_setting('show_customer_on_receipt', 'Always')
		show_tax = self.db.get_setting('show_tax_on_receipt', 'false').lower() == 'true'

		# Prepare customer dict based on settings
		customer_dict = None
		if show_customer == 'Always' or (show_customer == 'Optional' and (self.customer_name.text().strip() or self.customer_phone.text().strip())):
			customer_dict = {'name': self.customer_name.text().strip(), 'phone': self.customer_phone.text().strip()}

		receipt_totals = {
			'subtotal': subtotal,
			'discount': discount_total,
			'total': total,
			'paid': paid,
			'change': change,
		}
		
		if tax_enabled and show_tax:
			receipt_totals['tax'] = tax_amount

		receipt_text = format_receipt_lines(
			shop_name, invoice_id, self.cart, receipt_totals,
			phone=shop_phone, email=shop_email, address=shop_address if show_address else '',
			business_reg=business_reg, currency_symbol=currency_symbol, receipt_footer=receipt_footer,
			customer=customer_dict
		)
		
		# Auto-print receipt if enabled
		auto_print = self.db.get_setting('auto_print_receipt', 'false').lower() == 'true'
		if auto_print:
			print_receipt_text(receipt_text)
		else:
			# Always print for now (can add option to show preview)
			print_receipt_text(receipt_text)

		# Auto-generate PDF if enabled
		auto_pdf = self.db.get_setting('auto_generate_pdf', 'false').lower() == 'true'
		if auto_pdf:
			try:
				pdf_path = generate_invoice_pdf(
					self.invoices_dir, shop_name, invoice_id, self.cart, receipt_totals,
					phone=shop_phone, email=shop_email, address=shop_address if show_address else '',
					business_reg=business_reg, currency_symbol=currency_symbol,
					customer=customer_dict
				)
				if not auto_print:  # Only show message if not auto-printing
					QtWidgets.QMessageBox.information(self, 'Invoice Saved', f'Invoice PDF saved to:\n{pdf_path}')
			except Exception as e:
				QtWidgets.QMessageBox.warning(self, 'PDF Error', f'Failed to generate PDF: {e}')

		self.cart.clear()
		self.refresh_table()
		self.discount_total.setValue(0)
		self.paid_amount.setValue(0)
		self.customer_name.clear()
		self.customer_phone.clear()
		# Refresh completers to include newly saved customer
		self._setup_customer_completers()
		QtWidgets.QMessageBox.information(self, 'Success', f'Sale saved. Invoice {invoice_id}')

