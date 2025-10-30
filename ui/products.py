from PyQt5 import QtWidgets


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

		btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
		btns.accepted.connect(self.accept)
		btns.rejected.connect(self.reject)

		layout = QtWidgets.QVBoxLayout(self)
		layout.addLayout(form)
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


class ProductsWidget(QtWidgets.QWidget):
	def __init__(self, db, parent=None):
		super().__init__(parent)
		self.db = db
		self.table = QtWidgets.QTableWidget(0, 8)
		self.table.setHorizontalHeaderLabels(['Name', 'Brand', 'Category', 'Price', 'Cost', 'Stock', 'Barcode', 'Low'])
		self.table.horizontalHeader().setStretchLastSection(True)

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
		layout.addWidget(self.table)
		bar = QtWidgets.QHBoxLayout()
		bar.addWidget(self.btn_add)
		bar.addWidget(self.btn_edit)
		bar.addWidget(self.btn_delete)
		bar.addStretch()
		bar.addWidget(self.btn_manage_brands)
		bar.addWidget(self.btn_manage_categories)
		layout.addLayout(bar)

		self.refresh()

	def refresh(self):
		self.table.setRowCount(0)
		for p in self.db.list_products():
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
			self.refresh()

	def manage_categories(self):
		items = self.db.list_categories()
		dlg = MasterDataDialog('Manage Categories', items, self.db.create_category, self.db.update_category, self.db.delete_category, self)
		if dlg.exec_():
			self.refresh()

