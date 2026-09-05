from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import arabic_reshaper
from bidi.algorithm import get_display
from fpdf import FPDF

from app.services.accounting import format_toman
from app.services.persian_utils import format_amount_persian, format_jalali_date_persian, to_persian_digits

ASSETS_DIR = Path(__file__).resolve().parents[2] / 'assets'
FONT_PATH = ASSETS_DIR / 'fonts' / 'Vazirmatn-Regular.ttf'
LETTERHEAD_PATH = ASSETS_DIR / 'letterhead' / 'a5.jpg'

INVOICE_TOP_MM = 42
INVOICE_BOTTOM_MM = 32
INVOICE_SIDE_MM = 12
# Placed immediately left of the printed «تاریخ» label on the letterhead.
DATE_X_MM = 86
DATE_Y_MM = 31
DATE_W_MM = 30


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
        self._date_text = format_jalali_date_persian()

    def set_invoice_date(self, value: str) -> None:
        self._date_text = value

    @property
    def content_width(self) -> float:
        return self.w - (2 * INVOICE_SIDE_MM)

    def header(self) -> None:
        if LETTERHEAD_PATH.exists():
            self.image(str(LETTERHEAD_PATH), x=0, y=0, w=self.w, h=self.h)
        self.set_font('Vazir', size=10)
        self.set_xy(DATE_X_MM, DATE_Y_MM)
        self.cell(DATE_W_MM, 5, rtl(self._date_text), align='R')
        self.set_margins(INVOICE_SIDE_MM, INVOICE_TOP_MM, INVOICE_SIDE_MM)
        self.set_auto_page_break(auto=True, margin=INVOICE_BOTTOM_MM)
        self.set_y(INVOICE_TOP_MM)

    def table_row(
        self,
        widths: list[float],
        cells: list[str],
        *,
        height: float = 7,
        header: bool = False,
        aligns: list[str] | None = None,
        header_fill: tuple[int, int, int] | None = None,
    ) -> None:
        if aligns is None:
            aligns = ['C'] * len(cells)
        self.set_font('Vazir', size=10 if header else 9)
        if header:
            fill = header_fill or (235, 235, 235)
            self.set_fill_color(*fill)
        for width, text, align in zip(widths, cells, aligns):
            self.cell(
                width,
                height,
                rtl(text),
                border=1,
                align=align,
                fill=header,
            )
        self.ln(height)


from app.ui.themes import Theme, get_theme


def build_accounting_pdf(
    dashboard: dict[str, Any],
    repairs: list[dict[str, Any]],
    customer_debts: list[dict[str, Any]],
    path: Path,
    *,
    theme: Theme | None = None,
) -> Path:
    theme = theme or get_theme(None)
    pdf = PersianPDF()
    pdf.add_page()
    pdf.set_text_color(*theme.primary)
    pdf.cell_rtl(0, 10, 'گزارش حسابداری CTTEL', bold=True)
    pdf.set_text_color(0, 0, 0)
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


def build_invoice_pdf(
    repair: dict[str, Any],
    path: Path,
    *,
    theme: Theme | None = None,
) -> Path:
    theme = theme or get_theme(None)
    totals = repair['totals']
    pdf = InvoicePDF()
    pdf.set_invoice_date(format_jalali_date_persian())
    pdf.add_page()
    header_fill = theme.secondary

    w = pdf.content_width
    label_w = w * 0.28
    value_w = w - label_w
    col_row = w * 0.12
    col_desc = w * 0.56
    col_amount = w - col_row - col_desc

    pdf.set_font('Vazir', size=12)
    pdf.set_text_color(*theme.primary)
    pdf.cell(w, 8, rtl(f"فاکتور فروش #{to_persian_digits(repair['id'])}"), ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    pdf.table_row([value_w, label_w], ['مشخصات', 'مورد'], header=True, header_fill=header_fill)
    for label, value in [
        ('مشتری', repair['customer_name']),
        ('تماس', repair['customer_phone'] or '—'),
        ('دستگاه', repair['device']),
        ('ایراد', repair['issue']),
        ('تعمیرکار', repair.get('technician_name') or '—'),
    ]:
        pdf.table_row([value_w, label_w], [str(value), label], aligns=['R', 'R'])

    pdf.ln(3)
    pdf.table_row(
        [col_amount, col_desc, col_row],
        ['مبلغ (تومان)', 'شرح', 'ردیف'],
        header=True,
        height=8,
        header_fill=header_fill,
    )

    row_num = 1
    pdf.table_row(
        [col_amount, col_desc, col_row],
        [format_amount_persian(totals.labor_amount), 'اجرت تعمیر', to_persian_digits(row_num)],
        aligns=['C', 'R', 'C'],
    )
    row_num += 1
    for part in repair['parts']:
        pdf.table_row(
            [col_amount, col_desc, col_row],
            [
                format_amount_persian(int(part['sell_price'])),
                str(part['part_name']),
                to_persian_digits(row_num),
            ],
            aligns=['C', 'R', 'C'],
        )
        row_num += 1
    if not repair['parts'] and totals.labor_amount == 0:
        pdf.table_row(
            [col_amount, col_desc, col_row],
            [to_persian_digits(0), '—', to_persian_digits(1)],
            aligns=['C', 'C', 'C'],
        )

    pdf.ln(3)
    summary_label_w = w * 0.62
    summary_value_w = w - summary_label_w
    pdf.table_row([summary_value_w, summary_label_w], ['مبلغ (تومان)', 'شرح'], header=True, header_fill=header_fill)
    for label, amount in [
        ('جمع کل', totals.customer_total),
        ('پرداخت‌شده', totals.customer_paid),
        ('مانده حساب', totals.customer_debt),
    ]:
        pdf.table_row(
            [summary_value_w, summary_label_w],
            [format_amount_persian(amount), label],
            aligns=['C', 'R'],
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(path))
    return path
