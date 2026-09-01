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
                f"  • {row['name']} ({row['pct']}%): {format_toman(int(row['share']))}",
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
        lines.append(
            f"#{row['id']} | {row['customer_name']} | {row['device']} | {status}",
        )
    lines.append('\nبرای جزئیات: /repair شماره')
    lines.append('برای فاکتور: دکمه 🧾 فاکتور')
    return '\n'.join(lines)
