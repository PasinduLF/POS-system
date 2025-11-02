# Beauty P&C POS (Offline Desktop)

Offline desktop POS app for Windows.

Beauty P&C POS is a fully offline Point of Sale system for Windows, built with Python, PyQt5, and SQLite. It is designed for fast daily billing, inventory management, purchase tracking, and financial management in a retail shop.

## Features

### Core Features
- **User Management**: Login with Admin and Cashier roles
- **Product Management**: Add, edit, delete products with categories, brands, barcodes, cost prices, and selling prices
- **Product Variants**: Manage product variants with size, color, SKU, variant-specific barcodes, pricing, and stock
- **Stock Management**: Automatic stock tracking with low stock alerts (supports both products and variants)
- **POS Screen**: Fast checkout with search, barcode scanning, variant selection, cart, discounts, and multiple payment methods

### Sales & Customers
- **Sales Management**: View, edit, and delete sales transactions
- **Customer Management**: Track customers with purchase history
- **Customer Reports**: View customer details with sales statistics (total sales, invoice count, last purchase)
- **Sales Reports**: Daily, monthly, yearly sales summaries and category-wise analysis

### Purchases & Inventory
- **Purchase Management**: Record bulk purchases from suppliers with automatic stock updates
- **Purchase Reports**: Daily, monthly, yearly purchase summaries
- **Supplier Tracking**: Track suppliers with purchase history
- **Top Purchased Products**: Identify most purchased items
- **Inventory Reports**: Current stock levels with cost and selling price valuations

### Financial Management
- **Cashbook**: Track all cash transactions
  - Cash sales and other income
  - Cash expenses and cash purchases
  - Bank deposits (reduces cash)
  - Bank withdrawals (increases cash)
  - Net cash balance
- **Bankbook**: Track all bank/card transactions
  - Card sales (money into bank)
  - Card purchases and card expenses (money out of bank)
  - Deposits (cash to bank)
  - Withdrawals (bank to cash)
  - Net bank balance
- **Bank Transactions**: Record deposits and withdrawals between cash and bank
- **Expenses Tracking**: Record expenses with payment methods (Cash, Card, Cheque, Credit, Other)
- **Profit Reports**: Daily, monthly, yearly profit analysis with revenue, COGS, expenses, and net profit
- **Financial Reports**: Comprehensive financial summaries

### Reports
- Sales Reports (Daily, Monthly, Yearly, Category-wise, Top Products)
- Purchase Reports (Daily, Monthly, Yearly, Top Purchased, Supplier Summary)
- Financial Reports (Profit, Expenses, Income, Cashbook, Bankbook)
- Inventory Reports (Current Stock Levels)
- Customer Details Reports

### Additional Features
- **Product Variants Management**: 
  - Create variants with size, color, SKU, and unique barcodes
  - Variant-specific pricing and cost pricing
  - Individual stock tracking per variant
  - Low stock alerts for variants
  - Variant selection during sales and purchases
- **Thermal Receipt Printing**: ESC/POS or Windows printer support
- **PDF Invoice Generation**: Automatic PDF generation for sales
- **Export Functionality**: Export data to CSV/Excel
- **Backup & Restore**: Full database backup and restore functionality
- **Offline Operation**: All data stored locally in SQLite database

## Quick Start (Development)

1) Install Python 3.10+ (Windows)

2) Create venv and install requirements
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

3) Run the app (the schema is created automatically; no sample data is inserted)
```bash
python main.py
```

- Default admin login: admin / admin123 (change after first login)

Optional – load demo/sample data (do this only for testing; it will insert example products/brands/categories):
```bash
python -m sqlite3 database/beauty_pc.db ".read schema.sql"
python -m sqlite3 database/beauty_pc.db ".read sample_data.sql"
```

## Packaging to a Windows .exe (PyInstaller)
```bash
pyinstaller --noconsole --onefile --name "BeautyPC_POS" --icon assets/logo.ico main.py
```

- Place `assets/`, `database/`, and `schema.sql` next to the generated exe if using onefile.
- Alternatively, use `--add-data` to bundle assets and migrate to an app data folder on first run.

Example add-data use (PowerShell):
```bash
pyinstaller --noconsole --onefile --name "BeautyPC_POS" \
  --add-data "assets;assets" \
  --add-data "schema.sql;." \
  --add-data "sample_data.sql;." \
  main.py
```

## Hardware
- Barcode scanner: works as keyboard input in the search/barcode field
- Thermal printer: use ESC/POS (USB/Serial/Ethernet) or Windows printer (win32print)
- Optional cash drawer: supported via ESC/POS kick drawer command

## Backup & Restore
- Use the app menu: Backup to ZIP or export CSV/Excel
- Manual: copy the `database/beauty_pc.db` file to a safe location

## Project Structure
```
beauty_pc_pos/
├── main.py                    # Application entry point
├── database/
│   └── beauty_pc.db          # SQLite database
├── ui/
│   ├── login.py              # Login dialog
│   ├── dashboard.py          # Main dashboard window
│   ├── pos_screen.py         # Point of Sale screen
│   ├── products.py           # Product management with variants
│   ├── variant_selector.py   # Variant selection dialog
│   ├── purchases.py          # Purchase entry screen
│   ├── purchase_management.py # Purchase management dialog
│   ├── sales.py              # Sales management dialog
│   ├── customers.py          # Customer management dialog
│   ├── expenses.py           # Expenses management dialog
│   ├── other_income.py       # Other income management dialog
│   ├── users.py              # User management dialog
│   ├── reports.py            # Reports widget
│   └── bank_transactions.py  # Bank transactions dialog
├── utils/
│   ├── db_helper.py          # Database operations
│   ├── printer.py            # Receipt printing and PDF generation
│   └── backup.py             # Backup/restore utilities
├── assets/
│   ├── logo.png
│   └── icons/
├── invoices/                 # Generated PDF invoices
├── requirements.txt
├── schema.sql                # Database schema
└── sample_data.sql           # Optional sample data
```

## Key Workflows

### Making a Sale
1. Go to POS tab
2. Search or scan product barcode (supports both product and variant barcodes)
3. If product has variants, select the desired variant from the selection dialog
4. Add products/variants to cart (double-click or press Enter)
5. Adjust quantities, prices, discounts as needed
6. Select payment type (Cash, Card, QR, Other)
7. Enter paid amount
8. Click "Checkout & Print" (F9)
9. Stock automatically decreases (variant stock if variant selected, otherwise product stock)

### Recording a Purchase (Bulk Buy)
1. Go to Purchases tab (Admin only)
2. Search or select products (supports both product and variant barcodes)
3. If product has variants, select the desired variant from the selection dialog
4. Add products/variants to purchase cart with quantities and unit costs
5. Enter supplier name (optional)
6. Select payment type (Cash, Card, Cheque, Credit, Other)
7. Enter paid amount
8. Click "Save Purchase" (F9)
9. Stock automatically increases (variant stock if variant selected, otherwise product stock), cost price updates

### Recording Bank Transactions
1. Go to Manage menu → Bank Transactions (Admin only)
2. Click "Deposit (Cash → Bank)" to deposit cash to bank
3. Click "Withdrawal (Bank → Cash)" to withdraw from bank to cash
4. Enter amount and optional description
5. System validates available balances

### Managing Expenses
1. Go to Manage menu → Expenses (Admin only)
2. Enter description, category, amount
3. Select payment method (Cash, Card, Cheque, Credit, Other)
4. Select date and click "Add Expense"
5. Cash expenses reduce cashbook; card expenses reduce bankbook

## Payment Methods

The system tracks different payment methods:
- **Cash**: Affects cashbook balance
- **Card/QR/Other** (Sales): Affects bankbook balance
- **Card/Cheque/Credit/Other** (Purchases/Expenses): Affects bankbook balance

## Database Schema

Key tables:
- `users`: User accounts with roles
- `products`: Product catalog with stock
- `product_variants`: Product variants with size, color, SKU, barcodes, pricing, and stock
- `sales` & `sale_items`: Sales transactions (supports variant_id)
- `purchases` & `purchase_items`: Purchase transactions (supports variant_id)
- `expenses`: Expense records with payment types
- `customers`: Customer information
- `bank_transactions`: Cash ↔ Bank transfers
- `other_income`: Other income sources

## Product Variants

The system supports product variants to manage different sizes, colors, SKUs, and other variations of the same product:

- **Creating Variants**: Edit an existing product and go to the "Variants" tab to add variants
- **Variant Fields**: Size, Color, SKU, Barcode, Price (optional, falls back to product price), Cost Price, Stock Quantity, Low Stock Threshold
- **Variant Barcodes**: Each variant can have its own unique barcode for direct scanning
- **Stock Tracking**: Variants have independent stock levels separate from the base product
- **Pricing**: Variants can have custom pricing, or use the base product price if not specified
- **Sales & Purchases**: When adding a product with variants to cart, a selection dialog appears to choose the variant
- **Low Stock Alerts**: Both products and variants are included in low stock reports

## Notes
- The database auto-initializes on first launch using `schema.sql`. Sample data is not loaded by default.
- Replace the placeholder `assets/logo.png` with your shop logo.
- All data stays offline. No internet connection is required.
- Default admin login: `admin` / `admin123` (change after first login)
- Cashiers can only use POS screen; admins have full access
- Products without variants work exactly as before - the variant system is optional and backward compatible

## License
Proprietary – for Beauty P&C internal use.
