from PyQt5 import QtWidgets


class SettingsDialog(QtWidgets.QDialog):
	def __init__(self, db, parent=None):
		super().__init__(parent)
		self.db = db
		self.setWindowTitle('Settings')
		self.resize(650, 650)
		
		# Create tabs for better organization
		tabs = QtWidgets.QTabWidget()
		
		# Tab 1: Shop Information
		shop_tab = QtWidgets.QWidget()
		shop_layout = QtWidgets.QFormLayout()
		
		self.shop_name = QtWidgets.QLineEdit()
		self.shop_name.setPlaceholderText('Shop/Business Name')
		self.shop_phone = QtWidgets.QLineEdit()
		self.shop_phone.setPlaceholderText('Phone Number')
		self.shop_email = QtWidgets.QLineEdit()
		self.shop_email.setPlaceholderText('Email Address')
		self.shop_address = QtWidgets.QPlainTextEdit()
		self.shop_address.setMaximumHeight(80)
		self.shop_address.setPlaceholderText('Address (optional)')
		self.business_reg = QtWidgets.QLineEdit()
		self.business_reg.setPlaceholderText('Business Registration Number / Tax ID')
		self.business_license = QtWidgets.QLineEdit()
		self.business_license.setPlaceholderText('Business License Number (optional)')
		
		shop_layout.addRow('Shop Name:', self.shop_name)
		shop_layout.addRow('Phone:', self.shop_phone)
		shop_layout.addRow('Email:', self.shop_email)
		shop_layout.addRow('Address:', self.shop_address)
		shop_layout.addRow('Registration/Tax ID:', self.business_reg)
		shop_layout.addRow('License Number:', self.business_license)
		shop_tab.setLayout(shop_layout)
		tabs.addTab(shop_tab, 'Shop Information')
		
		# Tab 2: Receipt & Invoice Settings
		receipt_tab = QtWidgets.QWidget()
		receipt_layout = QtWidgets.QFormLayout()
		
		self.receipt_footer = QtWidgets.QPlainTextEdit()
		self.receipt_footer.setMaximumHeight(60)
		self.receipt_footer.setPlaceholderText('Thank you!')
		self.currency_symbol = QtWidgets.QLineEdit()
		self.currency_symbol.setPlaceholderText('Rs.')
		self.show_address_on_receipt = QtWidgets.QCheckBox()
		self.show_customer_on_receipt = QtWidgets.QComboBox()
		self.show_customer_on_receipt.addItems(['Always', 'Optional', 'Never'])
		self.invoice_prefix = QtWidgets.QLineEdit()
		self.invoice_prefix.setPlaceholderText('INV')
		self.bill_prefix = QtWidgets.QLineEdit()
		self.bill_prefix.setPlaceholderText('BILL')
		
		receipt_layout.addRow('Receipt Footer Message:', self.receipt_footer)
		receipt_layout.addRow('Currency Symbol:', self.currency_symbol)
		receipt_layout.addRow('Show Address on Receipt:', self.show_address_on_receipt)
		receipt_layout.addRow('Show Customer Details:', self.show_customer_on_receipt)
		receipt_layout.addRow('Invoice Number Prefix:', self.invoice_prefix)
		receipt_layout.addRow('Bill Number Prefix:', self.bill_prefix)
		receipt_tab.setLayout(receipt_layout)
		tabs.addTab(receipt_tab, 'Receipt & Invoice')
		
		# Tab 3: Tax & Payment Settings
		tax_tab = QtWidgets.QWidget()
		tax_layout = QtWidgets.QFormLayout()
		
		self.tax_enabled = QtWidgets.QCheckBox()
		self.tax_percentage = QtWidgets.QDoubleSpinBox()
		self.tax_percentage.setMinimum(0.0)
		self.tax_percentage.setMaximum(100.0)
		self.tax_percentage.setSuffix('%')
		self.tax_method = QtWidgets.QComboBox()
		self.tax_method.addItems(['Inclusive', 'Exclusive'])
		self.show_tax_on_receipt = QtWidgets.QCheckBox()
		
		self.default_payment_method = QtWidgets.QComboBox()
		self.default_payment_method.addItems(['Cash', 'Card', 'QR', 'Other'])
		self.cash_rounding = QtWidgets.QComboBox()
		self.cash_rounding.addItems(['No Rounding', 'Round to 0.05', 'Round to 0.50', 'Round to 1.00'])
		self.allow_partial_payment = QtWidgets.QCheckBox()
		
		tax_layout.addRow('Enable Tax/VAT:', self.tax_enabled)
		tax_layout.addRow('Tax/VAT Percentage:', self.tax_percentage)
		tax_layout.addRow('Tax Calculation Method:', self.tax_method)
		tax_layout.addRow('Show Tax on Receipt:', self.show_tax_on_receipt)
		# Spacer
		spacer_label = QtWidgets.QLabel('')
		tax_layout.addRow('', spacer_label)
		tax_layout.addRow('Default Payment Method:', self.default_payment_method)
		tax_layout.addRow('Cash Rounding:', self.cash_rounding)
		tax_layout.addRow('Allow Partial Payment:', self.allow_partial_payment)
		tax_tab.setLayout(tax_layout)
		tabs.addTab(tax_tab, 'Tax & Payment')
		
		# Tab 4: Stock & Product Settings
		stock_tab = QtWidgets.QWidget()
		stock_layout = QtWidgets.QFormLayout()
		
		self.default_low_stock = QtWidgets.QSpinBox()
		self.default_low_stock.setMinimum(1)
		self.default_low_stock.setMaximum(10000)
		self.default_low_stock.setPrefix('Threshold: ')
		self.default_stock_qty = QtWidgets.QSpinBox()
		self.default_stock_qty.setMinimum(0)
		self.default_stock_qty.setMaximum(100000)
		self.allow_negative_stock = QtWidgets.QCheckBox()
		self.auto_update_cost_price = QtWidgets.QCheckBox()
		
		stock_layout.addRow('Default Low Stock Threshold:', self.default_low_stock)
		stock_layout.addRow('Default Stock Quantity:', self.default_stock_qty)
		stock_layout.addRow('Allow Negative Stock:', self.allow_negative_stock)
		stock_layout.addRow('Auto-update Cost Price on Purchase:', self.auto_update_cost_price)
		stock_tab.setLayout(stock_layout)
		tabs.addTab(stock_tab, 'Stock & Products')
		
		# Tab 5: Automation Settings
		auto_tab = QtWidgets.QWidget()
		auto_layout = QtWidgets.QFormLayout()
		
		self.auto_print_receipt = QtWidgets.QCheckBox()
		self.auto_generate_pdf = QtWidgets.QCheckBox()
		self.auto_create_customer = QtWidgets.QCheckBox()
		self.require_customer = QtWidgets.QCheckBox()
		
		auto_layout.addRow('Auto-print Receipts:', self.auto_print_receipt)
		auto_layout.addRow('Auto-generate PDF Invoices:', self.auto_generate_pdf)
		auto_layout.addRow('Auto-create Customer on Sale:', self.auto_create_customer)
		auto_layout.addRow('Require Customer for Sales:', self.require_customer)
		auto_tab.setLayout(auto_layout)
		tabs.addTab(auto_tab, 'Automation')
		
		# Tab 6: Display & Format Settings
		display_tab = QtWidgets.QWidget()
		display_layout = QtWidgets.QFormLayout()
		
		self.theme = QtWidgets.QComboBox()
		self.theme.addItems(['Light', 'Dark'])
		self.date_format = QtWidgets.QComboBox()
		self.date_format.addItems(['YYYY-MM-DD', 'DD/MM/YYYY', 'DD-MM-YYYY', 'MM/DD/YYYY'])
		self.time_format = QtWidgets.QComboBox()
		self.time_format.addItems(['24-hour', '12-hour (AM/PM)'])
		self.decimal_places = QtWidgets.QSpinBox()
		self.decimal_places.setMinimum(0)
		self.decimal_places.setMaximum(4)
		self.currency_position = QtWidgets.QComboBox()
		self.currency_position.addItems(['Before Amount', 'After Amount'])
		
		display_layout.addRow('Theme:', self.theme)
		display_layout.addRow('Date Format:', self.date_format)
		display_layout.addRow('Time Format:', self.time_format)
		display_layout.addRow('Decimal Places:', self.decimal_places)
		display_layout.addRow('Currency Position:', self.currency_position)
		display_tab.setLayout(display_layout)
		tabs.addTab(display_tab, 'Display & Format')
		
		btn_save = QtWidgets.QPushButton('Save Settings')
		btn_save.clicked.connect(self.save_settings)
		btn_cancel = QtWidgets.QPushButton('Cancel')
		btn_cancel.clicked.connect(self.reject)
		
		layout = QtWidgets.QVBoxLayout(self)
		layout.addWidget(tabs)
		
		buttons = QtWidgets.QHBoxLayout()
		buttons.addStretch()
		buttons.addWidget(btn_save)
		buttons.addWidget(btn_cancel)
		layout.addLayout(buttons)
		
		self.load_settings()
	
	def load_settings(self):
		settings = self.db.get_all_settings()
		
		# Shop Information
		self.shop_name.setText(settings.get('shop_name', 'Beauty P&C'))
		self.shop_phone.setText(settings.get('shop_phone', '0785993262'))
		self.shop_email.setText(settings.get('shop_email', 'beautypandc@gmail.com'))
		self.shop_address.setPlainText(settings.get('shop_address', ''))
		self.business_reg.setText(settings.get('business_reg', ''))
		self.business_license.setText(settings.get('business_license', ''))
		
		# Receipt & Invoice
		self.receipt_footer.setPlainText(settings.get('receipt_footer', 'Thank you!'))
		self.currency_symbol.setText(settings.get('currency_symbol', 'Rs.'))
		self.show_address_on_receipt.setChecked(settings.get('show_address_on_receipt', 'false').lower() == 'true')
		customer_show = settings.get('show_customer_on_receipt', 'Always')
		idx = self.show_customer_on_receipt.findText(customer_show)
		if idx >= 0:
			self.show_customer_on_receipt.setCurrentIndex(idx)
		self.invoice_prefix.setText(settings.get('invoice_prefix', 'INV'))
		self.bill_prefix.setText(settings.get('bill_prefix', 'BILL'))
		
		# Tax & Payment
		self.tax_enabled.setChecked(settings.get('tax_enabled', 'false').lower() == 'true')
		self.tax_percentage.setValue(float(settings.get('tax_percentage', '0.0')))
		tax_method = settings.get('tax_method', 'Inclusive')
		idx = self.tax_method.findText(tax_method)
		if idx >= 0:
			self.tax_method.setCurrentIndex(idx)
		self.show_tax_on_receipt.setChecked(settings.get('show_tax_on_receipt', 'false').lower() == 'true')
		payment_method = settings.get('default_payment_method', 'Cash')
		idx = self.default_payment_method.findText(payment_method)
		if idx >= 0:
			self.default_payment_method.setCurrentIndex(idx)
		cash_rounding = settings.get('cash_rounding', 'No Rounding')
		idx = self.cash_rounding.findText(cash_rounding)
		if idx >= 0:
			self.cash_rounding.setCurrentIndex(idx)
		self.allow_partial_payment.setChecked(settings.get('allow_partial_payment', 'false').lower() == 'true')
		
		# Stock & Products
		self.default_low_stock.setValue(int(settings.get('default_low_stock', '5')))
		self.default_stock_qty.setValue(int(settings.get('default_stock_qty', '0')))
		self.allow_negative_stock.setChecked(settings.get('allow_negative_stock', 'false').lower() == 'true')
		self.auto_update_cost_price.setChecked(settings.get('auto_update_cost_price', 'true').lower() == 'true')
		
		# Automation
		self.auto_print_receipt.setChecked(settings.get('auto_print_receipt', 'false').lower() == 'true')
		self.auto_generate_pdf.setChecked(settings.get('auto_generate_pdf', 'false').lower() == 'true')
		self.auto_create_customer.setChecked(settings.get('auto_create_customer', 'true').lower() == 'true')
		self.require_customer.setChecked(settings.get('require_customer', 'false').lower() == 'true')
		
		# Display & Format
		theme = settings.get('theme', 'Light')
		idx = self.theme.findText(theme)
		if idx >= 0:
			self.theme.setCurrentIndex(idx)
		date_format = settings.get('date_format', 'YYYY-MM-DD')
		idx = self.date_format.findText(date_format)
		if idx >= 0:
			self.date_format.setCurrentIndex(idx)
		time_format = settings.get('time_format', '24-hour')
		idx = self.time_format.findText(time_format)
		if idx >= 0:
			self.time_format.setCurrentIndex(idx)
		self.decimal_places.setValue(int(settings.get('decimal_places', '2')))
		currency_pos = settings.get('currency_position', 'Before Amount')
		idx = self.currency_position.findText(currency_pos)
		if idx >= 0:
			self.currency_position.setCurrentIndex(idx)
	
	def save_settings(self):
		# Save all settings to database
		self.db.set_setting('shop_name', self.shop_name.text().strip() or 'Beauty P&C')
		self.db.set_setting('shop_phone', self.shop_phone.text().strip() or '0785993262')
		self.db.set_setting('shop_email', self.shop_email.text().strip() or 'beautypandc@gmail.com')
		self.db.set_setting('shop_address', self.shop_address.toPlainText().strip())
		self.db.set_setting('business_reg', self.business_reg.text().strip())
		self.db.set_setting('business_license', self.business_license.text().strip())
		
		self.db.set_setting('receipt_footer', self.receipt_footer.toPlainText().strip() or 'Thank you!')
		self.db.set_setting('currency_symbol', self.currency_symbol.text().strip() or 'Rs.')
		self.db.set_setting('show_address_on_receipt', 'true' if self.show_address_on_receipt.isChecked() else 'false')
		self.db.set_setting('show_customer_on_receipt', self.show_customer_on_receipt.currentText())
		self.db.set_setting('invoice_prefix', self.invoice_prefix.text().strip() or 'INV')
		self.db.set_setting('bill_prefix', self.bill_prefix.text().strip() or 'BILL')
		
		self.db.set_setting('tax_enabled', 'true' if self.tax_enabled.isChecked() else 'false')
		self.db.set_setting('tax_percentage', str(self.tax_percentage.value()))
		self.db.set_setting('tax_method', self.tax_method.currentText())
		self.db.set_setting('show_tax_on_receipt', 'true' if self.show_tax_on_receipt.isChecked() else 'false')
		self.db.set_setting('default_payment_method', self.default_payment_method.currentText())
		self.db.set_setting('cash_rounding', self.cash_rounding.currentText())
		self.db.set_setting('allow_partial_payment', 'true' if self.allow_partial_payment.isChecked() else 'false')
		
		self.db.set_setting('default_low_stock', str(self.default_low_stock.value()))
		self.db.set_setting('default_stock_qty', str(self.default_stock_qty.value()))
		self.db.set_setting('allow_negative_stock', 'true' if self.allow_negative_stock.isChecked() else 'false')
		self.db.set_setting('auto_update_cost_price', 'true' if self.auto_update_cost_price.isChecked() else 'false')
		
		self.db.set_setting('auto_print_receipt', 'true' if self.auto_print_receipt.isChecked() else 'false')
		self.db.set_setting('auto_generate_pdf', 'true' if self.auto_generate_pdf.isChecked() else 'false')
		self.db.set_setting('auto_create_customer', 'true' if self.auto_create_customer.isChecked() else 'false')
		self.db.set_setting('require_customer', 'true' if self.require_customer.isChecked() else 'false')
		
		self.db.set_setting('theme', self.theme.currentText())
		self.db.set_setting('date_format', self.date_format.currentText())
		self.db.set_setting('time_format', self.time_format.currentText())
		self.db.set_setting('decimal_places', str(self.decimal_places.value()))
		self.db.set_setting('currency_position', self.currency_position.currentText())
		
		# Apply theme immediately
		from ui.theme import apply_theme
		apply_theme(self.db.get_setting('theme', 'Light'))
		
		QtWidgets.QMessageBox.information(self, 'Settings Saved', 'All settings have been saved successfully.')
		self.accept()
