import os
import sqlite3
import hashlib
import secrets
from typing import Any, Dict, List, Optional, Tuple


class Database:
	_connection: Optional[sqlite3.Connection] = None
	_db_path: Optional[str] = None

	@classmethod
	def initialize(cls, db_path: str, schema_path: str, sample_data_path: Optional[str] = None) -> None:
		cls._db_path = db_path
		file_exists = os.path.exists(db_path)
		file_has_size = file_exists and os.path.getsize(db_path) > 0
		conn = sqlite3.connect(db_path, check_same_thread=False)
		conn.row_factory = sqlite3.Row
		cls._connection = conn
		with conn:
			conn.execute('PRAGMA foreign_keys = ON;')
			# Determine if DB is fresh (no core tables)
			is_fresh = not file_exists or not file_has_size
			if not is_fresh:
				row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'").fetchone()
				is_fresh = row is None

			if is_fresh and os.path.exists(schema_path):
				with open(schema_path, 'r', encoding='utf-8') as f:
					conn.executescript(f.read())
				if sample_data_path and os.path.exists(sample_data_path):
					with open(sample_data_path, 'r', encoding='utf-8') as f:
						conn.executescript(f.read())

			# Always run migrations to bring existing DBs up to date
			cls._ensure_schema(conn)

	@classmethod
	def _ensure_schema(cls, conn: sqlite3.Connection) -> None:
		# ensure brands table exists
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS brands (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				name TEXT UNIQUE NOT NULL
			);
			"""
		)
		# ensure other_income table exists
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS other_income (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				description TEXT NOT NULL,
				category TEXT,
				amount REAL NOT NULL,
				received_on DATE NOT NULL,
				created_at DATETIME DEFAULT CURRENT_TIMESTAMP
			);
			"""
		)
		try:
			conn.execute('CREATE INDEX IF NOT EXISTS idx_other_income_received_on ON other_income(received_on)')
		except Exception:
			pass
		# ensure customers table exists and sales.customer_id column
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS customers (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				name TEXT,
				phone TEXT,
				created_at DATETIME DEFAULT CURRENT_TIMESTAMP
			);
			"""
		)
		# add sales.customer_id if missing
		sales_cols = {row['name'] for row in conn.execute("PRAGMA table_info(sales)").fetchall()} if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sales'").fetchone() else set()
		if 'customer_id' not in sales_cols:
			try:
				conn.execute('ALTER TABLE sales ADD COLUMN customer_id INTEGER')
			except Exception:
				pass
		try:
			conn.execute('CREATE INDEX IF NOT EXISTS idx_sales_customer_id ON sales(customer_id)')
		except Exception:
			pass
		# ensure products optional columns exist
		pcols = {row['name'] for row in conn.execute("PRAGMA table_info(products)").fetchall()} if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'").fetchone() else set()
		if 'products' not in {r['name'] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}:
			return
		if 'brand' not in pcols:
			conn.execute('ALTER TABLE products ADD COLUMN brand TEXT')
		if 'brand_id' not in pcols:
			conn.execute('ALTER TABLE products ADD COLUMN brand_id INTEGER')
		# migrate legacy text brand into brands/brand_id
		rows = conn.execute("SELECT id, brand FROM products WHERE brand IS NOT NULL AND brand <> '' AND (brand_id IS NULL OR brand_id='')").fetchall()
		for r in rows:
			bname = (r['brand'] or '').strip()
			if not bname:
				continue
			conn.execute('INSERT OR IGNORE INTO brands (name) VALUES (?)', (bname,))
			brow = conn.execute('SELECT id FROM brands WHERE name=?', (bname,)).fetchone()
			if brow:
				conn.execute('UPDATE products SET brand_id=? WHERE id=?', (brow['id'], r['id']))
		# safe indexes (create if column exists)
		try:
			conn.execute('CREATE INDEX IF NOT EXISTS idx_products_brand_id ON products(brand_id)')
		except Exception:
			pass
		try:
			conn.execute('CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id)')
		except Exception:
			pass
		# ensure expenses.payment_type column exists
		if 'expenses' in {r['name'] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}:
			exp_cols = {row['name'] for row in conn.execute("PRAGMA table_info(expenses)").fetchall()}
			if 'payment_type' not in exp_cols:
				try:
					conn.execute('ALTER TABLE expenses ADD COLUMN payment_type TEXT NOT NULL DEFAULT "Cash"')
				except Exception:
					pass
		# ensure purchases and purchase_items tables exist
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS purchases (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				bill_id TEXT UNIQUE NOT NULL,
				total_amount REAL NOT NULL,
				supplier_name TEXT,
				payment_type TEXT NOT NULL,
				paid_amount REAL NOT NULL,
				user_id INTEGER,
				created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
				FOREIGN KEY (user_id) REFERENCES users(id)
			);
			"""
		)
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS purchase_items (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				purchase_id INTEGER NOT NULL,
				product_id INTEGER NOT NULL,
				quantity INTEGER NOT NULL,
				unit_cost REAL NOT NULL,
				line_total REAL NOT NULL,
				FOREIGN KEY (purchase_id) REFERENCES purchases(id) ON DELETE CASCADE,
				FOREIGN KEY (product_id) REFERENCES products(id)
			);
			"""
		)
		try:
			conn.execute('CREATE INDEX IF NOT EXISTS idx_purchases_created_at ON purchases(created_at)')
		except Exception:
			pass
		try:
			conn.execute('CREATE INDEX IF NOT EXISTS idx_purchase_items_purchase_id ON purchase_items(purchase_id)')
		except Exception:
			pass
		# ensure bank_transactions table exists
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS bank_transactions (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				transaction_type TEXT CHECK(transaction_type IN ('Deposit', 'Withdrawal')) NOT NULL,
				amount REAL NOT NULL,
				description TEXT,
				user_id INTEGER,
				created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
				FOREIGN KEY (user_id) REFERENCES users(id)
			);
			"""
		)
		try:
			conn.execute('CREATE INDEX IF NOT EXISTS idx_bank_transactions_created_at ON bank_transactions(created_at)')
		except Exception:
			pass
		# Ensure settings table exists
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS settings (
				key TEXT PRIMARY KEY,
				value TEXT NOT NULL,
				updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
			);
			"""
		)

	@classmethod
	def connection(cls) -> sqlite3.Connection:
		if cls._connection is None:
			raise RuntimeError('Database not initialized')
		return cls._connection

	# Password hashing using PBKDF2-HMAC-SHA256
	@staticmethod
	def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
		if salt is None:
			salt = secrets.token_bytes(16)
		dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 200_000)
		return salt.hex(), dk.hex()

	@staticmethod
	def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
		salt = bytes.fromhex(salt_hex)
		dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 200_000)
		return secrets.compare_digest(dk.hex(), hash_hex)

	@classmethod
	def ensure_default_admin(cls) -> None:
		conn = cls.connection()
		row = conn.execute('SELECT * FROM users WHERE username=?', ('admin',)).fetchone()
		if row is None:
			salt, pwd = cls.hash_password('admin123')
			conn.execute('INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)', ('admin', f'{salt}:{pwd}', 'admin'))
			return
		# If present but has placeholder/invalid hash, reset to admin123
		ph = str(row['password_hash'] or '')
		needs_reset = False
		if ':' not in ph:
			needs_reset = True
		elif ph == 'PLACEHOLDER_HASH_WILL_BE_SET_BY_APP':
			needs_reset = True
		else:
			try:
				salt_hex, hash_hex = ph.split(':', 1)
				if not cls.verify_password('admin123', salt_hex, hash_hex):
					needs_reset = True
			except Exception:
				needs_reset = True
		if needs_reset:
			salt, pwd = cls.hash_password('admin123')
			conn.execute('UPDATE users SET password_hash=?, role=? WHERE id=?', (f'{salt}:{pwd}', 'admin', row['id']))

	# Users
	@classmethod
	def authenticate_user(cls, username: str, password: str) -> Optional[Dict[str, Any]]:
		conn = cls.connection()
		row = conn.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
		if not row:
			return None
		try:
			salt_hex, hash_hex = str(row['password_hash']).split(':', 1)
		except Exception:
			return None
		if cls.verify_password(password, salt_hex, hash_hex):
			return dict(row)
		return None

	@classmethod
	def list_users(cls) -> List[Dict[str, Any]]:
		cur = cls.connection().execute('SELECT id, username, role, created_at FROM users ORDER BY username')
		return [dict(r) for r in cur.fetchall()]

	@classmethod
	def create_user(cls, username: str, password: str, role: str) -> int:
		salt, pwd = cls.hash_password(password)
		with cls.connection() as conn:
			cur = conn.execute(
				'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
				(username, f'{salt}:{pwd}', role)
			)
			return cur.lastrowid

	@classmethod
	def update_user_password(cls, user_id: int, new_password: str) -> None:
		salt, pwd = cls.hash_password(new_password)
		with cls.connection() as conn:
			conn.execute('UPDATE users SET password_hash=? WHERE id=?', (f'{salt}:{pwd}', user_id))

	@classmethod
	def delete_user(cls, user_id: int) -> None:
		with cls.connection() as conn:
			conn.execute('DELETE FROM users WHERE id=?', (user_id,))

	# Categories
	@classmethod
	def list_categories(cls) -> List[Dict[str, Any]]:
		cur = cls.connection().execute('SELECT id, name FROM categories ORDER BY name')
		return [dict(r) for r in cur.fetchall()]

	@classmethod
	def create_category(cls, name: str) -> int:
		with cls.connection() as conn:
			cur = conn.execute('INSERT INTO categories (name) VALUES (?)', (name.strip(),))
			return cur.lastrowid

	@classmethod
	def update_category(cls, category_id: int, name: str) -> None:
		with cls.connection() as conn:
			conn.execute('UPDATE categories SET name=? WHERE id=?', (name.strip(), category_id))

	@classmethod
	def delete_category(cls, category_id: int) -> None:
		with cls.connection() as conn:
			conn.execute('DELETE FROM categories WHERE id=?', (category_id,))

	# Brands
	@classmethod
	def list_brands(cls) -> List[Dict[str, Any]]:
		cur = cls.connection().execute('SELECT id, name FROM brands ORDER BY name')
		return [dict(r) for r in cur.fetchall()]

	@classmethod
	def create_brand(cls, name: str) -> int:
		with cls.connection() as conn:
			cur = conn.execute('INSERT INTO brands (name) VALUES (?)', (name.strip(),))
			return cur.lastrowid

	@classmethod
	def update_brand(cls, brand_id: int, name: str) -> None:
		with cls.connection() as conn:
			conn.execute('UPDATE brands SET name=? WHERE id=?', (name.strip(), brand_id))

	@classmethod
	def delete_brand(cls, brand_id: int) -> None:
		conn = cls.connection()
		with conn:
			brow = conn.execute('SELECT name FROM brands WHERE id=?', (brand_id,)).fetchone()
			bname = brow['name'] if brow else None
			if bname:
				# preserve human-readable brand text for affected products
				conn.execute('UPDATE products SET brand=IFNULL(brand, ?), brand_id=NULL WHERE brand_id=?', (bname, brand_id))
			else:
				conn.execute('UPDATE products SET brand_id=NULL WHERE brand_id=?', (brand_id,))
			conn.execute('DELETE FROM brands WHERE id=?', (brand_id,))

	# Products
	@classmethod
	def search_products(cls, query: str) -> List[Dict[str, Any]]:
		q = f'%{query.strip()}%'
		cur = cls.connection().execute(
			"""
			SELECT p.*, c.name AS category_name, b.name AS brand_name
			FROM products p
			LEFT JOIN categories c ON c.id = p.category_id
			LEFT JOIN brands b ON b.id = p.brand_id
			WHERE p.name LIKE ? OR p.barcode LIKE ? OR IFNULL(b.name,'') LIKE ? OR IFNULL(p.brand,'') LIKE ?
			ORDER BY p.name
			""",
			(q, q, q, q)
		)
		return [dict(r) for r in cur.fetchall()]

	@classmethod
	def get_product_by_barcode(cls, barcode: str) -> Optional[Dict[str, Any]]:
		row = cls.connection().execute('SELECT * FROM products WHERE barcode=?', (barcode,)).fetchone()
		return dict(row) if row else None

	@classmethod
	def list_products(cls) -> List[Dict[str, Any]]:
		cur = cls.connection().execute(
			'SELECT p.*, c.name AS category_name, b.name AS brand_name FROM products p LEFT JOIN categories c ON c.id=p.category_id LEFT JOIN brands b ON b.id=p.brand_id ORDER BY p.name'
		)
		return [dict(r) for r in cur.fetchall()]

	@classmethod
	def create_product(cls, name: str, category_id: Optional[int], description: str, price: float, cost_price: float, stock_quantity: int, barcode: Optional[str], low_stock_threshold: int, brand: Optional[str] = None, brand_id: Optional[int] = None) -> int:
		with cls.connection() as conn:
			cur = conn.execute(
				'INSERT INTO products (name, brand, brand_id, category_id, description, price, cost_price, stock_quantity, barcode, low_stock_threshold) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
				(name, brand, brand_id, category_id, description, price, cost_price, stock_quantity, barcode, low_stock_threshold)
			)
			return cur.lastrowid

	@classmethod
	def update_product(cls, product_id: int, name: str, category_id: Optional[int], description: str, price: float, cost_price: float, stock_quantity: int, barcode: Optional[str], low_stock_threshold: int, brand: Optional[str] = None, brand_id: Optional[int] = None) -> None:
		with cls.connection() as conn:
			conn.execute(
				'UPDATE products SET name=?, brand=?, brand_id=?, category_id=?, description=?, price=?, cost_price=?, stock_quantity=?, barcode=?, low_stock_threshold=? WHERE id=?',
				(name, brand, brand_id, category_id, description, price, cost_price, stock_quantity, barcode, low_stock_threshold, product_id)
			)

	@classmethod
	def delete_product(cls, product_id: int) -> None:
		with cls.connection() as conn:
			conn.execute('DELETE FROM products WHERE id=?', (product_id,))

	@classmethod
	def low_stock_products(cls) -> List[Dict[str, Any]]:
		cur = cls.connection().execute('SELECT id, name, stock_quantity, low_stock_threshold FROM products WHERE stock_quantity <= low_stock_threshold ORDER BY name')
		return [dict(r) for r in cur.fetchall()]

	# Sales
	@classmethod
	def next_invoice_id(cls) -> str:
		prefix = cls.get_setting('invoice_prefix', 'INV')
		row = cls.connection().execute('SELECT COUNT(*) AS c FROM sales').fetchone()
		count = (row['c'] if row else 0) + 1
		return f'{prefix}{count:06d}'

	@classmethod
	def create_sale(cls, user_id: int, items: List[Dict[str, Any]], discount_amount: float, payment_type: str, paid_amount: float, change_amount: float, customer_id: Optional[int] = None) -> str:
		conn = cls.connection()
		invoice_id = cls.next_invoice_id()
		with conn:
			cur = conn.execute(
				'INSERT INTO sales (invoice_id, total_amount, discount_amount, payment_type, paid_amount, change_amount, user_id, customer_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
				(invoice_id, sum(i['line_total'] for i in items), discount_amount, payment_type, paid_amount, change_amount, user_id, customer_id)
			)
			sale_id = cur.lastrowid
			for it in items:
				conn.execute(
					'INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, discount, line_total) VALUES (?, ?, ?, ?, ?, ?)',
					(sale_id, it['product_id'], it['quantity'], it['unit_price'], it.get('discount', 0.0), it['line_total'])
				)
				conn.execute('UPDATE products SET stock_quantity = stock_quantity - ? WHERE id=?', (it['quantity'], it['product_id']))
		return invoice_id

	# Customers
	@classmethod
	def upsert_customer(cls, name: Optional[str], phone: Optional[str]) -> Optional[int]:
		name = (name or '').strip()
		phone = (phone or '').strip()
		if not name and not phone:
			return None
		conn = cls.connection()
		with conn:
			row = None
			if phone:
				row = conn.execute('SELECT id FROM customers WHERE phone=?', (phone,)).fetchone()
			if row:
				cid = row['id']
				if name:
					conn.execute('UPDATE customers SET name=? WHERE id=?', (name, cid))
				return cid
			cur = conn.execute('INSERT INTO customers (name, phone) VALUES (?, ?)', (name or None, phone or None))
			return cur.lastrowid

	@classmethod
	def list_customers(cls) -> List[Dict[str, Any]]:
		cur = cls.connection().execute('SELECT id, name, phone, created_at FROM customers ORDER BY datetime(created_at) DESC')
		return [dict(r) for r in cur.fetchall()]

	@classmethod
	def update_customer(cls, customer_id: int, name: Optional[str], phone: Optional[str]) -> None:
		with cls.connection() as conn:
			conn.execute('UPDATE customers SET name=?, phone=? WHERE id=?', ((name or '').strip() or None, (phone or '').strip() or None, customer_id))

	@classmethod
	def delete_customer(cls, customer_id: int) -> None:
		with cls.connection() as conn:
			conn.execute('DELETE FROM customers WHERE id=?', (customer_id,))

	@classmethod
	def customer_details_report(cls) -> List[Dict[str, Any]]:
		cur = cls.connection().execute(
			"""
			SELECT 
				c.id,
				c.name,
				c.phone,
				IFNULL(SUM(s.total_amount), 0) AS total_sales,
				COUNT(s.id) AS invoice_count,
				MAX(s.created_at) AS last_purchase
			FROM customers c
			LEFT JOIN sales s ON s.customer_id = c.id
			GROUP BY c.id, c.name, c.phone
			HAVING invoice_count > 0
			ORDER BY total_sales DESC
			"""
		)
		return [dict(r) for r in cur.fetchall()]

	# Reports
	@classmethod
	def daily_totals(cls) -> Dict[str, float]:
		row = cls.connection().execute("SELECT IFNULL(SUM(total_amount),0) AS total, IFNULL(SUM(discount_amount),0) AS discount FROM sales WHERE DATE(created_at)=DATE('now','localtime')").fetchone()
		return {'total': float(row['total']), 'discount': float(row['discount'])}

	@classmethod
	def sales_summary(cls, period: str) -> List[Dict[str, Any]]:
		if period == 'daily':
			q = "SELECT DATE(created_at) d, SUM(total_amount) t FROM sales GROUP BY d ORDER BY d DESC LIMIT 31"
		elif period == 'monthly':
			q = "SELECT STRFTIME('%Y-%m', created_at) d, SUM(total_amount) t FROM sales GROUP BY d ORDER BY d DESC LIMIT 24"
		else:
			q = "SELECT STRFTIME('%Y', created_at) d, SUM(total_amount) t FROM sales GROUP BY d ORDER BY d DESC"
		cur = cls.connection().execute(q)
		return [{'period': r['d'], 'total': r['t']} for r in cur.fetchall()]

	@classmethod
	def top_products(cls, limit: int = 10) -> List[Dict[str, Any]]:
		cur = cls.connection().execute(
			"""
			SELECT p.name, SUM(si.quantity) qty, SUM(si.line_total) revenue
			FROM sale_items si
			JOIN products p ON p.id = si.product_id
			GROUP BY p.id
			ORDER BY qty DESC
			LIMIT ?
			""",
			(limit,)
		)
		return [dict(r) for r in cur.fetchall()]

	@classmethod
	def inventory_report(cls) -> List[Dict[str, Any]]:
		cur = cls.connection().execute('SELECT name, IFNULL((SELECT name FROM brands WHERE id=brand_id), brand) AS brand, stock_quantity, price, cost_price FROM products ORDER BY name')
		return [dict(r) for r in cur.fetchall()]

	# Expenses
	@classmethod
	def add_expense(cls, description: str, category: str, amount: float, incurred_on: str, payment_type: str = 'Cash') -> int:
		with cls.connection() as conn:
			cur = conn.execute('INSERT INTO expenses (description, category, amount, incurred_on, payment_type) VALUES (?, ?, ?, ?, ?)', (description, category, amount, incurred_on, payment_type))
			return cur.lastrowid

	@classmethod
	def monthly_expense_summary(cls) -> List[Dict[str, Any]]:
		cur = cls.connection().execute("SELECT STRFTIME('%Y-%m', incurred_on) m, SUM(amount) total FROM expenses GROUP BY m ORDER BY m DESC LIMIT 24")
		return [{'month': r['m'], 'total': r['total']} for r in cur.fetchall()]

	# Other Income
	@classmethod
	def add_other_income(cls, description: str, category: str, amount: float, received_on: str) -> int:
		with cls.connection() as conn:
			cur = conn.execute('INSERT INTO other_income (description, category, amount, received_on) VALUES (?, ?, ?, ?)', (description, category, amount, received_on))
			return cur.lastrowid

	@classmethod
	def monthly_income_summary(cls) -> List[Dict[str, Any]]:
		cur = cls.connection().execute("SELECT STRFTIME('%Y-%m', received_on) m, SUM(amount) total FROM other_income GROUP BY m ORDER BY m DESC LIMIT 24")
		return [{'month': r['m'], 'total': r['total']} for r in cur.fetchall()]

	@classmethod
	def category_sales_summary(cls) -> List[Dict[str, Any]]:
		q = """
		SELECT IFNULL(c.name,'Uncategorized') AS category,
		       SUM(si.quantity * si.unit_price - si.discount) AS revenue,
		       SUM(si.quantity * p.cost_price) AS cogs,
		       COUNT(DISTINCT s.id) AS invoices
		FROM sale_items si
		JOIN sales s ON s.id = si.sale_id
		JOIN products p ON p.id = si.product_id
		LEFT JOIN categories c ON c.id = p.category_id
		GROUP BY category
		ORDER BY revenue DESC
		"""
		cur = cls.connection().execute(q)
		return [dict(r) for r in cur.fetchall()]

	@classmethod
	def profit_report(cls, period: str = 'monthly') -> List[Dict[str, Any]]:
		# Aggregate revenue and COGS by period, then subtract expenses for same period
		if period == 'daily':
			date_expr = "DATE(s.created_at)"
			exp_expr = "STRFTIME('%Y-%m-%d', incurred_on)"
			inc_expr = "STRFTIME('%Y-%m-%d', received_on)"
		elif period == 'yearly':
			date_expr = "STRFTIME('%Y', s.created_at)"
			exp_expr = "STRFTIME('%Y', incurred_on)"
			inc_expr = "STRFTIME('%Y', received_on)"
		else:
			date_expr = "STRFTIME('%Y-%m', s.created_at)"
			exp_expr = "STRFTIME('%Y-%m', incurred_on)"
			inc_expr = "STRFTIME('%Y-%m', received_on)"
		rev_q = f"""
		SELECT {date_expr} AS p, 
		       SUM(si.quantity * si.unit_price - si.discount) AS revenue,
		       SUM(si.quantity * p.cost_price) AS cogs
		FROM sale_items si
		JOIN sales s ON s.id = si.sale_id
		JOIN products p ON p.id = si.product_id
		GROUP BY p
		ORDER BY p DESC
		"""
		exp_q = f"SELECT {exp_expr} AS p, SUM(amount) AS expenses FROM expenses GROUP BY p"
		inc_q = f"SELECT {inc_expr} AS p, SUM(amount) AS income FROM other_income GROUP BY p"
		conn = cls.connection()
		rev_rows = {r['p']: {'revenue': r['revenue'] or 0.0, 'cogs': r['cogs'] or 0.0} for r in conn.execute(rev_q).fetchall()}
		exp_rows = {r['p']: (r['expenses'] or 0.0) for r in conn.execute(exp_q).fetchall()}
		inc_rows = {r['p']: (r['income'] or 0.0) for r in conn.execute(inc_q).fetchall()}
		all_periods = set(rev_rows.keys()) | set(exp_rows.keys()) | set(inc_rows.keys())
		result = []
		for key in sorted(all_periods, reverse=True):
			rev = float(rev_rows.get(key, {}).get('revenue', 0.0))
			cogs = float(rev_rows.get(key, {}).get('cogs', 0.0))
			exp = float(exp_rows.get(key, 0.0))
			inc = float(inc_rows.get(key, 0.0))
			profit = rev - cogs - exp + inc
			result.append({'period': key, 'revenue': rev, 'cogs': cogs, 'expenses': exp, 'other_income': inc, 'profit': profit})
		return result

	# Cashbook
	@classmethod
	def cashbook_report(cls) -> Dict[str, Any]:
		conn = cls.connection()
		# Cash sales (where payment_type = 'Cash')
		cash_sales_row = conn.execute(
			"SELECT IFNULL(SUM(paid_amount), 0) AS total FROM sales WHERE payment_type = 'Cash'"
		).fetchone()
		cash_sales = float(cash_sales_row['total'] if cash_sales_row else 0.0)
		
		# Other income (assuming all is cash)
		income_row = conn.execute("SELECT IFNULL(SUM(amount), 0) AS total FROM other_income").fetchone()
		other_income = float(income_row['total'] if income_row else 0.0)
		
		# Cash expenses (where payment_type = 'Cash')
		cash_expenses_row = conn.execute(
			"SELECT IFNULL(SUM(amount), 0) AS total FROM expenses WHERE payment_type = 'Cash'"
		).fetchone()
		cash_expenses = float(cash_expenses_row['total'] if cash_expenses_row else 0.0)
		
		# Total expenses (all payment types)
		expenses_row = conn.execute("SELECT IFNULL(SUM(amount), 0) AS total FROM expenses").fetchone()
		total_expenses = float(expenses_row['total'] if expenses_row else 0.0)
		
		# Cash purchases (where payment_type = 'Cash')
		cash_purchases_row = conn.execute(
			"SELECT IFNULL(SUM(paid_amount), 0) AS total FROM purchases WHERE payment_type = 'Cash'"
		).fetchone()
		cash_purchases = float(cash_purchases_row['total'] if cash_purchases_row else 0.0)
		
		# Bank deposits (cash to bank) - reduces cash
		deposits_row = conn.execute(
			"SELECT IFNULL(SUM(amount), 0) AS total FROM bank_transactions WHERE transaction_type = 'Deposit'"
		).fetchone()
		deposits = float(deposits_row['total'] if deposits_row else 0.0)
		
		# Bank withdrawals (bank to cash) - increases cash
		withdrawals_row = conn.execute(
			"SELECT IFNULL(SUM(amount), 0) AS total FROM bank_transactions WHERE transaction_type = 'Withdrawal'"
		).fetchone()
		withdrawals = float(withdrawals_row['total'] if withdrawals_row else 0.0)
		
		# Total cash received
		total_received = cash_sales + other_income + withdrawals
		
		# Total cash paid out (cash expenses, cash purchases, and deposits)
		total_paid_out = cash_expenses + cash_purchases + deposits
		
		# Net cash balance
		net_cash = total_received - total_paid_out
		
		return {
			'cash_sales': cash_sales,
			'other_income': other_income,
			'withdrawals': withdrawals,
			'total_received': total_received,
			'cash_expenses': cash_expenses,
			'total_expenses': total_expenses,
			'cash_purchases': cash_purchases,
			'deposits': deposits,
			'total_paid_out': total_paid_out,
			'net_cash': net_cash
		}

	# Purchases
	@classmethod
	def next_bill_id(cls) -> str:
		prefix = cls.get_setting('bill_prefix', 'BILL')
		row = cls.connection().execute('SELECT COUNT(*) AS c FROM purchases').fetchone()
		count = (row['c'] if row else 0) + 1
		return f'{prefix}{count:06d}'

	@classmethod
	def create_purchase(cls, user_id: int, items: List[Dict[str, Any]], supplier_name: Optional[str], payment_type: str, paid_amount: float) -> str:
		conn = cls.connection()
		bill_id = cls.next_bill_id()
		total_amount = sum(i['line_total'] for i in items)
		with conn:
			cur = conn.execute(
				'INSERT INTO purchases (bill_id, total_amount, supplier_name, payment_type, paid_amount, user_id) VALUES (?, ?, ?, ?, ?, ?)',
				(bill_id, total_amount, supplier_name, payment_type, paid_amount, user_id)
			)
			purchase_id = cur.lastrowid
			for it in items:
				conn.execute(
					'INSERT INTO purchase_items (purchase_id, product_id, quantity, unit_cost, line_total) VALUES (?, ?, ?, ?, ?)',
					(purchase_id, it['product_id'], it['quantity'], it['unit_cost'], it['line_total'])
				)
				# Update product stock (increase) and cost_price (if different)
				conn.execute('UPDATE products SET stock_quantity = stock_quantity + ? WHERE id=?', (it['quantity'], it['product_id']))
				# Update cost_price to the latest purchase cost
				conn.execute('UPDATE products SET cost_price = ? WHERE id=?', (it['unit_cost'], it['product_id']))
		return bill_id

	@classmethod
	def list_purchases(cls, limit: int = 100) -> List[Dict[str, Any]]:
		cur = cls.connection().execute(
			'SELECT p.*, u.username FROM purchases p LEFT JOIN users u ON u.id = p.user_id ORDER BY p.created_at DESC LIMIT ?',
			(limit,)
		)
		return [dict(r) for r in cur.fetchall()]

	@classmethod
	def get_purchase(cls, purchase_id: int) -> Optional[Dict[str, Any]]:
		row = cls.connection().execute(
			'SELECT p.*, u.username FROM purchases p LEFT JOIN users u ON u.id = p.user_id WHERE p.id=?',
			(purchase_id,)
		).fetchone()
		return dict(row) if row else None

	@classmethod
	def get_purchase_items(cls, purchase_id: int) -> List[Dict[str, Any]]:
		cur = cls.connection().execute(
			"""
			SELECT pi.*, pr.name AS product_name, pr.barcode
			FROM purchase_items pi
			JOIN products pr ON pr.id = pi.product_id
			WHERE pi.purchase_id = ?
			ORDER BY pi.id
			""",
			(purchase_id,)
		)
		return [dict(r) for r in cur.fetchall()]

	@classmethod
	def purchases_summary(cls, period: str) -> List[Dict[str, Any]]:
		if period == 'daily':
			q = "SELECT DATE(created_at) d, SUM(total_amount) t, COUNT(*) c FROM purchases GROUP BY d ORDER BY d DESC LIMIT 31"
		elif period == 'monthly':
			q = "SELECT STRFTIME('%Y-%m', created_at) d, SUM(total_amount) t, COUNT(*) c FROM purchases GROUP BY d ORDER BY d DESC LIMIT 24"
		else:
			q = "SELECT STRFTIME('%Y', created_at) d, SUM(total_amount) t, COUNT(*) c FROM purchases GROUP BY d ORDER BY d DESC"
		cur = cls.connection().execute(q)
		return [{'period': r['d'], 'total': r['t'] or 0.0, 'count': r['c'] or 0} for r in cur.fetchall()]

	@classmethod
	def top_purchased_products(cls, limit: int = 10) -> List[Dict[str, Any]]:
		cur = cls.connection().execute(
			"""
			SELECT p.name, SUM(pi.quantity) qty, SUM(pi.line_total) total_cost
			FROM purchase_items pi
			JOIN products p ON p.id = pi.product_id
			GROUP BY p.id
			ORDER BY qty DESC
			LIMIT ?
			""",
			(limit,)
		)
		return [dict(r) for r in cur.fetchall()]

	@classmethod
	def supplier_summary(cls) -> List[Dict[str, Any]]:
		cur = cls.connection().execute(
			"""
			SELECT 
				IFNULL(supplier_name, 'Unknown') AS supplier,
				SUM(total_amount) AS total,
				COUNT(*) AS count
			FROM purchases
			GROUP BY supplier_name
			ORDER BY total DESC
			"""
		)
		return [dict(r) for r in cur.fetchall()]

	# Bank Transactions
	@classmethod
	def add_bank_transaction(cls, user_id: int, transaction_type: str, amount: float, description: Optional[str] = None) -> int:
		with cls.connection() as conn:
			cur = conn.execute(
				'INSERT INTO bank_transactions (transaction_type, amount, description, user_id) VALUES (?, ?, ?, ?)',
				(transaction_type, amount, description, user_id)
			)
			return cur.lastrowid

	@classmethod
	def list_bank_transactions(cls, limit: int = 200) -> List[Dict[str, Any]]:
		cur = cls.connection().execute(
			'SELECT bt.*, u.username FROM bank_transactions bt LEFT JOIN users u ON u.id = bt.user_id ORDER BY bt.created_at DESC LIMIT ?',
			(limit,)
		)
		return [dict(r) for r in cur.fetchall()]

	@classmethod
	def bankbook_report(cls) -> Dict[str, Any]:
		conn = cls.connection()
		# Card sales (where payment_type IN ('Card', 'QR', etc.))
		card_sales_row = conn.execute(
			"SELECT IFNULL(SUM(paid_amount), 0) AS total FROM sales WHERE payment_type IN ('Card', 'QR', 'Other')"
		).fetchone()
		card_sales = float(card_sales_row['total'] if card_sales_row else 0.0)
		
		# Card purchases (where payment_type IN ('Card', 'Cheque', 'Credit', etc.))
		card_purchases_row = conn.execute(
			"SELECT IFNULL(SUM(paid_amount), 0) AS total FROM purchases WHERE payment_type IN ('Card', 'Cheque', 'Credit', 'Other')"
		).fetchone()
		card_purchases = float(card_purchases_row['total'] if card_purchases_row else 0.0)
		
		# Card expenses (where payment_type IN ('Card', 'Cheque', 'Credit', etc.))
		card_expenses_row = conn.execute(
			"SELECT IFNULL(SUM(amount), 0) AS total FROM expenses WHERE payment_type IN ('Card', 'Cheque', 'Credit', 'Other')"
		).fetchone()
		card_expenses = float(card_expenses_row['total'] if card_expenses_row else 0.0)
		
		# Deposits (cash to bank)
		deposits_row = conn.execute(
			"SELECT IFNULL(SUM(amount), 0) AS total FROM bank_transactions WHERE transaction_type = 'Deposit'"
		).fetchone()
		deposits = float(deposits_row['total'] if deposits_row else 0.0)
		
		# Withdrawals (bank to cash)
		withdrawals_row = conn.execute(
			"SELECT IFNULL(SUM(amount), 0) AS total FROM bank_transactions WHERE transaction_type = 'Withdrawal'"
		).fetchone()
		withdrawals = float(withdrawals_row['total'] if withdrawals_row else 0.0)
		
		# Total bank received
		total_received = card_sales + deposits
		
		# Total bank paid out
		total_paid_out = card_purchases + card_expenses + withdrawals
		
		# Net bank balance
		net_bank = total_received - total_paid_out
		
		return {
			'card_sales': card_sales,
			'deposits': deposits,
			'total_received': total_received,
			'card_purchases': card_purchases,
			'card_expenses': card_expenses,
			'withdrawals': withdrawals,
			'total_paid_out': total_paid_out,
			'net_bank': net_bank
		}

	# Settings
	@classmethod
	def get_setting(cls, key: str, default: str = '') -> str:
		row = cls.connection().execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
		return row['value'] if row else default

	@classmethod
	def set_setting(cls, key: str, value: str) -> None:
		with cls.connection() as conn:
			conn.execute(
				'INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)',
				(key, value)
			)

	@classmethod
	def get_all_settings(cls) -> Dict[str, str]:
		cur = cls.connection().execute('SELECT key, value FROM settings')
		return {row['key']: row['value'] for row in cur.fetchall()}

	# Dashboard Widgets Data
	@classmethod
	def _get_date_filter(cls, period: str) -> str:
		"""Get SQL date filter based on period."""
		if period == 'today':
			return "DATE(created_at) = DATE('now', 'localtime')"
		elif period == 'week':
			return "DATE(created_at) >= DATE('now', 'localtime', '-7 days')"
		elif period == 'month':
			return "DATE(created_at) >= DATE('now', 'localtime', 'start of month')"
		elif period == 'year':
			return "DATE(created_at) >= DATE('now', 'localtime', 'start of year')"
		else:  # all_time
			return "1=1"  # All records

	@classmethod
	def sales_by_time_period(cls, period: str = 'today') -> List[Dict[str, Any]]:
		"""Get sales data grouped by time unit based on period, for chart."""
		date_filter = cls._get_date_filter(period)
		
		if period == 'today':
			# Group by hour for today
			query = f"""
				SELECT 
					STRFTIME('%H', created_at) AS time_unit,
					IFNULL(SUM(total_amount), 0) AS total
				FROM sales
				WHERE {date_filter}
				GROUP BY time_unit
				ORDER BY time_unit
			"""
		elif period == 'week':
			# Group by day for week
			query = f"""
				SELECT 
					DATE(created_at) AS time_unit,
					IFNULL(SUM(total_amount), 0) AS total
				FROM sales
				WHERE {date_filter}
				GROUP BY time_unit
				ORDER BY time_unit
			"""
		elif period == 'month':
			# Group by day for month
			query = f"""
				SELECT 
					DATE(created_at) AS time_unit,
					IFNULL(SUM(total_amount), 0) AS total
				FROM sales
				WHERE {date_filter}
				GROUP BY time_unit
				ORDER BY time_unit
			"""
		elif period == 'year':
			# Group by month for year
			query = f"""
				SELECT 
					STRFTIME('%Y-%m', created_at) AS time_unit,
					IFNULL(SUM(total_amount), 0) AS total
				FROM sales
				WHERE {date_filter}
				GROUP BY time_unit
				ORDER BY time_unit
			"""
		else:  # all_time
			# Group by month for all time
			query = f"""
				SELECT 
					STRFTIME('%Y-%m', created_at) AS time_unit,
					IFNULL(SUM(total_amount), 0) AS total
				FROM sales
				WHERE {date_filter}
				GROUP BY time_unit
				ORDER BY time_unit
			"""
		
		cur = cls.connection().execute(query)
		return [dict(r) for r in cur.fetchall()]

	@classmethod
	def summary_stats(cls, period: str = 'today') -> Dict[str, Any]:
		"""Get summary statistics for the selected period."""
		date_filter = cls._get_date_filter(period)
		# For sales table queries, 'created_at' is already correct (no join needed)
		conn = cls.connection()
		
		# Revenue
		revenue_row = conn.execute(
			f"SELECT IFNULL(SUM(total_amount), 0) AS total FROM sales WHERE {date_filter}"
		).fetchone()
		revenue = float(revenue_row['total'] if revenue_row else 0.0)
		
		# Transactions count
		transactions_row = conn.execute(
			f"SELECT COUNT(*) AS count FROM sales WHERE {date_filter}"
		).fetchone()
		transactions = int(transactions_row['count'] if transactions_row else 0)
		
		# Customers count (unique)
		customers_row = conn.execute(
			f"""
			SELECT COUNT(DISTINCT customer_id) AS count 
			FROM sales 
			WHERE {date_filter} AND customer_id IS NOT NULL
			"""
		).fetchone()
		customers = int(customers_row['count'] if customers_row else 0)
		
		# Average transaction value
		avg_transaction = revenue / transactions if transactions > 0 else 0.0
		
		# Discount total
		discount_row = conn.execute(
			f"SELECT IFNULL(SUM(discount_amount), 0) AS total FROM sales WHERE {date_filter}"
		).fetchone()
		discounts = float(discount_row['total'] if discount_row else 0.0)
		
		return {
			'revenue': revenue,
			'transactions': transactions,
			'customers': customers,
			'avg_transaction': avg_transaction,
			'discounts': discounts
		}

	@classmethod
	def top_products_by_period(cls, period: str = 'today', limit: int = 5) -> List[Dict[str, Any]]:
		"""Get top selling products for the selected period."""
		date_filter = cls._get_date_filter(period)
		# Replace 'created_at' with 's.created_at' to specify the table
		date_filter = date_filter.replace('created_at', 's.created_at')
		
		cur = cls.connection().execute(
			f"""
			SELECT 
				p.name,
				SUM(si.quantity) AS qty,
				SUM(si.line_total) AS revenue
			FROM sale_items si
			JOIN sales s ON s.id = si.sale_id
			JOIN products p ON p.id = si.product_id
			WHERE {date_filter}
			GROUP BY p.id
			ORDER BY qty DESC
			LIMIT ?
			""",
			(limit,)
		)
		return [dict(r) for r in cur.fetchall()]

