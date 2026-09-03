from __future__ import annotations

from app.services.accounting import format_toman


def format_repair_summary(repair: dict) -> str:
    totals = repair['totals']
    parts_lines = '\n'.join(
        f"  • {p['part_name']}: خرید {format_toman(int(p['cost']))} → فروش {format_toman(int(p['sell_price']))}"
        + (f" ({p['supplier_name']})" if p.get('supplier_name') else '')
        for p in repair['parts']
    ) or '  • بدون قطعه'
    status = 'باز' if repair['status'] == 'open' else 'بسته'
    return (
        f"📋 پرونده #{repair['id']} — {status}\n"
        f"👤 {repair['customer_name']} | {repair['customer_phone'] or '—'}\n"
        f"📱 {repair['device']}\n"
        f"🔧 {repair['issue']}\n"
        f"👨‍🔧 {repair['technician_name'] or '—'} ({repair['technician_pct']}%)\n\n"
        f"💼 اجرت: {format_toman(totals.labor_amount)}\n"
        f"🔩 قطعات:\n{parts_lines}\n\n"
        f"🧾 جمع مشتری: {format_toman(totals.customer_total)}\n"
        f"✅ دریافت‌شده: {format_toman(totals.customer_paid)}\n"
        f"📌 بدهی مشتری: {format_toman(totals.customer_debt)}\n"
        f"🏪 بدهی قطعه‌فروش: {format_toman(totals.supplier_debt)}\n"
        f"👨‍🔧 سهم تعمیرکار: {format_toman(totals.technician_share)}\n"
        f"✅ پرداخت به تعمیرکار: {format_toman(totals.technician_paid)}\n"
        f"📋 مانده طلب تعمیرکار: {format_toman(totals.technician_debt)}\n"
        f"🏢 سود فروشگاه: {format_toman(totals.shop_profit)}"
    )


def format_invoice(repair: dict) -> str:
    totals = repair['totals']
    parts_lines = '\n'.join(
        f"  • {p['part_name']}: {format_toman(int(p['sell_price']))}"
        for p in repair['parts']
    ) or '  • —'
    return (
        f"🧾 **فاکتور فروش #{repair['id']}**\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"👤 مشتری: {repair['customer_name']}\n"
        f"📞 تماس: {repair['customer_phone'] or '—'}\n"
        f"📱 دستگاه: {repair['device']}\n"
        f"🔧 ایراد: {repair['issue']}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💼 اجرت تعمیر: {format_toman(totals.labor_amount)}\n"
        f"🔩 قطعات:\n{parts_lines}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💰 **جمع کل:** {format_toman(totals.customer_total)}\n"
        f"✅ پرداخت‌شده: {format_toman(totals.customer_paid)}\n"
        f"📌 **مانده:** {format_toman(totals.customer_debt)}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"CTTEL · سی تی تل"
    )


def format_accounting_report(dashboard: dict) -> str:
    lines = [
        '📊 **گزارش حسابداری**',
        '━━━━━━━━━━━━━━━━',
        f"📂 پرونده باز: {dashboard['open_count']}",
        '',
        '🏢 **سود فروشگاه (پرونده باز)**',
        f"  {format_toman(dashboard['shop_profit'])}",
        '',
        '👨‍🔧 **سهم تعمیرکاران**',
    ]
    if dashboard['technicians']:
        for row in dashboard['technicians']:
            lines.append(
                f"  • {row['name']} ({row['pct']}%): "
                f"سهم {format_toman(int(row['share']))} | "
                f"پرداخت {format_toman(int(row.get('paid') or 0))} | "
                f"مانده {format_toman(int(row.get('debt') or 0))}",
            )
    else:
        lines.append('  • —')

    lines.extend(['', '🏪 **بدهی به قطعه‌فروش**'])
    if dashboard['suppliers']:
        for row in dashboard['suppliers']:
            lines.append(f"  • {row['name']}: {format_toman(int(row['debt']))}")
    else:
        lines.append('  • —')

    lines.extend(
        [
            '',
            '👥 **بدهی مشتریان**',
            f"  جمع: {format_toman(dashboard['customer_debt'])}",
            '',
            '━━━━━━━━━━━━━━━━',
            f"📌 جمع بدهی مشتری: {format_toman(dashboard['customer_debt'])}",
            f"🏪 جمع بدهی قطعه‌فروش: {format_toman(dashboard['supplier_debt'])}",
            f"👨‍🔧 جمع سهم تعمیرکار: {format_toman(dashboard['technician_share'])}",
            f"✅ پرداخت‌شده به تعمیرکاران: {format_toman(dashboard.get('technician_paid', 0))}",
            f"📋 مانده طلب تعمیرکاران: {format_toman(dashboard.get('technician_debt', 0))}",
            f"🏢 جمع سود فروشگاه: {format_toman(dashboard['shop_profit'])}",
        ],
    )
    return '\n'.join(lines)


def format_search_results(results: list[dict]) -> str:
    if not results:
        return 'نتیجه‌ای یافت نشد.'
    lines = ['🔍 **نتایج جستجو:**', '']
    for row in results:
        status = 'باز' if row['status'] == 'open' else 'بسته'
        issue = (row.get('issue') or '')[:35]
        phone = row.get('customer_phone') or '—'
        lines.append(
            f"#{row['id']} | {status} | {row['customer_name']}\n"
            f"📱 {row['device']}" + (f" | 🔧 {issue}" if issue else '') + f"\n📞 {phone}",
        )
        lines.append('')
    lines.append('برای جزئیات روی دکمه زیر بزنید.')
    return '\n'.join(lines)


REPAIR_LIST_PAGE_SIZE = 8

_LIST_TITLES = {
    'open': '📋 **پرونده‌های باز**',
    'closed': '📁 **پرونده‌های بسته**',
    'all': '📋 **همه پرونده‌ها**',
}


def format_repair_list(
    repairs: list[dict],
    *,
    status_filter: str = 'open',
    page: int = 0,
    total: int = 0,
) -> str:
    title = _LIST_TITLES.get(status_filter, _LIST_TITLES['open'])
    if not repairs:
        return f'{title}\n\nپرونده‌ای یافت نشد.'
    lines = [title, f'تعداد: {total}', '']
    for row in repairs:
        status = 'باز' if row['status'] == 'open' else 'بسته'
        phone = row.get('customer_phone') or '—'
        tech = row.get('technician_name') or '—'
        issue = (row.get('issue') or '—')[:40]
        total_amt = int(row.get('customer_total') or 0)
        lines.append(
            f"#{row['id']} | {status} | {row['customer_name']}\n"
            f"📱 {row['device']} | 🔧 {issue}\n"
            f"📞 {phone} | 👨‍🔧 {tech} | 💰 {format_toman(total_amt)}",
        )
        lines.append('')
    page_count = max(1, (total + REPAIR_LIST_PAGE_SIZE - 1) // REPAIR_LIST_PAGE_SIZE)
    lines.append(f'صفحه {page + 1} از {page_count}')
    lines.append('برای جزئیات روی دکمه زیر بزنید.')
    return '\n'.join(lines)
