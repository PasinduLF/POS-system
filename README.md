# Beauty P&C POS (Offline Desktop)

Offline desktop POS app for Windows.

Beauty P&C POS is a fully offline Point of Sale system for Windows, built with Python, PyQt5, and SQLite. It is designed for fast daily billing, simple inventory management, and reliable offline use in a small retail shop in Sri Lanka.

## Features
- Login with Admin and Cashier roles
- Product management (Cosmetics, Jewelry, Accessories)
- Fast POS screen: search by name or barcode, cart, discounts, multi-payment
- Auto stock updates and low stock alerts
- Sales, inventory, and profit reports; top products; category summary
- Expenses tracking and monthly summary
- Thermal receipt printing (ESC/POS or Windows printers)
- Offline SQLite database with local backup/restore
- Export to CSV/Excel

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
├── main.py
├── database/
│   └── beauty_pc.db
├── ui/
│   ├── login.py
│   ├── dashboard.py
│   ├── pos_screen.py
│   ├── products.py
│   └── reports.py
├── utils/
│   ├── db_helper.py
│   ├── printer.py
│   └── backup.py
├── assets/
│   ├── logo.png
│   └── icons/
├── requirements.txt
├── schema.sql
└── sample_data.sql
```

## Notes
- The database auto-initializes on first launch using `schema.sql`. Sample data is not loaded by default.
- Replace the placeholder `assets/logo.png` with your shop logo.
- All data stays offline. No internet connection is required.

## License
Proprietary – for Beauty P&C internal use.
