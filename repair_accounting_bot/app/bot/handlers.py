from __future__ import annotations

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import (
    cancel_keyboard,
    main_menu,
    parts_more_keyboard,
    repair_actions,
    skip_keyboard,
    supplier_keyboard,
    technician_keyboard,
)
from app.bot.middleware import RepositoryMiddleware
from app.bot.states import AddSupplier, AddTechnician, NewRepair, Payment
from app.config import settings
from app.services.accounting import format_toman
from app.storage.db import Database
from app.storage.repository import RepairRepository

router = Router()


def is_allowed(user_id: int | None) -> bool:
    return user_id is not None and user_id in settings.allowed_user_ids()


def is_admin(user_id: int | None) -> bool:
    return user_id is not None and user_id in settings.admin_user_ids()


def deny_message() -> str:
    return '⛔️ شما دسترسی به این ربات را ندارید.'


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    if not is_allowed(message.from_user.id if message.from_user else None):
        await message.answer(deny_message())
        return
    await state.clear()
    await message.answer(
        '🔧 ربات حسابداری تعمیرات\n\n'
        'پذیرش دستگاه، ثبت درصد تعمیرکار، قیمت قطعه، بدهی مشتری و طلب قطعه‌فروش.',
        reply_markup=main_menu(),
    )


@router.message(Command('help'))
@router.message(F.text == 'ℹ️ راهنما')
async def cmd_help(message: Message) -> None:
    if not is_allowed(message.from_user.id if message.from_user else None):
        await message.answer(deny_message())
        return
    await message.answer(
        '📝 **پذیرش جدید** — ثبت مشتری، دستگاه، تعمیرکار، اجرت و قطعات\n'
        '📋 **پرونده‌های باز** — لیست تعمیرات جاری\n'
        '💵 **دریافت از مشتری** — از دکمه‌های زیر هر پرونده\n'
        '💸 **پرداخت به قطعه‌فروش** — ثبت پرداخت به فروشنده قطعه\n'
        '💰 **گزارش بدهی‌ها** — جمع بدهی مشتریان و طلب قطعه‌فروش‌ها\n\n'
        'دستورات:\n'
        '/repair 12 — جزئیات پرونده\n'
        '/addtech نام|40 — افزودن تعمیرکار با درصد\n'
        '/addsup نام — افزودن قطعه‌فروش',
        parse_mode='Markdown',
    )


@router.message(F.text == '❌ انصراف')
async def cancel_flow(message: Message, state: FSMContext) -> None:
    if not is_allowed(message.from_user.id if message.from_user else None):
        return
    await state.clear()
    await message.answer('لغو شد.', reply_markup=main_menu())


@router.message(F.text == '📝 پذیرش جدید')
async def start_repair(message: Message, state: FSMContext) -> None:
    if not is_allowed(message.from_user.id if message.from_user else None):
        await message.answer(deny_message())
        return
    await state.clear()
    await state.set_state(NewRepair.customer_name)
    await state.update_data(parts=[])
    await message.answer('نام مشتری را وارد کنید:', reply_markup=cancel_keyboard())


@router.message(NewRepair.customer_name)
async def repair_customer_name(message: Message, state: FSMContext) -> None:
    await state.update_data(customer_name=message.text.strip())
    await state.set_state(NewRepair.customer_phone)
    await message.answer('شماره تماس مشتری (اختیاری — برای `-` بگذارید):')


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
    if not is_allowed(callback.from_user.id):
        await callback.answer(deny_message(), show_alert=True)
        return
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
        'مبلغ اجرت تعمیر (تومان، فقط عدد):',
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
    await message.answer(
        'نام قطعه (یا «⏭ بدون قطعه / ادامه»):',
        reply_markup=skip_keyboard(),
    )


@router.message(NewRepair.part_name, F.text == '⏭ بدون قطعه / ادامه')
async def repair_no_parts(message: Message, state: FSMContext, repo: RepairRepository) -> None:
    await finalize_repair(message, state, repo)


@router.message(NewRepair.part_name)
async def repair_part_name(message: Message, state: FSMContext) -> None:
    if message.text in {'✅ ثبت نهایی پذیرش', '➕ قطعه دیگر'}:
        return
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
        await message.answer('نام فروشنده قطعه را تایپ کنید (یا `-`):')


@router.callback_query(F.data.startswith('sup:'))
async def pick_supplier(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_allowed(callback.from_user.id):
        await callback.answer(deny_message(), show_alert=True)
        return
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
        'قطعه دیگر اضافه کنید یا «✅ ثبت نهایی پذیرش»:',
        reply_markup=parts_more_keyboard(),
    )


@router.message(NewRepair.part_name, F.text == '✅ ثبت نهایی پذیرش')
async def repair_finalize_button(message: Message, state: FSMContext, repo: RepairRepository) -> None:
    await finalize_repair(message, state, repo)


@router.message(NewRepair.part_name, F.text == '➕ قطعه دیگر')
async def repair_add_more_part(message: Message, state: FSMContext) -> None:
    await message.answer('نام قطعه بعدی:', reply_markup=cancel_keyboard())


async def finalize_repair(message: Message, state: FSMContext, repo: RepairRepository) -> None:
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
    await message.answer(format_repair(repair), reply_markup=repair_actions(repair_id))
    await message.answer('پذیرش ثبت شد ✅', reply_markup=main_menu())


def format_repair(repair: dict) -> str:
    totals = repair['totals']
    parts_lines = '\n'.join(
        f"  • {p['part_name']}: خرید {format_toman(int(p['cost']))} → فروش {format_toman(int(p['sell_price']))}"
        for p in repair['parts']
    ) or '  • بدون قطعه'
    return (
        f"📋 پرونده #{repair['id']} ({repair['status']})\n"
        f"👤 {repair['customer_name']} | {repair['customer_phone'] or '—'}\n"
        f"📱 {repair['device']}\n"
        f"🔧 {repair['issue']}\n"
        f"👨‍🔧 {repair['technician_name'] or '—'} ({repair['technician_pct']}%)\n\n"
        f"💼 اجرت: {format_toman(totals.labor_amount)}\n"
        f"🔩 قطعات:\n{parts_lines}\n\n"
        f"🧾 جمع مشتری: {format_toman(totals.customer_total)}\n"
        f"✅ دریافت‌شده: {format_toman(totals.customer_paid)}\n"
        f"📌 بدهی مشتری: {format_toman(totals.customer_debt)}\n"
        f"🏪 طلب قطعه‌فروش: {format_toman(totals.supplier_debt)}\n"
        f"👨‍🔧 سهم تعمیرکار: {format_toman(totals.technician_share)}\n"
        f"🏢 سود مغازه: {format_toman(totals.shop_profit)}"
    )


@router.message(F.text == '📋 پرونده‌های باز')
async def list_open(message: Message, repo: RepairRepository) -> None:
    if not is_allowed(message.from_user.id if message.from_user else None):
        await message.answer(deny_message())
        return
    repairs = await repo.list_open_repairs()
    if not repairs:
        await message.answer('پرونده بازی وجود ندارد.')
        return
    lines = []
    for r in repairs:
        debt = int(r['customer_debt'] or 0)
        lines.append(
            f"#{r['id']} | {r['customer_name']} | {r['device']} | بدهی {format_toman(debt)}",
        )
    await message.answer('\n'.join(lines))


@router.message(Command('repair'))
async def cmd_repair(message: Message, repo: RepairRepository) -> None:
    if not is_allowed(message.from_user.id if message.from_user else None):
        await message.answer(deny_message())
        return
    parts = (message.text or '').split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer('استفاده: /repair 12')
        return
    repair = await repo.get_repair(int(parts[1]))
    if not repair:
        await message.answer('پرونده یافت نشد.')
        return
    repair_id = int(parts[1])
    await message.answer(format_repair(repair), reply_markup=repair_actions(repair_id))


@router.message(F.text == '💰 گزارش بدهی‌ها')
async def report_summary(message: Message, repo: RepairRepository) -> None:
    if not is_allowed(message.from_user.id if message.from_user else None):
        await message.answer(deny_message())
        return
    summary = await repo.summary_report()
    await message.answer(
        f"📊 گزارش کلی\n\n"
        f"📂 پرونده باز: {summary['open_count']}\n"
        f"📌 جمع بدهی مشتریان: {format_toman(summary['customer_debt'])}\n"
        f"🏪 جمع طلب قطعه‌فروش‌ها: {format_toman(summary['supplier_debt'])}\n"
        f"👨‍🔧 سهم تعمیرکاران (پرونده باز): {format_toman(summary['technician_share_open'])}",
    )


@router.message(F.text == '👥 بدهی مشتریان')
async def report_customers(message: Message, repo: RepairRepository) -> None:
    if not is_allowed(message.from_user.id if message.from_user else None):
        await message.answer(deny_message())
        return
    rows = await repo.customer_debts()
    if not rows:
        await message.answer('بدهی فعالی ثبت نشده.')
        return
    lines = [f"{r['name']} ({r['phone'] or '—'}): {format_toman(int(r['debt']))}" for r in rows]
    await message.answer('\n'.join(lines))


@router.callback_query(F.data.startswith('pay_c:'))
async def pay_customer_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_allowed(callback.from_user.id):
        await callback.answer(deny_message(), show_alert=True)
        return
    repair_id = int(callback.data.split(':')[1])
    await state.set_state(Payment.amount)
    await state.update_data(repair_id=repair_id, payment_kind='customer')
    await callback.message.answer(f'مبلغ دریافتی از مشتری برای #{repair_id} (تومان):')
    await callback.answer()


@router.callback_query(F.data.startswith('pay_s:'))
async def pay_supplier_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_allowed(callback.from_user.id):
        await callback.answer(deny_message(), show_alert=True)
        return
    repair_id = int(callback.data.split(':')[1])
    await state.set_state(Payment.amount)
    await state.update_data(repair_id=repair_id, payment_kind='supplier')
    await callback.message.answer(f'مبلغ پرداختی به قطعه‌فروش برای #{repair_id} (تومان):')
    await callback.answer()


@router.message(Payment.amount)
async def payment_amount(message: Message, state: FSMContext, repo: RepairRepository) -> None:
    if not message.text.strip().isdigit():
        await message.answer('لطفاً فقط عدد وارد کنید.')
        return
    data = await state.get_data()
    repair_id = int(data['repair_id'])
    amount = int(message.text.strip())
    if data['payment_kind'] == 'customer':
        await repo.add_customer_payment(repair_id, amount)
    else:
        await repo.add_supplier_payment(repair_id, amount)
    repair = await repo.get_repair(repair_id)
    await state.clear()
    await message.answer('ثبت شد ✅\n\n' + format_repair(repair), reply_markup=repair_actions(repair_id))
    await message.answer('منوی اصلی', reply_markup=main_menu())


@router.callback_query(F.data.startswith('close:'))
async def close_repair(callback: CallbackQuery, repo: RepairRepository) -> None:
    if not is_allowed(callback.from_user.id):
        await callback.answer(deny_message(), show_alert=True)
        return
    repair_id = int(callback.data.split(':')[1])
    await repo.close_repair(repair_id)
    await callback.message.answer(f'پرونده #{repair_id} بسته شد ✅')
    await callback.answer()


@router.message(Command('addtech'))
async def cmd_addtech(message: Message, repo: RepairRepository) -> None:
    if not is_admin(message.from_user.id if message.from_user else None):
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
    await state.update_data(technician_id=tech_id, technician_pct=float(message.text.strip()))
    await state.set_state(NewRepair.labor_amount)
    await message.answer(
        f"تعمیرکار {data['tech_name']} ثبت شد.\n"
        'مبلغ اجرت تعمیر (تومان):',
        reply_markup=cancel_keyboard(),
    )


@router.message(Command('addsup'))
async def cmd_addsup(message: Message, repo: RepairRepository) -> None:
    if not is_admin(message.from_user.id if message.from_user else None):
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


def create_dispatcher(repo: RepairRepository) -> Dispatcher:
    dp = Dispatcher()
    dp.update.middleware(RepositoryMiddleware(repo))
    dp.include_router(router)
    return dp


async def run_bot() -> None:
    if not settings.allowed_user_ids():
        raise RuntimeError('ALLOWED_USER_IDS is empty — set at least one Telegram user ID')
    db = Database(settings.DATABASE_PATH)
    conn = await db.connect()
    repo = RepairRepository(conn)
    bot = Bot(token=settings.BOT_TOKEN)
    dp = create_dispatcher(repo)
    await dp.start_polling(bot)
