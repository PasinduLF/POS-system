from PyQt5 import QtWidgets
from .pos_screen import POSWidget
from .products import ProductsWidget
from .reports import ReportsWidget
from utils.backup import backup_database, export_table_to_csv, export_table_to_excel
import os
import zipfile


class DashboardWindow(QtWidgets.QMainWindow):
	def __init__(self, db, user, parent=None):
		super().__init__(parent)
		self.db = db
		self.user = user
		self.setWindowTitle('Beauty P&C POS - Dashboard')

		self.tabs = QtWidgets.QTabWidget()
		self.pos_tab = POSWidget(db, self.user)
		self.products_tab = ProductsWidget(db)
		self.reports_tab = ReportsWidget(db)

		self.tabs.addTab(self.pos_tab, 'POS')
		self.tabs.addTab(self.products_tab, 'Products')
		self.tabs.addTab(self.reports_tab, 'Reports')

		central = QtWidgets.QWidget()
		v = QtWidgets.QVBoxLayout(central)

		# Header: role and low stock
		header = QtWidgets.QHBoxLayout()
		self.info_label = QtWidgets.QLabel(f"Logged in: {self.user['username']} ({self.user['role']})")
		self.totals_label = QtWidgets.QLabel('')
		header.addWidget(self.info_label)
		header.addStretch()
		header.addWidget(self.totals_label)

		v.addLayout(header)
		v.addWidget(self.tabs)

		self.setCentralWidget(central)
		self.refresh_header()
		self._build_menu()

		# Start maximized for full-screen responsive layout
		self.showMaximized()

		if self.user['role'] == 'cashier':
			idx = self.tabs.indexOf(self.products_tab)
			self.tabs.removeTab(idx)
			idx = self.tabs.indexOf(self.reports_tab)
			self.tabs.removeTab(idx)

	def refresh_header(self):
		low = self.db.low_stock_products()
		low_count = len(low)
		daily = self.db.daily_totals()
		self.totals_label.setText(f"Low stock: {low_count} | Today: {daily['total']:.2f}")

	def _build_menu(self):
		menubar = self.menuBar()
		file_menu = menubar.addMenu('File')
		logout_action = file_menu.addAction('Logout')
		logout_action.setShortcut('Ctrl+L')
		backup_action = file_menu.addAction('Backup Database...')
		restore_action = file_menu.addAction('Restore Database...')
		exit_action = file_menu.addAction('Exit')
		logout_action.triggered.connect(self._logout)
		backup_action.triggered.connect(self._do_backup)
		restore_action.triggered.connect(self._do_restore)
		exit_action.triggered.connect(self.close)

		# View menu for fullscreen toggle
		view_menu = menubar.addMenu('View')
		self.fullscreen_action = view_menu.addAction('Toggle Full Screen')
		self.fullscreen_action.setShortcut('F11')
		self.fullscreen_action.triggered.connect(self._toggle_fullscreen)
		refresh_action = view_menu.addAction('Refresh')
		refresh_action.setShortcut('F5')
		refresh_action.triggered.connect(self._refresh_all)

		export_menu = menubar.addMenu('Export')
		self.export_actions = {
			'products': export_menu.addAction('Products (CSV)'),
			'sales': export_menu.addAction('Sales (CSV)'),
			'sale_items': export_menu.addAction('Sale Items (CSV)'),
			'categories': export_menu.addAction('Categories (CSV)'),
			'brands': export_menu.addAction('Brands (CSV)'),
			'expenses': export_menu.addAction('Expenses (CSV)'),
			'inventory_xlsx': export_menu.addAction('Inventory (Excel)'),
		}
		self.export_actions['products'].triggered.connect(lambda: self._export_table('products', 'csv'))
		self.export_actions['sales'].triggered.connect(lambda: self._export_table('sales', 'csv'))
		self.export_actions['sale_items'].triggered.connect(lambda: self._export_table('sale_items', 'csv'))
		self.export_actions['categories'].triggered.connect(lambda: self._export_table('categories', 'csv'))
		self.export_actions['brands'].triggered.connect(lambda: self._export_table('brands', 'csv'))
		self.export_actions['expenses'].triggered.connect(lambda: self._export_table('expenses', 'csv'))
		self.export_actions['other_income'] = export_menu.addAction('Other Income (CSV)')
		self.export_actions['other_income'].triggered.connect(lambda: self._export_table('other_income', 'csv'))
		self.export_actions['inventory_xlsx'].triggered.connect(lambda: self._export_table('products', 'xlsx'))

		manage_menu = menubar.addMenu('Manage')
		users_action = manage_menu.addAction('Users...')
		expenses_action = manage_menu.addAction('Expenses...')
		income_action = manage_menu.addAction('Other Income...')
		customers_action = manage_menu.addAction('Customers...')
		sales_action = manage_menu.addAction('Sales...')
		users_action.triggered.connect(self._open_users)
		expenses_action.triggered.connect(self._open_expenses)
		income_action.triggered.connect(self._open_other_income)
		customers_action.triggered.connect(self._open_customers)
		sales_action.triggered.connect(self._open_sales)

		# Role restrictions
		is_admin = self.user['role'] == 'admin'
		manage_menu.menuAction().setVisible(is_admin)
		export_menu.menuAction().setVisible(is_admin)
		backup_action.setVisible(is_admin)
		restore_action.setVisible(is_admin)

	def _toggle_fullscreen(self):
		if self.isFullScreen():
			self.showMaximized()
		else:
			self.showFullScreen()

	def _do_backup(self):
		path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Backup', 'beauty_pc_backup.zip', 'Zip Files (*.zip)')
		if not path:
			return
		try:
			backup_database(self.db._db_path, path)
			QtWidgets.QMessageBox.information(self, 'Backup', 'Backup completed')
		except Exception as e:
			QtWidgets.QMessageBox.critical(self, 'Backup Failed', str(e))

	def _do_restore(self):
		path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Restore Database', '', 'Zip (*.zip);;SQLite DB (*.db)')
		if not path:
			return
		try:
			if path.lower().endswith('.zip'):
				with zipfile.ZipFile(path, 'r') as zf:
					dbnames = [n for n in zf.namelist() if n.lower().endswith('.db')]
					if not dbnames:
						raise RuntimeError('No .db file in backup zip')
					zf.extract(dbnames[0], os.path.dirname(self.db._db_path))
					extracted = os.path.join(os.path.dirname(self.db._db_path), dbnames[0])
					os.replace(extracted, self.db._db_path)
			else:
				os.replace(path, self.db._db_path)
			QtWidgets.QMessageBox.information(self, 'Restore', 'Database restored. Please restart the app.')
		except Exception as e:
			QtWidgets.QMessageBox.critical(self, 'Restore Failed', str(e))

	def _export_table(self, table: str, fmt: str):
		if fmt == 'csv':
			path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Export to CSV', f'{table}.csv', 'CSV (*.csv)')
			if not path:
				return
			try:
				export_table_to_csv(self.db.connection(), table, path)
				QtWidgets.QMessageBox.information(self, 'Export', 'Exported to CSV')
			except Exception as e:
				QtWidgets.QMessageBox.critical(self, 'Export Failed', str(e))
		else:
			path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Export to Excel', f'{table}.xlsx', 'Excel (*.xlsx)')
			if not path:
				return
			try:
				export_table_to_excel(self.db.connection(), table, path)
				QtWidgets.QMessageBox.information(self, 'Export', 'Exported to Excel')
			except Exception as e:
				QtWidgets.QMessageBox.critical(self, 'Export Failed', str(e))

	def _open_users(self):
		try:
			from .users import UsersDialog
			dlg = UsersDialog(self.db, parent=self)
			dlg.exec_()
		except Exception as e:
			QtWidgets.QMessageBox.critical(self, 'Users', str(e))

	def _open_expenses(self):
		try:
			from .expenses import ExpensesDialog
			dlg = ExpensesDialog(self.db, parent=self)
			dlg.exec_()
		except Exception as e:
			QtWidgets.QMessageBox.critical(self, 'Expenses', str(e))

	def _open_other_income(self):
		try:
			from .other_income import OtherIncomeDialog
			dlg = OtherIncomeDialog(self.db, parent=self)
			dlg.exec_()
		except Exception as e:
			QtWidgets.QMessageBox.critical(self, 'Other Income', str(e))

	def _open_sales(self):
		try:
			from .sales import SalesDialog
			dlg = SalesDialog(self.db, parent=self)
			dlg.exec_()
		except Exception as e:
			QtWidgets.QMessageBox.critical(self, 'Sales', str(e))

	def _open_customers(self):
		try:
			from .customers import CustomersDialog
			dlg = CustomersDialog(self.db, parent=self)
			dlg.exec_()
		except Exception as e:
			QtWidgets.QMessageBox.critical(self, 'Customers', str(e))

	def _logout(self):
		from ui.login import LoginDialog
		app = QtWidgets.QApplication.instance()
		# Close current main window
		self.close()
		# Show login dialog
		login = LoginDialog(self.db)
		if login.exec_() == QtWidgets.QDialog.Accepted:
			new_user = login.get_authenticated_user()
			if not new_user:
				app.quit()
				return
			# Open a fresh dashboard window
			new_window = DashboardWindow(self.db, new_user)
			# Keep a reference on the app to avoid GC
			setattr(app, '_main_window', new_window)
			new_window.show()
		else:
			app.quit()

	def _rebuild_tabs(self):
		# Clear and recreate main tabs according to role
		while self.tabs.count() > 0:
			self.tabs.removeTab(0)
		self.pos_tab = POSWidget(self.db, self.user)
		self.tabs.addTab(self.pos_tab, 'POS')
		if self.user['role'] == 'admin':
			self.products_tab = ProductsWidget(self.db)
			self.reports_tab = ReportsWidget(self.db)
			self.tabs.addTab(self.products_tab, 'Products')
			self.tabs.addTab(self.reports_tab, 'Reports')

	def _refresh_all(self):
		# Refresh header stats
		self.refresh_header()
		# Refresh POS product list/cart totals
		try:
			self.pos_tab.refresh_all()
		except Exception:
			pass
		# Refresh Products list
		try:
			self.products_tab.refresh()
		except Exception:
			pass
		# Reports view is on-demand; nothing to refresh here

