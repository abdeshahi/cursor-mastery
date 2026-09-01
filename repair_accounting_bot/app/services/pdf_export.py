from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import arabic_reshaper
from bidi.algorithm import get_display
from fpdf import FPDF

from app.services.accounting import format_toman

FONT_PATH = Path(__file__).resolve().parents[2] / 'assets' / 'fonts' / 'Vazirmatn-Regular.ttf'


def rtl(text: str) -> str:
    return get_display(arabic_reshaper.reshape(str(text)))


class PersianPDF(FPDF):
    def __init__(self) -> None:
        super().__init__()
        self.add_font('Vazir', '', str(FONT_PATH))
        self.set_auto_page_break(auto=True, margin=12)

    def cell_rtl(self, w: float, h: float, text: str, *, ln: bool = True, bold: bool = False) -> None:
        self.set_font('Vazir', size=10 if not bold else 12)
        self.cell(w, h, rtl(text), ln=int(ln), align='R')


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
        ('جمع بدهی مشتری', format_toman(dashboard['customer_debt'])),
        ('جمع بدهی قطعه‌فروش', format_toman(dashboard['supplier_debt'])),
    ]:
        pdf.cell_rtl(0, 8, f'{label}: {amount}')

    pdf.ln(2)
    pdf.cell_rtl(0, 9, 'سهم تعمیرکاران', bold=True)
    for row in dashboard.get('technicians', []) or [{'name': '—', 'pct': 0, 'share': 0}]:
        pdf.cell_rtl(
            0,
            7,
            f"{row['name']} ({row['pct']}%) → {format_toman(int(row['share']))}",
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
    pdf = PersianPDF()
    pdf.add_page()
    pdf.cell_rtl(0, 10, f"فاکتور فروش #{repair['id']}", bold=True)
    pdf.cell_rtl(0, 8, 'CTTEL · سی تی تل')
    pdf.cell_rtl(0, 8, datetime.now().strftime('%Y-%m-%d %H:%M'))
    pdf.ln(3)

    for label, value in [
        ('مشتری', repair['customer_name']),
        ('تماس', repair['customer_phone'] or '—'),
        ('دستگاه', repair['device']),
        ('ایراد', repair['issue']),
        ('تعمیرکار', repair.get('technician_name') or '—'),
        ('درصد تعمیرکار', f"{repair['technician_pct']}%"),
    ]:
        pdf.cell_rtl(0, 8, f'{label}: {value}')

    pdf.ln(2)
    pdf.cell_rtl(0, 9, f'اجرت تعمیر: {format_toman(totals.labor_amount)}', bold=True)
    for part in repair['parts']:
        pdf.cell_rtl(0, 7, f"{part['part_name']}: {format_toman(int(part['sell_price']))}")
    if not repair['parts']:
        pdf.cell_rtl(0, 7, 'بدون قطعه')

    pdf.ln(2)
    pdf.cell_rtl(0, 9, f'جمع کل: {format_toman(totals.customer_total)}', bold=True)
    pdf.cell_rtl(0, 8, f'پرداخت‌شده: {format_toman(totals.customer_paid)}')
    pdf.cell_rtl(0, 8, f'مانده: {format_toman(totals.customer_debt)}')

    path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(path))
    return path
