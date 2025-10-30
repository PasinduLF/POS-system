from typing import List, Dict
import os
from datetime import datetime

try:
	import win32print
	import win32ui
	WIN32_AVAILABLE = True
except Exception:
	WIN32_AVAILABLE = False

try:
	from escpos.printer import Usb as EscposUsb
	ESCPOS_AVAILABLE = True
except Exception:
	ESCPOS_AVAILABLE = False

try:
	from reportlab.pdfgen import canvas
	from reportlab.lib.pagesizes import A4
	from reportlab.lib.units import mm
	REPORTLAB_AVAILABLE = True
except Exception:
	REPORTLAB_AVAILABLE = False


def format_receipt_lines(shop_name: str, invoice_id: str, items: List[Dict], totals: Dict) -> str:
	lines = []
	lines.append(shop_name)
	lines.append(f'Invoice: {invoice_id}')
	lines.append('-' * 32)
	for it in items:
		name = it.get('name', '')[:16]
		qty = it['quantity']
		price = it['unit_price']
		line_total = it['line_total']
		lines.append(f"{name:<16}{qty:>3} x {price:>6.2f}")
		lines.append(f"{'':<16}{'':>3}   {line_total:>6.2f}")
	lines.append('-' * 32)
	lines.append(f"Subtotal: {totals.get('subtotal', 0):.2f}")
	lines.append(f"Discount: {totals.get('discount', 0):.2f}")
	lines.append(f"Total:    {totals.get('total', 0):.2f}")
	lines.append(f"Paid:     {totals.get('paid', 0):.2f}")
	lines.append(f"Change:   {totals.get('change', 0):.2f}")
	lines.append('Thank you!')
	return '\n'.join(lines)


def print_receipt_text(text: str, printer_name: str = None) -> None:
	if WIN32_AVAILABLE:
		printer = printer_name or win32print.GetDefaultPrinter()
		hPrinter = win32print.OpenPrinter(printer)
		try:
			job = win32print.StartDocPrinter(hPrinter, 1, ("BeautyPC Receipt", None, "RAW"))
			win32print.StartPagePrinter(hPrinter)
			win32print.WritePrinter(hPrinter, text.encode('utf-8'))
			win32print.EndPagePrinter(hPrinter)
			win32print.EndDocPrinter(hPrinter)
		except Exception:
			win32print.AbortPrinter(hPrinter)
		finally:
			win32print.ClosePrinter(hPrinter)
	else:
		# Fallback: save receipt to a text file
		with open('receipt.txt', 'w', encoding='utf-8') as f:
			f.write(text)


def open_cash_drawer(vid: int = None, pid: int = None) -> bool:
	"""Try to open cash drawer via ESC/POS kick (USB). Returns True if attempted.
	If python-escpos is not available or no device IDs provided, returns False.
	"""
	if ESCPOS_AVAILABLE and vid is not None and pid is not None:
		try:
			p = EscposUsb(vid, pid, timeout=0, in_ep=0x82, out_ep=0x01)
			p.cashdraw(2)  # kick drawer
			p.close()
			return True
		except Exception:
			return False
	return False


def generate_invoice_pdf(output_dir: str, shop_name: str, invoice_id: str, items: List[Dict], totals: Dict) -> str:
	"""Generate a simple A4 PDF invoice and return the saved file path."""
	if not REPORTLAB_AVAILABLE:
		raise RuntimeError('reportlab is not installed')
	os.makedirs(output_dir, exist_ok=True)
	filename = f"{invoice_id}.pdf"
	output_path = os.path.join(output_dir, filename)
	c = canvas.Canvas(output_path, pagesize=A4)
	width, height = A4

	margin = 15 * mm
	y = height - margin
	c.setFont('Helvetica-Bold', 14)
	c.drawString(margin, y, shop_name)
	y -= 8 * mm
	c.setFont('Helvetica', 10)
	c.drawString(margin, y, f"Invoice: {invoice_id}")
	c.drawRightString(width - margin, y, datetime.now().strftime('%Y-%m-%d %H:%M'))
	y -= 6 * mm
	c.line(margin, y, width - margin, y)
	y -= 6 * mm

	# headers
	c.setFont('Helvetica-Bold', 10)
	c.drawString(margin, y, 'Item')
	c.drawRightString(width - 90 * mm, y, 'Qty')
	c.drawRightString(width - 60 * mm, y, 'Price')
	c.drawRightString(width - 30 * mm, y, 'Discount')
	c.drawRightString(width - margin, y, 'Total')
	y -= 5 * mm
	c.line(margin, y, width - margin, y)
	y -= 5 * mm

	c.setFont('Helvetica', 10)
	for it in items:
		if y < 40 * mm:
			c.showPage(); y = height - margin
			c.setFont('Helvetica', 10)
		name = str(it.get('name', ''))
		qty = it.get('quantity', 0)
		price = float(it.get('unit_price', 0))
		disc = float(it.get('discount', 0))
		line_total = float(it.get('line_total', (qty * price) - disc))
		c.drawString(margin, y, name[:48])
		c.drawRightString(width - 90 * mm, y, f"{qty}")
		c.drawRightString(width - 60 * mm, y, f"{price:.2f}")
		c.drawRightString(width - 30 * mm, y, f"{disc:.2f}")
		c.drawRightString(width - margin, y, f"{line_total:.2f}")
		y -= 6 * mm

	# totals
	y -= 4 * mm
	c.line(margin, y, width - margin, y)
	y -= 8 * mm
	c.setFont('Helvetica-Bold', 11)
	sub = float(totals.get('subtotal', 0))
	dis = float(totals.get('discount', 0))
	tot = float(totals.get('total', 0))
	paid = float(totals.get('paid', 0))
	chg = float(totals.get('change', 0))
	c.drawRightString(width - 30 * mm, y, 'Subtotal:')
	c.drawRightString(width - margin, y, f"{sub:.2f}")
	y -= 6 * mm
	c.drawRightString(width - 30 * mm, y, 'Discount:')
	c.drawRightString(width - margin, y, f"{dis:.2f}")
	y -= 6 * mm
	c.drawRightString(width - 30 * mm, y, 'Total:')
	c.drawRightString(width - margin, y, f"{tot:.2f}")
	y -= 6 * mm
	c.drawRightString(width - 30 * mm, y, 'Paid:')
	c.drawRightString(width - margin, y, f"{paid:.2f}")
	y -= 6 * mm
	c.drawRightString(width - 30 * mm, y, 'Change:')
	c.drawRightString(width - margin, y, f"{chg:.2f}")

	y -= 12 * mm
	c.setFont('Helvetica', 9)
	c.drawString(margin, y, 'Thank you for your purchase!')

	c.save()
	return output_path

