from PyQt5 import QtWidgets, QtCore, QtGui
from utils import db_helper


class VariantSelectorDialog(QtWidgets.QDialog):
	"""Dialog to select a product variant when a product has variants."""
	def __init__(self, db, product, parent=None):
		super().__init__(parent)
		self.db = db
		self.product = product
		self.selected_variant = None
		self.setWindowTitle(f"Select Variant - {product['name']}")
		self.setMinimumWidth(600)
		
		layout = QtWidgets.QVBoxLayout(self)
		
		# Info label
		info = QtWidgets.QLabel(f"Product: <b>{product['name']}</b> has multiple variants. Please select one:")
		info.setWordWrap(True)
		layout.addWidget(info)
		
		# Variants table
		self.table = QtWidgets.QTableWidget(0, 6)
		self.table.setHorizontalHeaderLabels(['Size', 'Color', 'SKU', 'Barcode', 'Price', 'Stock'])
		self.table.horizontalHeader().setStretchLastSection(True)
		self.table.setAlternatingRowColors(True)
		self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
		self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
		self.table.itemDoubleClicked.connect(self.accept_selection)
		self.table.currentItemChanged.connect(self.on_selection_changed)
		layout.addWidget(self.table)
		
		# Option to use base product (if no variants selected)
		self.use_base_product = QtWidgets.QCheckBox('Use base product (no variant)')
		self.use_base_product.setChecked(False)
		self.use_base_product.toggled.connect(self.on_base_toggled)
		layout.addWidget(self.use_base_product)
		
		# Buttons
		btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
		btns.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
		self.ok_button = btns.button(QtWidgets.QDialogButtonBox.Ok)
		btns.accepted.connect(self.accept)
		btns.rejected.connect(self.reject)
		layout.addWidget(btns)
		
		self.load_variants()
	
	def load_variants(self):
		"""Load variants for the product."""
		variants = self.db.list_variants(self.product['id'])
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
				f"{v.get('price') or self.product['price']:.2f}" if v.get('price') else f"{self.product['price']:.2f}",
				str(v.get('stock_quantity') or 0)
			]
			
			for col, text in enumerate(items):
				item = QtWidgets.QTableWidgetItem(text)
				if col == 4:  # Price column
					item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
				item.setForeground(QtGui.QBrush(text_color))
				item.setData(QtCore.Qt.UserRole, v['id'])
				self.table.setItem(row, col, item)
		
		if len(variants) == 0:
			# No variants, use base product
			self.use_base_product.setChecked(True)
			self.ok_button.setEnabled(True)
	
	def on_selection_changed(self, current, previous):
		"""Handle variant selection change."""
		if current:
			self.use_base_product.setChecked(False)
			row = current.row()
			variant_id = self.table.item(row, 0).data(QtCore.Qt.UserRole)
			variant = self.db.get_variant(variant_id)
			if variant:
				self.selected_variant = variant
				self.ok_button.setEnabled(True)
		else:
			self.ok_button.setEnabled(self.use_base_product.isChecked())
	
	def on_base_toggled(self, checked):
		"""Handle base product checkbox toggle."""
		if checked:
			self.table.clearSelection()
			self.selected_variant = None
			self.ok_button.setEnabled(True)
		else:
			self.ok_button.setEnabled(False)
	
	def accept_selection(self, item):
		"""Accept when variant is double-clicked."""
		if item:
			self.accept()
	
	def get_selection(self):
		"""Get the selected variant or None for base product."""
		if self.use_base_product.isChecked():
			return None
		return self.selected_variant

