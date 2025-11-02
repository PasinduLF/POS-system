from PyQt5 import QtWidgets, QtCore, QtGui
from datetime import datetime
import json


class SummaryCard(QtWidgets.QFrame):
	"""A card widget displaying a single metric."""
	def __init__(self, title: str, value: str, icon: str = '', color: str = '#2d7dff', parent=None):
		super().__init__(parent)
		self.setFrameShape(QtWidgets.QFrame.Box)
		self.setFrameShadow(QtWidgets.QFrame.Raised)
		
		# Initialize attributes before calling _apply_theme_style
		self.db_ref = None  # Will be set by parent
		self.title = title
		self.value_text = value
		self.icon_text = icon
		self.value_color = color
		
		layout = QtWidgets.QVBoxLayout(self)
		layout.setContentsMargins(10, 10, 10, 10)
		layout.setSpacing(5)
		
		self.title_label = QtWidgets.QLabel(title)
		layout.addWidget(self.title_label)
		
		self.value_label = QtWidgets.QLabel(value)
		layout.addWidget(self.value_label)
		
		self.icon_label = None
		if icon:
			self.icon_label = QtWidgets.QLabel(icon)
			layout.addWidget(self.icon_label)
		
		# Apply theme styling after widgets are created
		self._apply_theme_style()
	
	def set_db(self, db):
		"""Set database reference for theme access."""
		self.db_ref = db
		self._apply_theme_style()
	
	def _apply_theme_style(self):
		"""Apply theme-based styling."""
		# Get theme from db reference if available
		is_dark = False
		if self.db_ref:
			theme = self.db_ref.get_setting('theme', 'Light')
			is_dark = theme.lower() == 'dark'
		else:
			# Try to get from parent widget chain
			parent = self.parent()
			while parent:
				if hasattr(parent, 'db'):
					theme = parent.db.get_setting('theme', 'Light')
					is_dark = theme.lower() == 'dark'
					break
				parent = parent.parent()
		
		if is_dark:
			bg_color = '#2d2d2d'
			border_color = '#3d3d3d'
			title_color = '#b0b0b0'
		else:
			bg_color = 'white'
			border_color = '#e0e0e0'
			title_color = '#666'
		
		self.setStyleSheet(f'''
			QFrame {{
				background-color: {bg_color};
				border: 1px solid {border_color};
				border-radius: 8px;
				padding: 15px;
			}}
		''')
		
		if hasattr(self, 'title_label'):
			self.title_label.setStyleSheet(f'color: {title_color}; font-size: 11pt;')
		if hasattr(self, 'value_label'):
			self.value_label.setStyleSheet(f'color: {self.value_color}; font-size: 20pt; font-weight: bold;')
		if hasattr(self, 'icon_label') and self.icon_label:
			self.icon_label.setStyleSheet('font-size: 24pt;')

	def update_value(self, value: str):
		"""Update the value displayed."""
		self.value_text = value
		if hasattr(self, 'value_label'):
			self.value_label.setText(value)


class ChartView(QtWidgets.QWidget):
	"""Custom widget for drawing the sales chart."""
	def __init__(self, db, parent=None):
		super().__init__(parent)
		self.db = db
		self.period = 'today'
		self.setMinimumHeight(200)
		self.setStyleSheet('background-color: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 4px;')

	def set_period(self, period: str):
		"""Set the time period for the chart."""
		self.period = period
		self.update()

	def paintEvent(self, event):
		"""Draw the chart."""
		# Get data
		data = self.db.sales_by_time_period(self.period)
		if not data:
			# Draw empty state
			painter = QtGui.QPainter(self)
			painter.setRenderHint(QtGui.QPainter.Antialiasing)
			theme = self.db.get_setting('theme', 'Light')
			is_dark = theme.lower() == 'dark'
			bg_color = QtGui.QColor('#2d2d2d') if is_dark else QtGui.QColor('#f8f9fa')
			text_color = QtGui.QColor('#e0e0e0') if is_dark else QtGui.QColor('#666666')
			painter.fillRect(self.rect(), bg_color)
			painter.setPen(QtGui.QPen(text_color))
			font = QtGui.QFont()
			font.setPointSize(12)
			painter.setFont(font)
			period_label = self.period.replace('_', ' ').title() if self.period != 'all_time' else 'All Time'
			painter.drawText(self.rect(), QtCore.Qt.AlignCenter, f'No sales data for {period_label}')
			painter.end()
			return
		
		# Prepare data for chart
		time_units = [r['time_unit'] for r in data]
		totals = [float(r['total']) for r in data]
		
		if not totals or all(t == 0 for t in totals):
			# Draw empty state
			painter = QtGui.QPainter(self)
			painter.setRenderHint(QtGui.QPainter.Antialiasing)
			theme = self.db.get_setting('theme', 'Light')
			is_dark = theme.lower() == 'dark'
			bg_color = QtGui.QColor('#2d2d2d') if is_dark else QtGui.QColor('#f8f9fa')
			text_color = QtGui.QColor('#e0e0e0') if is_dark else QtGui.QColor('#666666')
			painter.fillRect(self.rect(), bg_color)
			painter.setPen(QtGui.QPen(text_color))
			font = QtGui.QFont()
			font.setPointSize(12)
			painter.setFont(font)
			painter.drawText(self.rect(), QtCore.Qt.AlignCenter, 'No sales data for today')
			painter.end()
			return
		
		max_value = max(totals) if totals else 1
		if max_value == 0:
			max_value = 1
		
		# Create painter
		painter = QtGui.QPainter(self)
		painter.setRenderHint(QtGui.QPainter.Antialiasing)
		
		# Get theme
		theme = self.db.get_setting('theme', 'Light')
		is_dark = theme.lower() == 'dark'
		line_color = QtGui.QColor('#4a9eff') if is_dark else QtGui.QColor('#2d7dff')
		bg_color = QtGui.QColor('#2d2d2d') if is_dark else QtGui.QColor('#f8f9fa')
		grid_color = QtGui.QColor('#3d3d3d') if is_dark else QtGui.QColor('#e0e0e0')
		text_color = QtGui.QColor('#e0e0e0') if is_dark else QtGui.QColor('#333333')
		
		painter.fillRect(self.rect(), bg_color)
		
		width = self.width()
		height = self.height()
		margin = 40
		
		if width < 100 or height < 100:
			painter.end()
			return
		
		# Draw grid lines
		painter.setPen(QtGui.QPen(grid_color, 1, QtCore.Qt.DashLine))
		for i in range(5):
			y = margin + (height - 2 * margin) * i / 4
			painter.drawLine(margin, int(y), width - margin, int(y))
		
		# Draw axes
		painter.setPen(QtGui.QPen(text_color, 1))
		painter.drawLine(margin, margin, margin, height - margin)
		painter.drawLine(margin, height - margin, width - margin, height - margin)
		
		# Draw chart line and points
		if len(time_units) > 0:
			painter.setPen(QtGui.QPen(line_color, 2))
			painter.setBrush(QtGui.QBrush(line_color))
			
			points = []
			chart_width = width - 2 * margin
			chart_height = height - 2 * margin
			
			for i, (time_unit, total) in enumerate(zip(time_units, totals)):
				if len(time_units) > 1:
					x = margin + (chart_width / max(1, len(time_units) - 1)) * i
				else:
					x = margin + chart_width / 2
				y = height - margin - (total / max_value) * chart_height
				points.append((x, y))
			
			# Draw line
			for i in range(len(points) - 1):
				painter.drawLine(int(points[i][0]), int(points[i][1]), 
								int(points[i + 1][0]), int(points[i + 1][1]))
			
			# Draw points
			for x, y in points:
				painter.drawEllipse(int(x) - 4, int(y) - 4, 8, 8)
		
		# Draw labels
		painter.setPen(QtGui.QPen(text_color, 1))
		font = QtGui.QFont()
		font.setPointSize(9)
		painter.setFont(font)
		
		# Y-axis labels
		for i in range(5):
			value = max_value * (1 - i / 4)
			if value >= 1000:
				label = f'{value/1000:.1f}K'
			else:
				label = f'{value:.0f}'
			painter.drawText(5, int(margin + (height - 2 * margin) * i / 4 + 5), label)
		
		# X-axis labels (format based on period)
		if len(time_units) > 0:
			for i, time_unit in enumerate(time_units):
				if len(time_units) > 1:
					x = margin + (chart_width / max(1, len(time_units) - 1)) * i
				else:
					x = margin + chart_width / 2
				
				# Format label based on period
				if self.period == 'today':
					# Hour format: HH:00
					label = f'{time_unit}:00'
				elif self.period in ('week', 'month'):
					# Date format: DD/MM
					try:
						from datetime import datetime
						dt = datetime.strptime(time_unit, '%Y-%m-%d')
						label = dt.strftime('%d/%m')
					except:
						label = time_unit[:5] if len(time_unit) > 5 else time_unit
				else:  # year or all_time
					# Month format: MM/YY or YYYY-MM
					label = time_unit[-5:] if len(time_unit) > 5 else time_unit
				
				# Truncate long labels
				if len(label) > 8:
					label = label[:5] + '...'
				painter.drawText(int(x) - 20, height - margin + 20, label)
		
		painter.end()


class SalesChartWidget(QtWidgets.QWidget):
	"""A simple line chart widget for sales by period."""
	def __init__(self, db, period: str = 'today', parent=None):
		super().__init__(parent)
		self.db = db
		self.period = period
		self.setMinimumHeight(250)
		
		layout = QtWidgets.QVBoxLayout(self)
		layout.setContentsMargins(10, 10, 10, 10)
		
		period_label = period.replace('_', ' ').title() if period != 'all_time' else 'All Time'
		title = QtWidgets.QLabel(f'📈 Sales Chart ({period_label})')
		title.setStyleSheet('font-size: 14pt; font-weight: bold; margin-bottom: 10px;')
		layout.addWidget(title)
		
		self.chart_view = ChartView(db)
		self.chart_view.set_period(period)
		self.chart_view.setMinimumHeight(200)
		layout.addWidget(self.chart_view)

	def set_period(self, period: str):
		"""Set the time period for the chart."""
		self.period = period
		period_label = period.replace('_', ' ').title() if period != 'all_time' else 'All Time'
		# Update title
		title_label = self.findChild(QtWidgets.QLabel)
		if title_label:
			title_label.setText(f'📈 Sales Chart ({period_label})')
		if self.chart_view:
			self.chart_view.set_period(period)

	def refresh(self):
		"""Refresh the chart."""
		if self.chart_view:
			self.chart_view.update()


class TopProductsWidget(QtWidgets.QFrame):
	"""Widget showing top selling products for selected period."""
	def __init__(self, db, period: str = 'today', parent=None):
		super().__init__(parent)
		self.db = db
		self.period = period
		self.setFrameShape(QtWidgets.QFrame.Box)
		self.setFrameShadow(QtWidgets.QFrame.Raised)
		self._apply_theme_style()
		
		layout = QtWidgets.QVBoxLayout(self)
		layout.setContentsMargins(10, 10, 10, 10)
		
		period_label = period.replace('_', ' ').title() if period != 'all_time' else 'All Time'
		self.title_label = QtWidgets.QLabel(f'🏆 Top Products ({period_label})')
		self.title_label.setStyleSheet('font-size: 14pt; font-weight: bold; margin-bottom: 10px;')
		layout.addWidget(self.title_label)
		
		self.table = QtWidgets.QTableWidget(0, 3)
		self.table.setHorizontalHeaderLabels(['Product', 'Qty', 'Revenue'])
		self.table.horizontalHeader().setStretchLastSection(True)
		self.table.verticalHeader().setVisible(False)
		self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		self.table.setAlternatingRowColors(True)
		self.table.setMaximumHeight(200)
		layout.addWidget(self.table)

	def set_period(self, period: str):
		"""Set the time period for the widget."""
		self.period = period
		period_label = period.replace('_', ' ').title() if period != 'all_time' else 'All Time'
		self.title_label.setText(f'🏆 Top Products ({period_label})')
		self.refresh()

	def refresh(self):
		"""Refresh the top products list."""
		data = self.db.top_products_by_period(self.period, 5)
		self.table.setRowCount(0)
		
		theme = self.db.get_setting('theme', 'Light')
		is_dark = theme.lower() == 'dark'
		text_color = QtGui.QColor('#e0e0e0') if is_dark else QtGui.QColor('#333333')
		
		for r in data:
			row = self.table.rowCount()
			self.table.insertRow(row)
			
			item1 = QtWidgets.QTableWidgetItem(r['name'] or 'Unknown')
			item1.setForeground(QtGui.QBrush(text_color))
			self.table.setItem(row, 0, item1)
			
			item2 = QtWidgets.QTableWidgetItem(str(int(r['qty'])))
			item2.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
			item2.setForeground(QtGui.QBrush(text_color))
			self.table.setItem(row, 1, item2)
			
			item3 = QtWidgets.QTableWidgetItem(f"{float(r['revenue']):.2f}")
			item3.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
			item3.setForeground(QtGui.QBrush(text_color))
			self.table.setItem(row, 2, item3)
	
	def _apply_theme_style(self):
		"""Apply theme-based styling."""
		theme = self.db.get_setting('theme', 'Light')
		is_dark = theme.lower() == 'dark'
		
		if is_dark:
			bg_color = '#2d2d2d'
			border_color = '#3d3d3d'
		else:
			bg_color = 'white'
			border_color = '#e0e0e0'
		
		self.setStyleSheet(f'''
			QFrame {{
				background-color: {bg_color};
				border: 1px solid {border_color};
				border-radius: 8px;
				padding: 15px;
			}}
		''')


class LowStockWidget(QtWidgets.QFrame):
	"""Widget showing products with low stock."""
	def __init__(self, db, parent=None):
		super().__init__(parent)
		self.db = db
		self.setFrameShape(QtWidgets.QFrame.Box)
		self.setFrameShadow(QtWidgets.QFrame.Raised)
		self._apply_theme_style()
		
		layout = QtWidgets.QVBoxLayout(self)
		layout.setContentsMargins(10, 10, 10, 10)
		
		title = QtWidgets.QLabel('⚠️ Low Stock Alerts')
		title.setStyleSheet('font-size: 14pt; font-weight: bold; color: #ff9800; margin-bottom: 10px;')
		layout.addWidget(title)
		
		self.table = QtWidgets.QTableWidget(0, 3)
		self.table.setHorizontalHeaderLabels(['Product', 'Stock', 'Threshold'])
		self.table.horizontalHeader().setStretchLastSection(True)
		self.table.verticalHeader().setVisible(False)
		self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		self.table.setAlternatingRowColors(True)
		self.table.setMaximumHeight(200)
		layout.addWidget(self.table)

	def refresh(self):
		"""Refresh the low stock list."""
		data = self.db.low_stock_products()
		self.table.setRowCount(0)
		
		theme = self.db.get_setting('theme', 'Light')
		is_dark = theme.lower() == 'dark'
		text_color = QtGui.QColor('#e0e0e0') if is_dark else QtGui.QColor('#333333')
		warning_color = QtGui.QColor('#ff9800')
		
		for r in data:
			row = self.table.rowCount()
			self.table.insertRow(row)
			
			item1 = QtWidgets.QTableWidgetItem(r['name'] or 'Unknown')
			item1.setForeground(QtGui.QBrush(text_color))
			self.table.setItem(row, 0, item1)
			
			item2 = QtWidgets.QTableWidgetItem(str(r['stock_quantity']))
			item2.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
			item2.setForeground(QtGui.QBrush(warning_color))
			self.table.setItem(row, 1, item2)
			
			item3 = QtWidgets.QTableWidgetItem(str(r['low_stock_threshold']))
			item3.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
			item3.setForeground(QtGui.QBrush(text_color))
			self.table.setItem(row, 2, item3)
		
		if len(data) == 0:
			# Show message if no low stock items
			row = self.table.rowCount()
			self.table.insertRow(row)
			item = QtWidgets.QTableWidgetItem('✓ All products have sufficient stock')
			item.setForeground(QtGui.QBrush(QtGui.QColor('#4caf50')))
			item.setTextAlignment(QtCore.Qt.AlignCenter)
			self.table.setItem(row, 0, item)
			self.table.setSpan(row, 0, 1, 3)
	
	def _apply_theme_style(self):
		"""Apply theme-based styling."""
		theme = self.db.get_setting('theme', 'Light')
		is_dark = theme.lower() == 'dark'
		
		if is_dark:
			bg_color = '#2d2d2d'
			border_color = '#ff9800'
		else:
			bg_color = 'white'
			border_color = '#ff9800'
		
		self.setStyleSheet(f'''
			QFrame {{
				background-color: {bg_color};
				border: 1px solid {border_color};
				border-radius: 8px;
				padding: 15px;
			}}
		''')


class DashboardWidgets(QtWidgets.QWidget):
	"""Main dashboard widgets container with customizable layout."""
	def __init__(self, db, parent=None):
		super().__init__(parent)
		self.db = db
		self.period = 'today'  # Default period
		self.refresh_timer = QtCore.QTimer()
		self.refresh_timer.timeout.connect(self.refresh_all)
		self.refresh_timer.start(60000)  # Refresh every 60 seconds
		
		# Load widget preferences
		self.widget_preferences = self.load_widget_preferences()
		
		main_layout = QtWidgets.QVBoxLayout(self)
		main_layout.setContentsMargins(15, 15, 15, 15)
		main_layout.setSpacing(15)
		
		# Header with period selector, refresh button and customize button
		header = QtWidgets.QHBoxLayout()
		title = QtWidgets.QLabel('📊 Dashboard')
		title.setStyleSheet('font-size: 18pt; font-weight: bold;')
		header.addWidget(title)
		header.addStretch()
		
		# Period selector
		period_label = QtWidgets.QLabel('Period:')
		period_label.setStyleSheet('font-size: 11pt;')
		header.addWidget(period_label)
		
		self.period_combo = QtWidgets.QComboBox()
		self.period_combo.addItems(['Today', 'Week', 'Month', 'Year', 'All Time'])
		self.period_combo.setCurrentText('Today')
		self.period_combo.currentTextChanged.connect(self._on_period_changed)
		header.addWidget(self.period_combo)
		
		self.refresh_btn = QtWidgets.QPushButton('🔄 Refresh')
		self.refresh_btn.clicked.connect(self.refresh_all)
		header.addWidget(self.refresh_btn)
		
		self.customize_btn = QtWidgets.QPushButton('⚙️ Customize')
		self.customize_btn.clicked.connect(self.customize_layout)
		header.addWidget(self.customize_btn)
		
		main_layout.addLayout(header)
		
		# Scroll area for widgets
		scroll = QtWidgets.QScrollArea()
		scroll.setWidgetResizable(True)
		scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
		
		self.widget_container = QtWidgets.QWidget()
		self.container_layout = QtWidgets.QVBoxLayout(self.widget_container)
		self.container_layout.setContentsMargins(0, 0, 0, 0)
		self.container_layout.setSpacing(15)
		
		scroll.setWidget(self.widget_container)
		main_layout.addWidget(scroll)
		
		# Initialize widgets
		self.summary_cards = {}
		self.chart_widget = None
		self.top_products_widget = None
		self.low_stock_widget = None
		
		self.build_widgets()

	def load_widget_preferences(self) -> dict:
		"""Load widget visibility and layout preferences from settings."""
		prefs_json = self.db.get_setting('dashboard_widgets_prefs', '{}')
		try:
			return json.loads(prefs_json)
		except:
			return {
				'summary_cards': {'visible': True},
				'sales_chart': {'visible': True},
				'top_products': {'visible': True},
				'low_stock': {'visible': True}
			}

	def save_widget_preferences(self):
		"""Save widget visibility and layout preferences to settings."""
		prefs_json = json.dumps(self.widget_preferences)
		self.db.set_setting('dashboard_widgets_prefs', prefs_json)

	def build_widgets(self):
		"""Build all dashboard widgets based on preferences."""
		# Clear existing widgets
		self.clear_widgets()
		
		# Summary cards row
		if self.widget_preferences.get('summary_cards', {}).get('visible', True):
			cards_row = QtWidgets.QHBoxLayout()
			cards_row.setSpacing(15)
			
			stats = self.db.summary_stats(self.period)
			currency_symbol = self.db.get_setting('currency_symbol', 'Rs.')
			
			period_label = self.period.replace('_', ' ').title() if self.period != 'all_time' else 'All Time'
			
			# Revenue card
			revenue_card = SummaryCard(
				f'💰 Revenue ({period_label})',
				f'{currency_symbol}{stats["revenue"]:.2f}',
				icon='',
				color='#4caf50'
			)
			revenue_card.set_db(self.db)
			cards_row.addWidget(revenue_card)
			self.summary_cards['revenue'] = revenue_card
			
			# Transactions card
			transactions_card = SummaryCard(
				'📋 Transactions',
				str(stats['transactions']),
				icon='',
				color='#2196f3'
			)
			transactions_card.set_db(self.db)
			cards_row.addWidget(transactions_card)
			self.summary_cards['transactions'] = transactions_card
			
			# Customers card
			customers_card = SummaryCard(
				'👥 Customers',
				str(stats['customers']),
				icon='',
				color='#9c27b0'
			)
			customers_card.set_db(self.db)
			cards_row.addWidget(customers_card)
			self.summary_cards['customers'] = customers_card
			
			# Average transaction card
			avg_card = SummaryCard(
				'📊 Avg Transaction',
				f'{currency_symbol}{stats["avg_transaction"]:.2f}',
				icon='',
				color='#ff9800'
			)
			avg_card.set_db(self.db)
			cards_row.addWidget(avg_card)
			self.summary_cards['avg_transaction'] = avg_card
			
			cards_widget = QtWidgets.QWidget()
			cards_widget.setLayout(cards_row)
			self.container_layout.addWidget(cards_widget)
		
		# Chart and other widgets row
		middle_row = QtWidgets.QHBoxLayout()
		middle_row.setSpacing(15)
		
		# Sales chart
		if self.widget_preferences.get('sales_chart', {}).get('visible', True):
			chart_container = QtWidgets.QFrame()
			chart_container.setFrameShape(QtWidgets.QFrame.Box)
			chart_container.setFrameShadow(QtWidgets.QFrame.Raised)
			# Apply theme styling
			theme = self.db.get_setting('theme', 'Light')
			is_dark = theme.lower() == 'dark'
			bg_color = '#2d2d2d' if is_dark else 'white'
			border_color = '#3d3d3d' if is_dark else '#e0e0e0'
			chart_container.setStyleSheet(f'''
				QFrame {{
					background-color: {bg_color};
					border: 1px solid {border_color};
					border-radius: 8px;
					padding: 10px;
				}}
			''')
			chart_layout = QtWidgets.QVBoxLayout(chart_container)
			chart_layout.setContentsMargins(0, 0, 0, 0)
			
			self.chart_widget = SalesChartWidget(self.db, self.period)
			chart_layout.addWidget(self.chart_widget)
			middle_row.addWidget(chart_container, 2)  # Chart takes 2/3 space
		
		# Right column widgets
		right_column = QtWidgets.QVBoxLayout()
		right_column.setSpacing(15)
		
		# Top products
		if self.widget_preferences.get('top_products', {}).get('visible', True):
			self.top_products_widget = TopProductsWidget(self.db, self.period)
			right_column.addWidget(self.top_products_widget)
		
		# Low stock
		if self.widget_preferences.get('low_stock', {}).get('visible', True):
			self.low_stock_widget = LowStockWidget(self.db)
			right_column.addWidget(self.low_stock_widget)
		
		if right_column.count() > 0:
			right_widget = QtWidgets.QWidget()
			right_widget.setLayout(right_column)
			middle_row.addWidget(right_widget, 1)  # Right column takes 1/3 space
		
		if middle_row.count() > 0:
			middle_widget = QtWidgets.QWidget()
			middle_widget.setLayout(middle_row)
			self.container_layout.addWidget(middle_widget)
		
		self.container_layout.addStretch()
		
		# Initial refresh
		self.refresh_all()

	def clear_widgets(self):
		"""Clear all widgets from container."""
		while self.container_layout.count():
			child = self.container_layout.takeAt(0)
			if child.widget():
				child.widget().deleteLater()
		
		self.summary_cards.clear()
		self.chart_widget = None
		self.top_products_widget = None
		self.low_stock_widget = None

	def _on_period_changed(self, period_text: str):
		"""Handle period selection change."""
		period_map = {
			'Today': 'today',
			'Week': 'week',
			'Month': 'month',
			'Year': 'year',
			'All Time': 'all_time'
		}
		self.period = period_map.get(period_text, 'today')
		# Rebuild widgets with new period
		self.build_widgets()

	def refresh_all(self):
		"""Refresh all dashboard widgets."""
		# Refresh summary cards
		stats = self.db.summary_stats(self.period)
		currency_symbol = self.db.get_setting('currency_symbol', 'Rs.')
		
		period_label = self.period.replace('_', ' ').title() if self.period != 'all_time' else 'All Time'
		
		if 'revenue' in self.summary_cards:
			# Update title and value
			if hasattr(self.summary_cards['revenue'], 'title_label'):
				self.summary_cards['revenue'].title_label.setText(f'💰 Revenue ({period_label})')
			self.summary_cards['revenue'].update_value(f'{currency_symbol}{stats["revenue"]:.2f}')
		
		if 'transactions' in self.summary_cards:
			self.summary_cards['transactions'].update_value(str(stats['transactions']))
		
		if 'customers' in self.summary_cards:
			self.summary_cards['customers'].update_value(str(stats['customers']))
		
		if 'avg_transaction' in self.summary_cards:
			self.summary_cards['avg_transaction'].update_value(f'{currency_symbol}{stats["avg_transaction"]:.2f}')
		
		# Refresh chart
		if self.chart_widget:
			self.chart_widget.set_period(self.period)
			self.chart_widget.refresh()
		
		# Refresh top products
		if self.top_products_widget:
			self.top_products_widget.set_period(self.period)
			self.top_products_widget.refresh()
		
		# Refresh low stock
		if self.low_stock_widget:
			self.low_stock_widget.refresh()

	def customize_layout(self):
		"""Open dialog to customize widget visibility."""
		dlg = CustomizeDashboardDialog(self.widget_preferences.copy(), parent=self)
		if dlg.exec_() == QtWidgets.QDialog.Accepted:
			self.widget_preferences = dlg.get_preferences()
			self.save_widget_preferences()
			self.build_widgets()


class CustomizeDashboardDialog(QtWidgets.QDialog):
	"""Dialog for customizing dashboard widget layout."""
	def __init__(self, preferences: dict, parent=None):
		super().__init__(parent)
		self.preferences = preferences
		self.setWindowTitle('Customize Dashboard')
		self.setMinimumWidth(400)
		
		layout = QtWidgets.QVBoxLayout(self)
		
		info_label = QtWidgets.QLabel('Select which widgets to display on the dashboard:')
		layout.addWidget(info_label)
		
		# Checkboxes for each widget
		self.checkboxes = {}
		widgets = [
			('summary_cards', 'Summary Cards (Revenue, Transactions, etc.)'),
			('sales_chart', 'Real-time Sales Chart'),
			('top_products', 'Top Products Widget'),
			('low_stock', 'Low Stock Alerts')
		]
		
		for key, label in widgets:
			checkbox = QtWidgets.QCheckBox(label)
			checkbox.setChecked(self.preferences.get(key, {}).get('visible', True))
			layout.addWidget(checkbox)
			self.checkboxes[key] = checkbox
		
		layout.addStretch()
		
		# Buttons
		buttons = QtWidgets.QHBoxLayout()
		ok_btn = QtWidgets.QPushButton('OK')
		ok_btn.clicked.connect(self.accept)
		cancel_btn = QtWidgets.QPushButton('Cancel')
		cancel_btn.clicked.connect(self.reject)
		buttons.addWidget(ok_btn)
		buttons.addWidget(cancel_btn)
		layout.addLayout(buttons)

	def get_preferences(self) -> dict:
		"""Get updated preferences from checkboxes."""
		for key, checkbox in self.checkboxes.items():
			if key not in self.preferences:
				self.preferences[key] = {}
			self.preferences[key]['visible'] = checkbox.isChecked()
		return self.preferences

