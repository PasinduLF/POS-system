from PyQt5 import QtWidgets


def get_light_theme() -> str:
	"""Returns the light theme stylesheet."""
	return '''
		QMainWindow, QWidget { 
			background-color: #f7f7f9; 
			color: #333333;
		}
		QTabWidget::pane { 
			border: 1px solid #dcdce0; 
			background-color: white;
		}
		QTabBar::tab { 
			padding: 6px 12px; 
			background-color: #e9ecef;
			border: 1px solid #dcdce0;
			border-bottom: none;
		}
		QTabBar::tab:selected { 
			background-color: white;
			border-bottom: 2px solid #2d7dff;
		}
		QPushButton { 
			padding: 6px 10px; 
			background-color: #2d7dff; 
			color: white; 
			border: none; 
			border-radius: 3px; 
		}
		QPushButton:hover { 
			background-color: #1e6ae6; 
		}
		QPushButton:pressed { 
			background-color: #1559d1; 
		}
		QPushButton:disabled { 
			background-color: #9ab8ff; 
			color: #cccccc;
		}
		QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QPlainTextEdit { 
			padding: 6px; 
			border: 1px solid #dcdce0; 
			border-radius: 3px; 
			background-color: white; 
			color: #333333;
		}
		QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QPlainTextEdit:focus { 
			border: 1px solid #2d7dff; 
		}
		QTableWidget { 
			gridline-color: #e6e6ea; 
			background-color: white;
			color: #333333;
		}
		QTableWidget::item:selected { 
			background-color: #e3f2fd; 
			color: #333333;
		}
		QHeaderView::section { 
			background-color: #f0f0f0; 
			padding: 6px;
			border: 1px solid #dcdce0;
		}
		QMenuBar { 
			background-color: white; 
			color: #333333;
		}
		QMenuBar::item:selected { 
			background-color: #e3f2fd; 
		}
		QMenu { 
			background-color: white; 
			color: #333333;
		}
		QMenu::item:selected { 
			background-color: #e3f2fd; 
		}
		QLabel { 
			color: #333333;
		}
		QCheckBox { 
			color: #333333;
		}
		QDialog { 
			background-color: white; 
			color: #333333;
		}
	'''


def get_dark_theme() -> str:
	"""Returns the dark theme stylesheet."""
	return '''
		QMainWindow, QWidget { 
			background-color: #1e1e1e; 
			color: #e0e0e0;
		}
		QTabWidget::pane { 
			border: 1px solid #3d3d3d; 
			background-color: #2d2d2d;
		}
		QTabBar::tab { 
			padding: 6px 12px; 
			background-color: #2d2d2d;
			border: 1px solid #3d3d3d;
			border-bottom: none;
			color: #e0e0e0;
		}
		QTabBar::tab:selected { 
			background-color: #1e1e1e;
			border-bottom: 2px solid #4a9eff;
			color: #4a9eff;
		}
		QPushButton { 
			padding: 6px 10px; 
			background-color: #4a9eff; 
			color: white; 
			border: none; 
			border-radius: 3px; 
		}
		QPushButton:hover { 
			background-color: #3a8eef; 
		}
		QPushButton:pressed { 
			background-color: #2a7edf; 
		}
		QPushButton:disabled { 
			background-color: #2d4d7d; 
			color: #666666;
		}
		QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QPlainTextEdit { 
			padding: 6px; 
			border: 1px solid #3d3d3d; 
			border-radius: 3px; 
			background-color: #2d2d2d; 
			color: #e0e0e0;
		}
		QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QPlainTextEdit:focus { 
			border: 1px solid #4a9eff; 
		}
		QTableWidget { 
			gridline-color: #3d3d3d; 
			background-color: #2d2d2d;
			color: #e0e0e0;
		}
		QTableWidget::item { 
			background-color: #2d2d2d;
			color: #e0e0e0;
			border: none;
		}
		QTableWidget::item:selected { 
			background-color: #3d5a7d; 
			color: white;
		}
		QTableWidget::item:alternate { 
			background-color: #252525;
			color: #e0e0e0;
		}
		QTableWidget QTableCornerButton::section {
			background-color: #252525;
			border: 1px solid #3d3d3d;
		}
		QHeaderView::section { 
			background-color: #252525; 
			padding: 6px;
			border: 1px solid #3d3d3d;
			color: #e0e0e0;
		}
		QMenuBar { 
			background-color: #252525; 
			color: #e0e0e0;
		}
		QMenuBar::item:selected { 
			background-color: #3d5a7d; 
		}
		QMenu { 
			background-color: #252525; 
			color: #e0e0e0;
		}
		QMenu::item:selected { 
			background-color: #3d5a7d; 
		}
		QLabel { 
			color: #e0e0e0;
		}
		QCheckBox { 
			color: #e0e0e0;
		}
		QDialog { 
			background-color: #2d2d2d; 
			color: #e0e0e0;
		}
	'''


def apply_theme(theme_name: str = 'Light', app: QtWidgets.QApplication = None) -> None:
	"""Apply the specified theme to the application.
	
	Args:
		theme_name: 'Light' or 'Dark'
		app: QApplication instance. If None, will get the instance.
	"""
	if app is None:
		app = QtWidgets.QApplication.instance()
	
	if app is None:
		return
	
	if theme_name.lower() == 'dark':
		app.setStyleSheet(get_dark_theme())
	else:
		app.setStyleSheet(get_light_theme())

