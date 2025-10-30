import os
import zipfile
from typing import List, Dict
import pandas as pd


def backup_database(db_path: str, output_zip: str) -> None:
	with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
		zf.write(db_path, arcname=os.path.basename(db_path))


def export_table_to_csv(db_conn, table_name: str, output_csv: str) -> None:
	df = pd.read_sql_query(f'SELECT * FROM {table_name}', db_conn)
	df.to_csv(output_csv, index=False)


def export_table_to_excel(db_conn, table_name: str, output_xlsx: str) -> None:
	df = pd.read_sql_query(f'SELECT * FROM {table_name}', db_conn)
	df.to_excel(output_xlsx, index=False)





