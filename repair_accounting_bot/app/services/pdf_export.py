from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import arabic_reshaper
from bidi.algorithm import get_display
from fpdf import FPDF

from app.services.accounting import format_toman

ASSETS_DIR = Path(__file__).resolve().parents[2] / 'assets'
FONT_PATH = ASSETS_DIR / 'fonts' / 'Vazirmatn-Regular.ttf'
LETTERHEAD_PATH = ASSETS_DIR / 'letterhead' / 'a5.jpg'

# A5 content box aligned with the provided letterhead artwork.
INVOICE_TOP_MM = 42
INVOICE_BOTTOM_MM = 32
INVOICE_SIDE_MM = 12
DATE_X_MM = 108
DATE_Y_MM = 33


def rtl(text: str) -> str:
    return get_display(arabic_reshaper.reshape(str(text)))


class PersianPDF(FPDF):
    def __init__(self, *, page_format: str | tuple[float, float] = 'A4') -> None:
        super().__init__(orientation='P', unit='mm', format=page_format)
        self.add_font('Vazir', '', str(FONT_PATH))
        self.set_auto_page_break(auto=True, margin=12)

    def cell_rtl(self, w: float, h: float, text: str, *, ln: bool = True, bold: bool = False) -> None:
        self.set_font('Vazir', size=10 if not bold else 12)
        self.cell(w, h, rtl(text), ln=int(ln), align='R')


class InvoicePDF(PersianPDF):
    def __init__(self) -> None:
        super().__init__(page_format='A5')
        self._date_text = datetime.now().strftime('%Y/%m/%d')

    def set_invoice_date(self, value: str) -> None:
        self._date_text = value

    def header(self) -> None:
        if LETTERHEAD_PATH.exists():
            self.image(str(LETTERHEAD_PATH), x=0, y=0, w=self.w, h=self.h)
        self.set_font('Vazir', size=9)
        self.set_xy(DATE_X_MM, DATE_Y_MM)
        self.cell(self.w - DATE_X_MM - INVOICE_SIDE_MM, 5, rtl(self._date_text), align='R')
        self.set_margins(INVOICE_SIDE_MM, INVOICE_TOP_MM, INVOICE_SIDE_MM)
        self.set_auto_page_break(auto=True, margin=INVOICE_BOTTOM_MM)
        self.set_y(INVOICE_TOP_MM)

    def line_rtl(self, h: float, text: str, *, bold: bool = False, size: int = 10) -> None:
        self.set_font('Vazir', size=size if not bold else size + 1)
        self.cell(0, h, rtl(text), ln=True, align='R')


def build_accounting_pdf(
    dashboard: dict[str, Any],
    repairs: list[dict[str, Any]],
    customer_debts: list[dict[str, Any]],
    path: Path,
) -> Path:
    pdf = PersianPDF()
    pdf.add_page()
    pdf.cell_rtl(0, 10, 'گزارش حسابداری CTTEL', bold=True)
    pdf.cell_rtl(0, 8, datetime.now().strftime('%Y-%m-%d %H:%M'))
    pdf.ln(4)

    for label, amount in [
        ('پرونده باز', str(dashboard['open_count'])),
        ('سود فروشگاه', format_toman(dashboard['shop_profit'])),
        ('جمع سهم تعمیرکار', format_toman(dashboard['technician_share'])),
        ('پرداخت‌شده به تعمیرکار', format_toman(dashboard.get('technician_paid', 0))),
        ('مانده طلب تعمیرکار', format_toman(dashboard.get('technician_debt', 0))),
        ('جمع بدهی مشتری', format_toman(dashboard['customer_debt'])),
        ('جمع بدهی قطعه‌فروش', format_toman(dashboard['supplier_debt'])),
    ]:
        pdf.cell_rtl(0, 8, f'{label}: {amount}')

    pdf.ln(2)
    pdf.cell_rtl(0, 9, 'طلب تعمیرکاران', bold=True)
    for row in dashboard.get('technicians', []) or [{'name': '—', 'pct': 0, 'share': 0, 'paid': 0, 'debt': 0}]:
        pdf.cell_rtl(
            0,
            7,
            (
                f"{row['name']} ({row['pct']}%) → "
                f"سهم {format_toman(int(row['share']))} | "
                f"پرداخت {format_toman(int(row.get('paid') or 0))} | "
                f"مانده {format_toman(int(row.get('debt') or 0))}"
            ),
        )

    pdf.ln(2)
    pdf.cell_rtl(0, 9, 'بدهی قطعه‌فروش', bold=True)
    for row in dashboard.get('suppliers', []) or [{'name': '—', 'debt': 0}]:
        pdf.cell_rtl(0, 7, f"{row['name']}: {format_toman(int(row['debt']))}")

    pdf.ln(2)
    pdf.cell_rtl(0, 9, 'بدهی مشتریان', bold=True)
    for row in customer_debts or [{'name': '—', 'phone': '—', 'debt': 0}]:
        pdf.cell_rtl(
            0,
            7,
            f"{row['name']} ({row.get('phone') or '—'}): {format_toman(int(row['debt']))}",
        )

    pdf.add_page()
    pdf.cell_rtl(0, 10, 'پرونده‌های باز', bold=True)
    for repair in repairs:
        totals = repair['totals']
        pdf.cell_rtl(
            0,
            8,
            (
                f"#{repair['id']} | {repair['customer_name']} | {repair['device']} | "
                f"سود {format_toman(totals.shop_profit)}"
            ),
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(path))
    return path


def build_invoice_pdf(repair: dict[str, Any], path: Path) -> Path:
    totals = repair['totals']
    pdf = InvoicePDF()
    pdf.set_invoice_date(datetime.now().strftime('%Y/%m/%d'))
    pdf.add_page()

    pdf.line_rtl(8, f"فاکتور فروش #{repair['id']}", bold=True, size=12)
    pdf.ln(2)

    for label, value in [
        ('مشتری', repair['customer_name']),
        ('تماس', repair['customer_phone'] or '—'),
        ('دستگاه', repair['device']),
        ('ایراد', repair['issue']),
        ('تعمیرکار', repair.get('technician_name') or '—'),
    ]:
        pdf.line_rtl(7, f'{label}: {value}')

    pdf.ln(2)
    pdf.line_rtl(8, 'اقلام فاکتور', bold=True)
    pdf.line_rtl(7, f"اجرت تعمیر: {format_toman(totals.labor_amount)}")
    for part in repair['parts']:
        pdf.line_rtl(7, f"{part['part_name']}: {format_toman(int(part['sell_price']))}")
    if not repair['parts']:
        pdf.line_rtl(7, 'بدون قطعه')

    pdf.ln(2)
    pdf.line_rtl(8, f'جمع کل: {format_toman(totals.customer_total)}', bold=True, size=11)
    pdf.line_rtl(7, f'پرداخت‌شده: {format_toman(totals.customer_paid)}')
    pdf.line_rtl(7, f'مانده حساب: {format_toman(totals.customer_debt)}', bold=True)

    path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(path))
    return path
