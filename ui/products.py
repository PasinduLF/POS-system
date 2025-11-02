from PyQt5 import QtWidgets, QtCore, QtGui


class MasterDataDialog(QtWidgets.QDialog):
	def __init__(self, title: str, items: list, on_create, on_update, on_delete, parent=None):
		super().__init__(parent)
		self.setWindowTitle(title)
		self.on_create = on_create
		self.on_update = on_update
		self.on_delete = on_delete
		self.table = QtWidgets.QTableWidget(0, 2)
		self.table.setHorizontalHeaderLabels(['ID', 'Name'])
		self.table.horizontalHeader().setStretchLastSection(True)
		self.name = QtWidgets.QLineEdit()
		btn_add = QtWidgets.QPushButton('Add')
		btn_update = QtWidgets.QPushButton('Update')
		btn_delete = QtWidgets.QPushButton('Delete')
		btn_add.clicked.connect(self.add_item)
		btn_update.clicked.connect(self.update_item)
		btn_delete.clicked.connect(self.delete_item)

		layout = QtWidgets.QVBoxLayout(self)
		layout.addWidget(self.table)
		form = QtWidgets.QHBoxLayout(); form.addWidget(self.name); form.addWidget(btn_add); form.addWidget(btn_update); form.addWidget(btn_delete)
		layout.addLayout(form)
		self.load(items)

	def load(self, items: list):
		self.table.setRowCount(0)
		for it in items:
			row = self.table.rowCount(); self.table.insertRow(row)
			self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(it['id'])))
			self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(it['name']))

	def selected(self):
		row = self.table.currentRow()
		if row < 0:
			return None
		return int(self.table.item(row, 0).text()), self.table.item(row, 1).text()

	def add_item(self):
		name = self.name.text().strip()
		if not name:
			QtWidgets.QMessageBox.warning(self, 'Validation', 'Name is required')
			return
		try:
			self.on_create(name)
			self.accept()
		except Exception as e:
			QtWidgets.QMessageBox.critical(self, 'Add Failed', f'Cannot add: {e}')

	def update_item(self):
		sel = self.selected()
		if not sel:
			QtWidgets.QMessageBox.warning(self, 'Select', 'Select an item to update')
			return
		_id, _ = sel
		name = self.name.text().strip()
		if not name:
			QtWidgets.QMessageBox.warning(self, 'Validation', 'Name is required')
			return
		try:
			self.on_update(_id, name)
			self.accept()
		except Exception as e:
			QtWidgets.QMessageBox.critical(self, 'Update Failed', f'Cannot update: {e}')

	def delete_item(self):
		sel = self.selected()
		if not sel:
			return
		_id, name = sel
		if QtWidgets.QMessageBox.question(self, 'Confirm', f'Delete "{name}"?') != QtWidgets.QMessageBox.Yes:
			return
		try:
			self.on_delete(_id)
			self.accept()
		except Exception as e:
			QtWidgets.QMessageBox.critical(self, 'Delete Failed', f'Cannot delete: {e}')


class ProductDialog(QtWidgets.QDialog):
	def __init__(self, db, product=None, parent=None):
		super().__init__(parent)
		self.db = db
		self.product = product
		self.setWindowTitle('Product')

		self.name = QtWidgets.QLineEdit()
		self.brand = QtWidgets.QComboBox(); self.brand.addItem('— None —', None)
		for b in self.db.list_brands():
			self.brand.addItem(b['name'], b['id'])
		self.category = QtWidgets.QComboBox(); self.category.addItem('— None —', None)
		for c in self.db.list_categories():
			self.category.addItem(c['name'], c['id'])
		self.description = QtWidgets.QLineEdit()
		self.price = QtWidgets.QDoubleSpinBox(); self.price.setMaximum(1_000_000); self.price.setPrefix('Price: ')
		self.cost = QtWidgets.QDoubleSpinBox(); self.cost.setMaximum(1_000_000); self.cost.setPrefix('Cost: ')
		self.stock = QtWidgets.QSpinBox(); self.stock.setMaximum(1_000_000)
		self.barcode = QtWidgets.QLineEdit()
		self.low_stock = QtWidgets.QSpinBox(); self.low_stock.setMaximum(10_000)

		form = QtWidgets.QFormLayout()
		form.addRow('Name', self.name)
		form.addRow('Brand', self.brand)
		form.addRow('Category', self.category)
		form.addRow('Description', self.description)
		form.addRow(self.price)
		form.addRow(self.cost)
		form.addRow('Stock', self.stock)
		form.addRow('Barcode', self.barcode)
		form.addRow('Low stock threshold', self.low_stock)

		# Variants management
		self.variants_tab = None
		self.tabs = QtWidgets.QTabWidget()
		
		# Product details tab
		product_tab = QtWidgets.QWidget()
		product_layout = QtWidgets.QVBoxLayout(product_tab)
		product_layout.addLayout(form)
		
		self.tabs.addTab(product_tab, 'Product Details')
		
		# Variants tab (only for existing products)
		if product:
			self.variants_tab = VariantsTabWidget(self.db, product['id'])
			self.tabs.addTab(self.variants_tab, 'Variants')
		
		btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
		btns.accepted.connect(self.accept)
		btns.rejected.connect(self.reject)

		layout = QtWidgets.QVBoxLayout(self)
		layout.addWidget(self.tabs)
		layout.addWidget(btns)

		if product:
			self.name.setText(product['name'])
			# prefer brand_id if present; fallback to matching legacy brand text
			if product.get('brand_id'):
				idx = self.brand.findData(product['brand_id'])
				self.brand.setCurrentIndex(max(0, idx))
			elif product.get('brand'):
				idx = self.brand.findText(product['brand'])
				self.brand.setCurrentIndex(max(0, idx))
			cidx = self.category.findData(product['category_id'])
			self.category.setCurrentIndex(max(0, cidx))
			self.description.setText(product.get('description') or '')
			self.price.setValue(float(product['price']))
			self.cost.setValue(float(product['cost_price']))
			self.stock.setValue(int(product['stock_quantity']))
			self.barcode.setText(product.get('barcode') or '')
			self.low_stock.setValue(int(product.get('low_stock_threshold', 5)))

	def get_data(self):
		return {
			'name': self.name.text().strip(),
			'brand_id': self.brand.currentData(),
			'brand': None,  # we no longer capture legacy text here
			'category_id': self.category.currentData(),
			'description': self.description.text().strip(),
			'price': float(self.price.value()),
			'cost_price': float(self.cost.value()),
			'stock_quantity': int(self.stock.value()),
			'barcode': self.barcode.text().strip() or None,
			'low_stock_threshold': int(self.low_stock.value()),
		}


class VariantDialog(QtWidgets.QDialog):
	"""Dialog for adding/editing a product variant."""
	def __init__(self, db, product_id: int, variant=None, parent=None):
		super().__init__(parent)
		self.db = db
		self.product_id = product_id
		self.variant = variant
		self.setWindowTitle('Variant' if variant else 'Add Variant')
		self.setMinimumWidth(500)
		
		form = QtWidgets.QFormLayout()
		
		self.size = QtWidgets.QLineEdit()
		self.size.setPlaceholderText('e.g., S, M, L, 100ml')
		form.addRow('Size:', self.size)
		
		self.color = QtWidgets.QLineEdit()
		self.color.setPlaceholderText('e.g., Red, Blue, Black')
		form.addRow('Color:', self.color)
		
		self.sku = QtWidgets.QLineEdit()
		self.sku.setPlaceholderText('SKU code')
		form.addRow('SKU:', self.sku)
		
		self.barcode = QtWidgets.QLineEdit()
		self.barcode.setPlaceholderText('Variant barcode')
		form.addRow('Barcode:', self.barcode)
		
		self.price = QtWidgets.QDoubleSpinBox()
		self.price.setMaximum(1_000_000)
		self.price.setPrefix('Price: ')
		self.price.setValue(0.0)
		form.addRow(self.price)
		
		self.cost_price = QtWidgets.QDoubleSpinBox()
		self.cost_price.setMaximum(1_000_000)
		self.cost_price.setPrefix('Cost Price: ')
		self.cost_price.setValue(0.0)
		form.addRow(self.cost_price)
		
		self.stock = QtWidgets.QSpinBox()
		self.stock.setMaximum(1_000_000)
		self.stock.setValue(0)
		form.addRow('Stock Quantity:', self.stock)
		
		self.low_stock = QtWidgets.QSpinBox()
		self.low_stock.setMaximum(10_000)
		self.low_stock.setValue(5)
		form.addRow('Low Stock Threshold:', self.low_stock)
		
		if variant:
			self.size.setText(variant.get('size') or '')
			self.color.setText(variant.get('color') or '')
			self.sku.setText(variant.get('sku') or '')
			self.barcode.setText(variant.get('barcode') or '')
			self.price.setValue(float(variant.get('price') or 0))
			self.cost_price.setValue(float(variant.get('cost_price') or 0))
			self.stock.setValue(int(variant.get('stock_quantity') or 0))
			self.low_stock.setValue(int(variant.get('low_stock_threshold') or 5))
		
		btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
		btns.accepted.connect(self.accept)
		btns.rejected.connect(self.reject)
		
		layout = QtWidgets.QVBoxLayout(self)
		layout.addLayout(form)
		layout.addWidget(btns)
	
	def get_data(self):
		return {
			'size': self.size.text().strip() or None,
			'color': self.color.text().strip() or None,
			'sku': self.sku.text().strip() or None,
			'barcode': self.barcode.text().strip() or None,
			'price': float(self.price.value()) if self.price.value() > 0 else None,
			'cost_price': float(self.cost_price.value()),
			'stock_quantity': int(self.stock.value()),
			'low_stock_threshold': int(self.low_stock.value())
		}


class VariantsTabWidget(QtWidgets.QWidget):
	"""Widget for managing product variants."""
	def __init__(self, db, product_id: int, parent=None):
		super().__init__(parent)
		self.db = db
		self.product_id = product_id
		
		layout = QtWidgets.QVBoxLayout(self)
		
		# Header
		header = QtWidgets.QHBoxLayout()
		title = QtWidgets.QLabel('Product Variants')
		title.setStyleSheet('font-size: 12pt; font-weight: bold;')
		header.addWidget(title)
		header.addStretch()
		
		self.btn_add = QtWidgets.QPushButton('➕ Add Variant')
		self.btn_edit = QtWidgets.QPushButton('✏️ Edit')
		self.btn_delete = QtWidgets.QPushButton('🗑️ Delete')
		self.btn_refresh = QtWidgets.QPushButton('🔄 Refresh')
		
		self.btn_add.clicked.connect(self.add_variant)
		self.btn_edit.clicked.connect(self.edit_variant)
		self.btn_delete.clicked.connect(self.delete_variant)
		self.btn_refresh.clicked.connect(self.refresh)
		
		header.addWidget(self.btn_add)
		header.addWidget(self.btn_edit)
		header.addWidget(self.btn_delete)
		header.addWidget(self.btn_refresh)
		
		layout.addLayout(header)
		
		# Variants table
		self.table = QtWidgets.QTableWidget(0, 8)
		self.table.setHorizontalHeaderLabels(['Size', 'Color', 'SKU', 'Barcode', 'Price', 'Cost Price', 'Stock', 'Low Stock'])
		self.table.horizontalHeader().setStretchLastSection(True)
		self.table.setAlternatingRowColors(True)
		self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
		layout.addWidget(self.table)
		
		self.refresh()
	
	def refresh(self):
		"""Refresh the variants table."""
		variants = self.db.list_variants(self.product_id)
		self.table.setRowCount(0)
		
		theme = self.db.get_setting('theme', 'Light')
		is_dark = theme.lower() == 'dark'
		text_color = QtGui.QColor('#e0e0e0') if is_dark else QtGui.QColor('#333333')
		
		for v in variants:
			row = self.table.rowCount()
			self.table.insertRow(row)
			
			items = [
				v.get('size') or '',
				v.get('color') or '',
				v.get('sku') or '',
				v.get('barcode') or '',
				f"{v.get('price') or 0:.2f}" if v.get('price') else '',
				f"{v.get('cost_price') or 0:.2f}",
				str(v.get('stock_quantity') or 0),
				str(v.get('low_stock_threshold') or 5)
			]
			
			for col, text in enumerate(items):
				item = QtWidgets.QTableWidgetItem(text)
				if col in (5, 6, 7):  # Price, Cost Price, Stock, Low Stock columns
					item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
				item.setForeground(QtGui.QBrush(text_color))
				item.setData(QtCore.Qt.UserRole, v['id'])
				self.table.setItem(row, col, item)
	
	def current_variant_id(self):
		"""Get the ID of the currently selected variant."""
		row = self.table.currentRow()
		if row < 0:
			return None
		item = self.table.item(row, 0)
		if item:
			return item.data(QtCore.Qt.UserRole)
		return None
	
	def add_variant(self):
		"""Add a new variant."""
		dlg = VariantDialog(self.db, self.product_id, parent=self)
		if dlg.exec_() == QtWidgets.QDialog.Accepted:
			data = dlg.get_data()
			self.db.create_variant(self.product_id, **data)
			self.refresh()
	
	def edit_variant(self):
		"""Edit the selected variant."""
		variant_id = self.current_variant_id()
		if not variant_id:
			QtWidgets.QMessageBox.warning(self, 'Select Variant', 'Please select a variant to edit.')
			return
		variant = self.db.get_variant(variant_id)
		if not variant:
			return
		dlg = VariantDialog(self.db, self.product_id, variant, parent=self)
		if dlg.exec_() == QtWidgets.QDialog.Accepted:
			data = dlg.get_data()
			self.db.update_variant(variant_id, **data)
			self.refresh()
	
	def delete_variant(self):
		"""Delete the selected variant."""
		variant_id = self.current_variant_id()
		if not variant_id:
			QtWidgets.QMessageBox.warning(self, 'Select Variant', 'Please select a variant to delete.')
			return
		variant = self.db.get_variant(variant_id)
		if not variant:
			return
		
		# Build variant description
		variant_desc = []
		if variant.get('size'):
			variant_desc.append(f"Size: {variant['size']}")
		if variant.get('color'):
			variant_desc.append(f"Color: {variant['color']}")
		if not variant_desc:
			variant_desc.append('this variant')
		
		if QtWidgets.QMessageBox.question(
			self, 'Confirm Delete', 
			f'Delete variant ({", ".join(variant_desc)})?'
		) == QtWidgets.QMessageBox.Yes:
			self.db.delete_variant(variant_id)
			self.refresh()


class ProductsWidget(QtWidgets.QWidget):
	def __init__(self, db, parent=None):
		super().__init__(parent)
		self.db = db
		self.table = QtWidgets.QTableWidget(0, 8)
		self.table.setHorizontalHeaderLabels(['Name', 'Brand', 'Category', 'Price', 'Cost', 'Stock', 'Barcode', 'Low'])
		self.table.horizontalHeader().setStretchLastSection(True)

		# Filter dropdowns
		filter_layout = QtWidgets.QHBoxLayout()
		filter_layout.addWidget(QtWidgets.QLabel('Filter by:'))
		self.filter_brand = QtWidgets.QComboBox()
		self.filter_brand.addItem('All Brands', None)
		self.filter_brand.currentIndexChanged.connect(self.refresh)
		self.filter_category = QtWidgets.QComboBox()
		self.filter_category.addItem('All Categories', None)
		self.filter_category.currentIndexChanged.connect(self.refresh)
		filter_layout.addWidget(QtWidgets.QLabel('Brand:'))
		filter_layout.addWidget(self.filter_brand)
		filter_layout.addWidget(QtWidgets.QLabel('Category:'))
		filter_layout.addWidget(self.filter_category)
		filter_layout.addStretch()

		self.btn_add = QtWidgets.QPushButton('Add')
		self.btn_edit = QtWidgets.QPushButton('Edit')
		self.btn_delete = QtWidgets.QPushButton('Delete')
		self.btn_manage_brands = QtWidgets.QPushButton('Manage Brands')
		self.btn_manage_categories = QtWidgets.QPushButton('Manage Categories')
		self.btn_add.clicked.connect(self.add_product)
		self.btn_edit.clicked.connect(self.edit_product)
		self.btn_delete.clicked.connect(self.delete_product)
		self.btn_manage_brands.clicked.connect(self.manage_brands)
		self.btn_manage_categories.clicked.connect(self.manage_categories)

		layout = QtWidgets.QVBoxLayout(self)
		layout.addLayout(filter_layout)
		layout.addWidget(self.table)
		bar = QtWidgets.QHBoxLayout()
		bar.addWidget(self.btn_add)
		bar.addWidget(self.btn_edit)
		bar.addWidget(self.btn_delete)
		bar.addStretch()
		bar.addWidget(self.btn_manage_brands)
		bar.addWidget(self.btn_manage_categories)
		layout.addLayout(bar)

		self._load_filters()
		self.refresh()

	def _load_filters(self):
		# Reload filter dropdowns
		self.filter_brand.clear()
		self.filter_brand.addItem('All Brands', None)
		for b in self.db.list_brands():
			self.filter_brand.addItem(b['name'], b['id'])
		self.filter_category.clear()
		self.filter_category.addItem('All Categories', None)
		for c in self.db.list_categories():
			self.filter_category.addItem(c['name'], c['id'])

	def refresh(self):
		self.table.setRowCount(0)
		filter_brand_id = self.filter_brand.currentData()
		filter_category_id = self.filter_category.currentData()
		for p in self.db.list_products():
			# Apply filters
			if filter_brand_id is not None and p.get('brand_id') != filter_brand_id:
				continue
			if filter_category_id is not None and p.get('category_id') != filter_category_id:
				continue
			row = self.table.rowCount()
			self.table.insertRow(row)
			self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(p['name']))
			self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(p.get('brand_name') or p.get('brand') or ''))
			self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(p.get('category_name') or ''))
			self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{p['price']:.2f}"))
			self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(f"{p['cost_price']:.2f}"))
			self.table.setItem(row, 5, QtWidgets.QTableWidgetItem(str(p['stock_quantity'])))
			self.table.setItem(row, 6, QtWidgets.QTableWidgetItem(p.get('barcode') or ''))
			self.table.setItem(row, 7, QtWidgets.QTableWidgetItem(str(p.get('low_stock_threshold', 5))))

	def current_product(self):
		row = self.table.currentRow()
		if row < 0:
			return None
		name = self.table.item(row, 0).text()
		brand = self.table.item(row, 1).text()
		candidates = [p for p in self.db.list_products() if p['name'] == name and (p.get('brand_name') or p.get('brand') or '') == brand]
		return candidates[0] if candidates else None

	def add_product(self):
		dlg = ProductDialog(self.db, parent=self)
		if dlg.exec_() == QtWidgets.QDialog.Accepted:
			data = dlg.get_data()
			self.db.create_product(**data)
			self.refresh()

	def edit_product(self):
		p = self.current_product()
		if not p:
			return
		dlg = ProductDialog(self.db, product=p, parent=self)
		if dlg.exec_() == QtWidgets.QDialog.Accepted:
			data = dlg.get_data()
			self.db.update_product(p['id'], **data)
			self.refresh()

	def delete_product(self):
		p = self.current_product()
		if not p:
			return
		if QtWidgets.QMessageBox.question(self, 'Confirm', f"Delete {p['name']}?") == QtWidgets.QMessageBox.Yes:
			self.db.delete_product(p['id'])
			self.refresh()

	def manage_brands(self):
		items = self.db.list_brands()
		dlg = MasterDataDialog('Manage Brands', items, self.db.create_brand, self.db.update_brand, self.db.delete_brand, self)
		if dlg.exec_():
			self._load_filters()
			self.refresh()

	def manage_categories(self):
		items = self.db.list_categories()
		dlg = MasterDataDialog('Manage Categories', items, self.db.create_category, self.db.update_category, self.db.delete_category, self)
		if dlg.exec_():
			self._load_filters()
			self.refresh()

