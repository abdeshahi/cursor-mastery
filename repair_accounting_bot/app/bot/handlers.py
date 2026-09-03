from __future__ import annotations

from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from app.bot.keyboards import (
    ACC_CUSTOMER_DEBT,
    ACC_EXPORT_EXCEL,
    ACC_EXPORT_PDF,
    ACC_SHOP_PROFIT,
    ACC_SUMMARY,
    ACC_SUPPLIER_DEBT,
    ACC_TECH_SHARE,
    BACK_ROOT,
    REC_INVOICE,
    REC_NEW,
    REC_REPORT,
    REC_SEARCH,
    ROOT_ACCOUNTING,
    ROOT_RECEPTION,
    accounting_menu,
    cancel_keyboard,
    parts_more_keyboard,
    reception_menu,
    repair_actions,
    root_menu,
    search_result_keyboard,
    skip_keyboard,
    supplier_keyboard,
    technician_keyboard,
)
from app.bot.middleware import RepositoryMiddleware
from app.bot.parsing import parse_staff_args
from app.bot.staff_middleware import StaffGuardMiddleware
from app.bot.admin_handlers import admin_router
from app.bot.edit_handlers import edit_router
from app.bot.settle_handlers import process_settle_payment, settle_router
from app.bot.states import AddSupplier, AddTechnician, InvoiceLookup, NewRepair, Payment, SearchRepair
from app.config import settings
from app.services.accounting import format_toman
from app.services.export_service import ExportService
from app.services.formatters import (
    format_accounting_report,
    format_invoice,
    format_repair_summary,
    format_search_results,
)
from app.storage.db import Database
from app.storage.staff_repository import StaffRepository
from app.storage.repository import RepairRepository
from app.staff.roles import ROLE_LABELS

router = Router()


def user_root_menu(can_reception: bool, can_accounting: bool, can_manage: bool):
    return root_menu(
        can_reception=can_reception,
        can_accounting=can_accounting,
        can_manage=can_manage,
    )


async def show_repair(
    message: Message,
    repo: RepairRepository,
    repair_id: int,
    *,
    can_edit_repair: bool = False,
) -> None:
    repair = await repo.get_repair(repair_id)
    if not repair:
        await message.answer('پرونده یافت نشد.')
        return
    is_open = repair.get('status') == 'open'
    await message.answer(
        format_repair_summary(repair),
        reply_markup=repair_actions(repair_id, is_open=is_open, can_edit=can_edit_repair),
    )


async def show_accounting_report(message: Message, repo: RepairRepository) -> None:
    dashboard = await repo.accounting_dashboard()
    await message.answer(format_accounting_report(dashboard), parse_mode='Markdown')


async def send_export_file(message: Message, path: Path, caption: str) -> None:
    await message.answer_document(FSInputFile(path), caption=caption)


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    state: FSMContext,
    can_reception: bool,
    can_accounting: bool,
    can_manage: bool,
    invite_joined: bool = False,
) -> None:
    await state.clear()
    text = ''
    if invite_joined:
        text += '✅ **به تیم CTTEL خوش آمدید!**\n\n'
    text += '🔧 **بات پذیرش و حسابداری CTTEL**\n\n'
    if can_reception:
        text += '📥 **پذیرش** — ثبت، جستجو، فاکتور\n'
    if can_accounting:
        text += '💼 **حسابداری** — سود، سهم تعمیرکار، بدهی‌ها\n'
    if can_manage:
        text += '⚙️ **مدیریت** — پرسنل، تعمیرکار، فروشنده\n'
    await message.answer(
        text,
        reply_markup=user_root_menu(can_reception, can_accounting, can_manage),
        parse_mode='Markdown',
    )


@router.message(Command('help'))
@router.message(F.text == 'ℹ️ راهنما')
async def cmd_help(message: Message) -> None:
    await message.answer(
        '📥 **منوی پذیرش**\n'
        '• پذیرش جدید — ثبت مشتری، دستگاه، تعمیرکار، اجرت، قطعه\n'
        '• ✏️ ویرایش پرونده — تغییر اجرت یا افزودن قطعه (با اجازه مدیر)\n'
        '• جستجو — با شماره پرونده، نام، موبایل یا مدل دستگاه\n'
        '• فاکتور — صدور فاکتور فروش برای مشتری\n'
        '• گزارش حسابداری — خلاصه مالی\n\n'
        '💼 **منوی حسابداری**\n'
        '• سود فروشگاه — سود خالص پرونده‌های باز\n'
        '• طلب تعمیرکاران — سهم، پرداخت‌شده و مانده طلب هر نفر\n'
        '• بدهی قطعه‌فروش — طلب فروشندگان قطعه\n'
        '• بدهی مشتریان — مانده حساب مشتری‌ها\n'
        '• 💸 ثبت پرداخت بدهی — پرداخت به تعمیرکار یا فروشنده (کامل یا جزئی)\n'
        '• 💵 دریافت از مشتری — ثبت پرداخت بدهی مشتری (کامل یا جزئی)\n'
        '• ✏️ ویرایش پرونده — تغییر اجرت یا افزودن قطعه بعد از پذیرش\n'
        '• خروجی Excel / PDF — گزارش کامل حسابداری\n\n'
        'روی هر پرونده: 📊 Excel و 📄 PDF فاکتور\n\n'
        '⚙️ **مدیریت (فقط مدیر):** پرسنل، لینک دعوت، تعمیرکاران، قطعه‌فروش، دسترسی ویرایش پرونده\n'
        'برای گرفتن آیدی: /myid',
        parse_mode='Markdown',
    )


@router.message(F.text == BACK_ROOT)
@router.message(F.text == '❌ انصراف')
async def back_to_root(
    message: Message,
    state: FSMContext,
    can_reception: bool,
    can_accounting: bool,
    can_manage: bool,
) -> None:
    await state.clear()
    await message.answer(
        'منوی اصلی',
        reply_markup=user_root_menu(can_reception, can_accounting, can_manage),
    )


@router.message(F.text == ROOT_RECEPTION)
async def open_reception_menu(message: Message, state: FSMContext, can_reception: bool) -> None:
    if not can_reception:
        await message.answer('⛔️ دسترسی پذیرش برای شما فعال نیست.')
        return
    await state.clear()
    await message.answer('📥 **منوی پذیرش**', reply_markup=reception_menu(), parse_mode='Markdown')


@router.message(F.text == ROOT_ACCOUNTING)
async def open_accounting_menu(message: Message, state: FSMContext, can_accounting: bool) -> None:
    if not can_accounting:
        await message.answer('⛔️ دسترسی حسابداری برای شما فعال نیست.')
        return
    await state.clear()
    await message.answer('💼 **منوی حسابداری**', reply_markup=accounting_menu(), parse_mode='Markdown')


# --- Reception: new repair flow ---

@router.message(F.text == REC_NEW)
async def start_repair(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(NewRepair.customer_name)
    await state.update_data(parts=[])
    await message.answer('نام مشتری را وارد کنید:', reply_markup=cancel_keyboard())


@router.message(NewRepair.customer_name)
async def repair_customer_name(message: Message, state: FSMContext) -> None:
    await state.update_data(customer_name=message.text.strip())
    await state.set_state(NewRepair.customer_phone)
    await message.answer('شماره تماس مشتری (اختیاری — `-` برای خالی):')


@router.message(NewRepair.customer_phone)
async def repair_customer_phone(message: Message, state: FSMContext) -> None:
    phone = message.text.strip()
    if phone == '-':
        phone = ''
    await state.update_data(customer_phone=phone)
    await state.set_state(NewRepair.device)
    await message.answer('مدل دستگاه (مثلاً iPhone 13):')


@router.message(NewRepair.device)
async def repair_device(message: Message, state: FSMContext) -> None:
    await state.update_data(device=message.text.strip())
    await state.set_state(NewRepair.issue)
    await message.answer('شرح مشکل / ایراد:')


@router.message(NewRepair.issue)
async def repair_issue(message: Message, state: FSMContext, repo: RepairRepository) -> None:
    await state.update_data(issue=message.text.strip())
    technicians = await repo.list_technicians()
    if not technicians:
        await state.set_state(AddTechnician.name)
        await message.answer('هنوز تعمیرکاری ثبت نشده. نام تعمیرکار را وارد کنید:')
        return
    await state.set_state(NewRepair.technician)
    await message.answer('تعمیرکار را انتخاب کنید:', reply_markup=technician_keyboard(technicians))


@router.callback_query(F.data.startswith('tech:'))
async def pick_technician(callback: CallbackQuery, state: FSMContext, repo: RepairRepository) -> None:
    value = callback.data.split(':', 1)[1]
    if value == 'new':
        await state.set_state(AddTechnician.name)
        await callback.message.answer('نام تعمیرکار جدید:')
        await callback.answer()
        return
    tech_id = int(value)
    technicians = await repo.list_technicians()
    tech = next((t for t in technicians if t['id'] == tech_id), None)
    if not tech:
        await callback.answer('تعمیرکار یافت نشد', show_alert=True)
        return
    await state.update_data(technician_id=tech_id, technician_pct=float(tech['default_pct']))
    await state.set_state(NewRepair.labor_amount)
    await callback.message.answer(
        f"تعمیرکار: {tech['name']} ({tech['default_pct']}%)\n"
        'مبلغ اجرت تعمیر (تومان):',
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(NewRepair.labor_amount)
async def repair_labor(message: Message, state: FSMContext) -> None:
    if not message.text.strip().isdigit():
        await message.answer('لطفاً فقط عدد وارد کنید.')
        return
    await state.update_data(labor_amount=int(message.text.strip()))
    await state.set_state(NewRepair.part_name)
    await message.answer('نام قطعه (یا «⏭ بدون قطعه / ادامه»):', reply_markup=skip_keyboard())


@router.message(NewRepair.part_name, F.text == '⏭ بدون قطعه / ادامه')
async def repair_no_parts(message: Message, state: FSMContext, repo: RepairRepository, can_edit_repair: bool = False) -> None:
    await finalize_repair(message, state, repo, can_edit_repair=can_edit_repair)


@router.message(NewRepair.part_name, F.text == '✅ ثبت نهایی پذیرش')
async def repair_finalize_button(message: Message, state: FSMContext, repo: RepairRepository, can_edit_repair: bool = False) -> None:
    await finalize_repair(message, state, repo, can_edit_repair=can_edit_repair)


@router.message(NewRepair.part_name, F.text == '➕ قطعه دیگر')
async def repair_add_more_part(message: Message, state: FSMContext) -> None:
    await message.answer('نام قطعه بعدی:', reply_markup=cancel_keyboard())


@router.message(NewRepair.part_name)
async def repair_part_name(message: Message, state: FSMContext) -> None:
    await state.update_data(current_part={'part_name': message.text.strip()})
    await state.set_state(NewRepair.part_cost)
    await message.answer('قیمت خرید قطعه از فروشنده (تومان):', reply_markup=cancel_keyboard())


@router.message(NewRepair.part_cost)
async def repair_part_cost(message: Message, state: FSMContext) -> None:
    if not message.text.strip().isdigit():
        await message.answer('لطفاً فقط عدد وارد کنید.')
        return
    data = await state.get_data()
    part = data.get('current_part', {})
    part['cost'] = int(message.text.strip())
    await state.update_data(current_part=part)
    await state.set_state(NewRepair.part_sell)
    await message.answer('قیمت فروش قطعه به مشتری (تومان):')


@router.message(NewRepair.part_sell)
async def repair_part_sell(message: Message, state: FSMContext, repo: RepairRepository) -> None:
    if not message.text.strip().isdigit():
        await message.answer('لطفاً فقط عدد وارد کنید.')
        return
    data = await state.get_data()
    part = data.get('current_part', {})
    part['sell_price'] = int(message.text.strip())
    await state.update_data(current_part=part)
    suppliers = await repo.list_suppliers()
    await state.set_state(NewRepair.part_supplier)
    if suppliers:
        await message.answer('فروشنده قطعه:', reply_markup=supplier_keyboard(suppliers))
    else:
        await message.answer('نام فروشنده قطعه (یا `-`):')


@router.callback_query(F.data.startswith('sup:'))
async def pick_supplier(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.split(':', 1)[1]
    data = await state.get_data()
    part = data.get('current_part', {})
    if value == 'new':
        await state.set_state(AddSupplier.name)
        await callback.message.answer('نام فروشنده قطعه:')
        await callback.answer()
        return
    if value != 'skip':
        part['supplier_id'] = int(value)
    await state.update_data(current_part=part)
    await append_part(callback.message, state)
    await callback.answer()


@router.message(NewRepair.part_supplier)
async def repair_part_supplier_text(message: Message, state: FSMContext, repo: RepairRepository) -> None:
    data = await state.get_data()
    part = data.get('current_part', {})
    name = message.text.strip()
    if name != '-':
        part['supplier_id'] = await repo.add_supplier(name)
    await state.update_data(current_part=part)
    await append_part(message, state)


async def append_part(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    parts = list(data.get('parts', []))
    parts.append(data['current_part'])
    await state.update_data(parts=parts, current_part={})
    await state.set_state(NewRepair.part_name)
    await message.answer(
        f"قطعه ثبت شد ({len(parts)} مورد).\n"
        'قطعه دیگر یا «✅ ثبت نهایی پذیرش»:',
        reply_markup=parts_more_keyboard(),
    )


async def finalize_repair(
    message: Message,
    state: FSMContext,
    repo: RepairRepository,
    *,
    can_edit_repair: bool = False,
) -> None:
    data = await state.get_data()
    customer_id = await repo.find_or_create_customer(
        data['customer_name'],
        data.get('customer_phone', ''),
    )
    repair_id = await repo.create_repair(
        customer_id=customer_id,
        technician_id=data.get('technician_id'),
        device=data['device'],
        issue=data['issue'],
        labor_amount=int(data['labor_amount']),
        technician_pct=float(data.get('technician_pct', 40)),
        parts=list(data.get('parts', [])),
    )
    repair = await repo.get_repair(repair_id)
    await state.clear()
    await message.answer(format_repair_summary(repair), reply_markup=repair_actions(repair_id, is_open=True, can_edit=can_edit_repair))
    await message.answer(
        format_invoice(repair),
        parse_mode='Markdown',
        reply_markup=reception_menu(),
    )


# --- Reception: search & invoice ---

@router.message(F.text == REC_SEARCH)
async def start_search(message: Message, state: FSMContext) -> None:
    await state.set_state(SearchRepair.query)
    await message.answer(
        '🔍 عبارت جستجو:\n'
        'شماره پرونده، نام مشتری، موبایل، مدل دستگاه یا ایراد',
        reply_markup=cancel_keyboard(),
    )


@router.message(SearchRepair.query)
async def run_search(message: Message, state: FSMContext, repo: RepairRepository) -> None:
    results = await repo.search_repairs(message.text.strip())
    await state.clear()
    await message.answer(
        format_search_results(results),
        parse_mode='Markdown',
        reply_markup=search_result_keyboard(results) if results else reception_menu(),
    )
    if results:
        await message.answer('یک پرونده را انتخاب کنید یا /repair شماره', reply_markup=reception_menu())


@router.message(F.text == REC_INVOICE)
async def start_invoice(message: Message, state: FSMContext) -> None:
    await state.set_state(InvoiceLookup.repair_id)
    await message.answer('شماره پرونده برای صدور فاکتور:', reply_markup=cancel_keyboard())


@router.message(InvoiceLookup.repair_id)
async def show_invoice(message: Message, state: FSMContext, repo: RepairRepository) -> None:
    if not message.text.strip().isdigit():
        await message.answer('لطفاً شماره پرونده را وارد کنید.')
        return
    repair = await repo.get_repair(int(message.text.strip()))
    await state.clear()
    if not repair:
        await message.answer('پرونده یافت نشد.', reply_markup=reception_menu())
        return
    await message.answer(format_invoice(repair), parse_mode='Markdown', reply_markup=reception_menu())


@router.message(F.text == REC_REPORT)
async def reception_report(message: Message, repo: RepairRepository) -> None:
    await show_accounting_report(message, repo)


# --- Accounting menu ---

@router.message(F.text == ACC_SUMMARY)
async def accounting_summary(message: Message, repo: RepairRepository) -> None:
    await show_accounting_report(message, repo)


@router.message(F.text == ACC_SHOP_PROFIT)
async def accounting_shop_profit(message: Message, repo: RepairRepository) -> None:
    dashboard = await repo.accounting_dashboard()
    await message.answer(
        f"🏢 **سود فروشگاه** (پرونده‌های باز)\n\n"
        f"💰 {format_toman(dashboard['shop_profit'])}\n\n"
        f"📂 تعداد پرونده: {dashboard['open_count']}",
        parse_mode='Markdown',
        reply_markup=accounting_menu(),
    )


@router.message(F.text == ACC_TECH_SHARE)
async def accounting_tech_share(message: Message, repo: RepairRepository) -> None:
    dashboard = await repo.accounting_dashboard()
    lines = ['👨‍🔧 **طلب تعمیرکاران**', '']
    if dashboard['technicians']:
        for row in dashboard['technicians']:
            lines.append(
                f"• {row['name']} ({row['pct']}%)\n"
                f"  سهم: {format_toman(int(row['share']))}\n"
                f"  پرداخت‌شده: {format_toman(int(row.get('paid') or 0))}\n"
                f"  **مانده طلب:** {format_toman(int(row.get('debt') or 0))}",
            )
    else:
        lines.append('• پرونده بازی با تعمیرکار ثبت نشده')
    lines.append(f"\n📊 **جمع مانده طلب:** {format_toman(dashboard.get('technician_debt', 0))}")
    await message.answer('\n'.join(lines), parse_mode='Markdown', reply_markup=accounting_menu())


@router.message(F.text == ACC_SUPPLIER_DEBT)
async def accounting_supplier_debt(message: Message, repo: RepairRepository) -> None:
    dashboard = await repo.accounting_dashboard()
    lines = ['🏪 **بدهی به قطعه‌فروش**', '']
    if dashboard['suppliers']:
        for row in dashboard['suppliers']:
            lines.append(f"• {row['name']}: {format_toman(int(row['debt']))}")
    else:
        lines.append('• بدهی فعالی ثبت نشده')
    lines.append(f"\n📊 **جمع:** {format_toman(dashboard['supplier_debt'])}")
    await message.answer('\n'.join(lines), parse_mode='Markdown', reply_markup=accounting_menu())


@router.message(F.text == ACC_CUSTOMER_DEBT)
async def accounting_customer_debt(message: Message, repo: RepairRepository) -> None:
    rows = await repo.customer_debts()
    lines = ['👥 **بدهی مشتریان**', '']
    if rows:
        for row in rows:
            lines.append(f"• {row['name']} ({row['phone'] or '—'}): {format_toman(int(row['debt']))}")
    else:
        lines.append('• بدهی فعالی ثبت نشده')
    dashboard = await repo.accounting_dashboard()
    lines.append(f"\n📊 **جمع:** {format_toman(dashboard['customer_debt'])}")
    await message.answer('\n'.join(lines), parse_mode='Markdown', reply_markup=accounting_menu())


@router.message(F.text == ACC_EXPORT_EXCEL)
async def export_accounting_excel(message: Message, export_service: ExportService) -> None:
    await message.answer('⏳ در حال ساخت فایل Excel...')
    path = await export_service.export_accounting_excel()
    await send_export_file(message, path, '📊 گزارش حسابداری Excel')


@router.message(F.text == ACC_EXPORT_PDF)
async def export_accounting_pdf(message: Message, export_service: ExportService) -> None:
    await message.answer('⏳ در حال ساخت فایل PDF...')
    path = await export_service.export_accounting_pdf()
    await send_export_file(message, path, '📄 گزارش حسابداری PDF')


# --- Callbacks ---

@router.callback_query(F.data.startswith('xlsx:'))
async def callback_invoice_excel(callback: CallbackQuery, export_service: ExportService) -> None:
    repair_id = int(callback.data.split(':')[1])
    path = await export_service.export_invoice_excel(repair_id)
    if not path:
        await callback.answer('پرونده یافت نشد', show_alert=True)
        return
    await callback.message.answer_document(
        FSInputFile(path),
        caption=f'📊 فاکتور Excel #{repair_id}',
    )
    await callback.answer()


@router.callback_query(F.data.startswith('pdf:'))
async def callback_invoice_pdf(callback: CallbackQuery, export_service: ExportService) -> None:
    repair_id = int(callback.data.split(':')[1])
    path = await export_service.export_invoice_pdf(repair_id)
    if not path:
        await callback.answer('پرونده یافت نشد', show_alert=True)
        return
    await callback.message.answer_document(
        FSInputFile(path),
        caption=f'📄 فاکتور PDF #{repair_id}',
    )
    await callback.answer()


@router.callback_query(F.data.startswith('view:'))
async def view_repair(callback: CallbackQuery, repo: RepairRepository, can_edit_repair: bool = False) -> None:
    repair_id = int(callback.data.split(':')[1])
    await show_repair(callback.message, repo, repair_id, can_edit_repair=can_edit_repair)
    await callback.answer()


@router.callback_query(F.data.startswith('inv:'))
async def callback_invoice(callback: CallbackQuery, repo: RepairRepository) -> None:
    repair_id = int(callback.data.split(':')[1])
    repair = await repo.get_repair(repair_id)
    if repair:
        await callback.message.answer(format_invoice(repair), parse_mode='Markdown')
    await callback.answer()


@router.callback_query(F.data.startswith('acc:'))
async def callback_accounting(callback: CallbackQuery, repo: RepairRepository) -> None:
    repair_id = int(callback.data.split(':')[1])
    repair = await repo.get_repair(repair_id)
    if repair:
        totals = repair['totals']
        await callback.message.answer(
            f"💼 حسابداری پرونده #{repair_id}\n\n"
            f"👨‍🔧 سهم تعمیرکار ({repair['technician_pct']}%): {format_toman(totals.technician_share)}\n"
            f"✅ پرداخت‌شده: {format_toman(totals.technician_paid)}\n"
            f"📋 مانده طلب: {format_toman(totals.technician_debt)}\n"
            f"🏪 بدهی قطعه‌فروش: {format_toman(totals.supplier_debt)}\n"
            f"📌 بدهی مشتری: {format_toman(totals.customer_debt)}\n"
            f"🏢 سود فروشگاه: {format_toman(totals.shop_profit)}",
        )
    await callback.answer()


@router.message(Command('repair'))
async def cmd_repair(message: Message, repo: RepairRepository, can_edit_repair: bool = False) -> None:
    parts = (message.text or '').split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer('استفاده: /repair 12')
        return
    await show_repair(message, repo, int(parts[1]), can_edit_repair=can_edit_repair)


@router.callback_query(F.data.startswith('pay_t:'))
async def pay_technician_start(callback: CallbackQuery, state: FSMContext) -> None:
    repair_id = int(callback.data.split(':')[1])
    await state.set_state(Payment.amount)
    await state.update_data(repair_id=repair_id, payment_kind='technician')
    await callback.message.answer(f'💸 مبلغ پرداختی به تعمیرکار — پرونده #{repair_id}:')
    await callback.answer()


@router.callback_query(F.data.startswith('pay_c:'))
async def pay_customer_start(callback: CallbackQuery, state: FSMContext) -> None:
    repair_id = int(callback.data.split(':')[1])
    await state.set_state(Payment.amount)
    await state.update_data(repair_id=repair_id, payment_kind='customer')
    await callback.message.answer(f'💵 مبلغ دریافتی از مشتری — پرونده #{repair_id}:')
    await callback.answer()


@router.callback_query(F.data.startswith('pay_s:'))
async def pay_supplier_start(callback: CallbackQuery, state: FSMContext) -> None:
    repair_id = int(callback.data.split(':')[1])
    await state.set_state(Payment.amount)
    await state.update_data(repair_id=repair_id, payment_kind='supplier')
    await callback.message.answer(f'💸 مبلغ پرداختی به قطعه‌فروش — پرونده #{repair_id}:')
    await callback.answer()


@router.message(Payment.amount)
async def payment_amount(
    message: Message,
    state: FSMContext,
    repo: RepairRepository,
    can_edit_repair: bool = False,
) -> None:
    if not message.text.strip().isdigit():
        await message.answer('لطفاً فقط عدد وارد کنید.')
        return
    amount = int(message.text.strip())
    if await process_settle_payment(message, state, repo, amount):
        return
    data = await state.get_data()
    repair_id = int(data['repair_id'])
    if data['payment_kind'] == 'customer':
        await repo.add_customer_payment(repair_id, amount)
    elif data['payment_kind'] == 'supplier':
        await repo.add_supplier_payment(repair_id, amount)
    else:
        await repo.add_technician_payment(repair_id, amount)
    repair = await repo.get_repair(repair_id)
    await state.clear()
    await message.answer(
        '✅ ثبت شد\n\n' + format_repair_summary(repair),
        reply_markup=repair_actions(
            repair_id,
            is_open=repair.get('status') == 'open',
            can_edit=can_edit_repair,
        ),
    )
    await message.answer('منوی حسابداری', reply_markup=accounting_menu())


@router.callback_query(F.data.startswith('close:'))
async def close_repair(callback: CallbackQuery, repo: RepairRepository) -> None:
    repair_id = int(callback.data.split(':')[1])
    await repo.close_repair(repair_id)
    await callback.message.answer(f'پرونده #{repair_id} بسته شد ✅', reply_markup=reception_menu())
    await callback.answer()


@router.message(Command('addstaff'))
async def cmd_addstaff(message: Message, repo: RepairRepository, staff_repo: StaffRepository, is_admin: bool) -> None:
    if not is_admin:
        await message.answer('فقط مدیر پرسنل می‌تواند پرسنل اضافه کند.')
        return
    parts = (message.text or '').split(maxsplit=1)
    if len(parts) < 2:
        await message.answer('استفاده: /addstaff 123456789|علی رضایی')
        return
    parsed = parse_staff_args(parts[1])
    if parsed is None:
        await message.answer('فرمت درست: /addstaff 123456789|نام\n(آیدی باید عدد باشد)')
        return
    telegram_id, name = parsed
    await staff_repo.add_staff(telegram_id, name)
    await message.answer(f'✅ پرسنل اضافه شد: {name.strip()} ({telegram_id})')


@router.message(Command('removestaff'))
async def cmd_removestaff(message: Message, staff_repo: StaffRepository, is_admin: bool) -> None:
    if not is_admin:
        await message.answer('فقط مدیر پرسنل می‌تواند پرسنل حذف کند.')
        return
    parts = (message.text or '').split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        await message.answer('استفاده: /removestaff 123456789')
        return
    telegram_id = int(parts[1].strip())
    if telegram_id == message.from_user.id:
        await message.answer('نمی‌توانید خودتان را حذف کنید.')
        return
    if await staff_repo.remove_staff(telegram_id):
        await message.answer(f'🚫 دسترسی پرسنل {telegram_id} غیرفعال شد.')
    else:
        await message.answer('پرسنل یافت نشد.')


@router.message(Command('staff'))
async def cmd_staff_list(message: Message, staff_repo: StaffRepository, is_admin: bool) -> None:
    if not is_admin:
        await message.answer('فقط مدیر می‌تواند لیست پرسنل را ببیند.')
        return
    rows = await staff_repo.list_staff()
    if not rows:
        await message.answer('پرسنلی ثبت نشده.')
        return
    lines = ['👥 **پرسنل مجاز**', '']
    for row in rows:
        role = ROLE_LABELS.get(row.get('role') or 'full', 'کارمند')
        lines.append(f"• {row['name']} — `{row['telegram_id']}` ({role})")
    lines.append('\nاز منوی ⚙️ مدیریت → 👥 پرسنل هم می‌توانید مدیریت کنید.')
    await message.answer('\n'.join(lines), parse_mode='Markdown')


@router.message(Command('addtech'))
async def cmd_addtech(message: Message, repo: RepairRepository, is_admin: bool) -> None:
    if not is_admin:
        await message.answer('فقط ادمین.')
        return
    parts = (message.text or '').split(maxsplit=1)
    if len(parts) < 2 or '|' not in parts[1]:
        await message.answer('استفاده: /addtech علی|40')
        return
    name, pct_raw = parts[1].split('|', 1)
    if not pct_raw.replace('.', '', 1).isdigit():
        await message.answer('درصد نامعتبر.')
        return
    tech_id = await repo.add_technician(name, float(pct_raw))
    await message.answer(f'تعمیرکار #{tech_id} ثبت شد: {name.strip()} ({pct_raw}%)')


@router.message(AddTechnician.name)
async def add_technician_name(message: Message, state: FSMContext) -> None:
    await state.update_data(tech_name=message.text.strip())
    await state.set_state(AddTechnician.pct)
    await message.answer('درصد سهم تعمیرکار (مثلاً 40):')


@router.message(AddTechnician.pct)
async def add_technician_pct(message: Message, state: FSMContext, repo: RepairRepository) -> None:
    if not message.text.strip().replace('.', '', 1).isdigit():
        await message.answer('درصد نامعتبر.')
        return
    data = await state.get_data()
    tech_id = await repo.add_technician(data['tech_name'], float(message.text.strip()))
    pct = float(message.text.strip())
    await state.update_data(technician_id=tech_id, technician_pct=pct)
    await state.set_state(NewRepair.labor_amount)
    await message.answer(
        f"تعمیرکار {data['tech_name']} ({pct}%) ثبت شد.\n"
        'مبلغ اجرت تعمیر (تومان):',
        reply_markup=cancel_keyboard(),
    )


@router.message(Command('addsup'))
async def cmd_addsup(message: Message, repo: RepairRepository, is_admin: bool) -> None:
    if not is_admin:
        await message.answer('فقط ادمین.')
        return
    parts = (message.text or '').split(maxsplit=1)
    if len(parts) < 2:
        await message.answer('استفاده: /addsup رضایی')
        return
    sup_id = await repo.add_supplier(parts[1])
    await message.answer(f'قطعه‌فروش #{sup_id} ثبت شد.')


@router.message(AddSupplier.name)
async def add_supplier_name(message: Message, state: FSMContext, repo: RepairRepository) -> None:
    sup_id = await repo.add_supplier(message.text.strip())
    data = await state.get_data()
    part = data.get('current_part', {})
    part['supplier_id'] = sup_id
    await state.update_data(current_part=part)
    await append_part(message, state)


def create_dispatcher(
    repo: RepairRepository,
    export_service: ExportService,
    staff_repo: StaffRepository,
) -> Dispatcher:
    dp = Dispatcher()
    dp.update.middleware(StaffGuardMiddleware(staff_repo))
    dp.update.middleware(RepositoryMiddleware(repo, export_service, staff_repo))
    dp.include_router(settle_router)
    dp.include_router(edit_router)
    dp.include_router(admin_router)
    dp.include_router(router)
    return dp


async def run_bot() -> None:
    db = Database(settings.DATABASE_PATH)
    conn = await db.connect()
    staff_repo = StaffRepository(conn)
    if not settings.allowed_user_ids() and await staff_repo.active_staff_count() == 0:
        raise RuntimeError(
            'ALLOWED_USER_IDS is empty and no staff in database — set at least one Telegram user ID',
        )
    await staff_repo.seed_from_env()
    repo = RepairRepository(conn)
    export_service = ExportService(repo, Path(settings.EXPORT_DIR))
    session = AiohttpSession(proxy=settings.TELEGRAM_PROXY) if settings.TELEGRAM_PROXY else None
    bot = Bot(token=settings.BOT_TOKEN, session=session)
    dp = create_dispatcher(repo, export_service, staff_repo)
    await dp.start_polling(bot)
