import os
import sys
from PyQt5 import QtWidgets

from utils.db_helper import Database
from ui.login import LoginDialog
from ui.dashboard import DashboardWindow

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, 'database', 'beauty_pc.db')
SCHEMA_PATH = os.path.join(APP_DIR, 'schema.sql')
SAMPLE_DATA_PATH = None  # disabled by default to avoid demo data in real use
ASSETS_DIR = os.path.join(APP_DIR, 'assets')
INVOICES_DIR = os.path.join(APP_DIR, 'invoices')


def ensure_directories():
	os.makedirs(os.path.join(APP_DIR, 'database'), exist_ok=True)
	os.makedirs(os.path.join(APP_DIR, 'utils'), exist_ok=True)
	os.makedirs(os.path.join(APP_DIR, 'ui'), exist_ok=True)
	os.makedirs(os.path.join(ASSETS_DIR, 'icons'), exist_ok=True)
	os.makedirs(INVOICES_DIR, exist_ok=True)

	# placeholder logo if missing
	logo_path = os.path.join(ASSETS_DIR, 'logo.png')
	if not os.path.exists(logo_path):
		with open(logo_path, 'wb') as f:
			f.write(b'')


def initialize_database():
	Database.initialize(DB_PATH, SCHEMA_PATH, SAMPLE_DATA_PATH)
	Database.ensure_default_admin()


def apply_styles(app: QtWidgets.QApplication):
	"""Apply theme based on settings."""
	from ui.theme import apply_theme
	theme = Database.get_setting('theme', 'Light')
	apply_theme(theme, app)


def run():
	ensure_directories()
	initialize_database()

	app = QtWidgets.QApplication(sys.argv)
	apply_styles(app)
	login = LoginDialog(Database)
	if login.exec_() == QtWidgets.QDialog.Accepted:
		user = login.get_authenticated_user()
		window = DashboardWindow(Database, user)
		window.show()
		return app.exec_()
	return 0


if __name__ == '__main__':
	sys.exit(run())

