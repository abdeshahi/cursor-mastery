from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import (
    accounting_menu,
    settle_action_keyboard,
    settle_kind_keyboard,
    settle_payee_keyboard,
    settle_receive_action_keyboard,
    settle_repair_keyboard,
)
from app.bot.menu_filter import MenuFilter
from app.bot.states import Payment, SettlePayment
from app.ui.themes import Theme
from app.services.accounting import format_toman
from app.storage.repository import RepairRepository

settle_router = Router()

PAYEE_HINT = (
    '💡 **پرداخت جزئی:**\n'
    '• مبلغ را همین‌جا بفرستید (مثلاً `550000`) و بعد طرف حساب را انتخاب کنید\n'
    '• یا بعد از انتخاب، **✏️ مبلغ جزئی** را بزنید'
)

RECEIVE_HINT = (
    '💡 **دریافت جزئی:**\n'
    '• مبلغ را همین‌جا بفرستید (مثلاً `550000`) و بعد مشتری را انتخاب کنید\n'
    '• یا بعد از انتخاب، **✏️ مبلغ جزئی** را بزنید'
)


def _settle_prefix(kind: str | None) -> str:
    if kind == 'technician':
        return '👨‍🔧'
    if kind == 'customer':
        return '👥'
    return '🏪'


async def _show_settle_actions(
    message: Message,
    name: str,
    debt: int,
    prefix: str,
    *,
    receive: bool = False,
) -> None:
    action = 'دریافت' if receive else 'پرداخت'
    keyboard = settle_receive_action_keyboard() if receive else settle_action_keyboard()
    await message.answer(
        f'{prefix} **{name}**\n'
        f'مانده: **{format_toman(debt)}**\n\n'
        f'نوع {action} را انتخاب کنید:',
        parse_mode='Markdown',
        reply_markup=keyboard,
    )


async def _finish_settle(
    message: Message,
    state: FSMContext,
    applied: list[tuple[int, int]],
    *,
    name: str,
    theme: Theme,
    receive: bool = False,
) -> None:
    await state.clear()
    if not applied:
        await message.answer('مبلغی ثبت نشد یا بدهی باقی نمانده.', reply_markup=accounting_menu(theme))
        return
    total = sum(amount for _, amount in applied)
    verb = 'دریافت' if receive else 'پرداخت'
    lines = [f'✅ {verb} ثبت شد — {name}', f'جمع: {format_toman(total)}', '']
    for repair_id, amount in applied:
        lines.append(f'• پرونده #{repair_id}: {format_toman(amount)}')
    await message.answer('\n'.join(lines), reply_markup=accounting_menu(theme))


async def _apply_settle_payment(
    repo: RepairRepository,
    *,
    kind: str,
    entity_id: int,
    amount: int,
    repair_id: int | None = None,
) -> list[tuple[int, int]]:
    if kind == 'technician':
        return await repo.allocate_technician_payment(entity_id, amount, repair_id=repair_id)
    if kind == 'customer':
        return await repo.allocate_customer_payment(entity_id, amount, repair_id=repair_id)
    return await repo.allocate_supplier_payment(entity_id, amount, repair_id=repair_id)


async def _finalize_payee_selection(
    callback: CallbackQuery,
    state: FSMContext,
    repo: RepairRepository,
    theme: Theme,
    *,
    kind: str,
    entity_id: int,
    name: str,
    debt: int,
    prefix: str,
    receive: bool = False,
) -> None:
    data = await state.get_data()
    preset = data.get('settle_preset_amount')
    if preset is not None:
        amount = int(preset)
        applied = await _apply_settle_payment(
            repo,
            kind=kind,
            entity_id=entity_id,
            amount=amount,
        )
        await _finish_settle(callback.message, state, applied, name=name, theme=theme, receive=receive)
        await callback.answer('ثبت شد ✅')
        return

    await state.set_state(None)
    await _show_settle_actions(callback.message, name, debt, prefix, receive=receive)
    await callback.answer()


@settle_router.message(MenuFilter('acc_pay_debt'))
async def accounting_pay_debt_start(message: Message, state: FSMContext, theme: Theme) -> None:
    await state.clear()
    await message.answer(
        '💸 **ثبت پرداخت بدهی**\n\n'
        'پرداخت به تعمیرکار یا فروشنده قطعه (جزئی یا کامل):',
        parse_mode='Markdown',
        reply_markup=settle_kind_keyboard(),
    )


@settle_router.message(MenuFilter('acc_receive_customer'))
async def accounting_receive_customer_start(message: Message, state: FSMContext, repo: RepairRepository, theme: Theme) -> None:
    customers = await repo.customers_with_debt()
    if not customers:
        await message.answer('بدهی فعالی از مشتری نیست.', reply_markup=accounting_menu(theme))
        return
    await state.clear()
    await state.set_state(SettlePayment.choose_payee)
    await state.update_data(settle_kind='customer')
    await message.answer(
        '💵 **دریافت از مشتری**\n\n'
        'مشتری را انتخاب کنید:\n\n' + RECEIVE_HINT,
        parse_mode='Markdown',
        reply_markup=settle_payee_keyboard(customers, kind='cust'),
    )


@settle_router.callback_query(F.data == 'settle:cancel')
async def settle_cancel(callback: CallbackQuery, state: FSMContext, theme: Theme) -> None:
    await state.clear()
    await callback.message.answer('لغو شد.', reply_markup=accounting_menu(theme))
    await callback.answer()


@settle_router.callback_query(F.data == 'settle:kind:tech')
async def settle_pick_technician(callback: CallbackQuery, state: FSMContext, repo: RepairRepository) -> None:
    payees = await repo.technicians_with_debt()
    if not payees:
        await callback.answer('طلب فعالی برای تعمیرکار نیست', show_alert=True)
        return
    await state.clear()
    await state.set_state(SettlePayment.choose_payee)
    await state.update_data(settle_kind='technician')
    await callback.message.answer(
        '👨‍🔧 **تعمیرکار را انتخاب کنید:**\n\n' + PAYEE_HINT,
        parse_mode='Markdown',
        reply_markup=settle_payee_keyboard(payees, kind='tech'),
    )
    await callback.answer()


@settle_router.callback_query(F.data == 'settle:kind:sup')
async def settle_pick_supplier(callback: CallbackQuery, state: FSMContext, repo: RepairRepository) -> None:
    payees = await repo.suppliers_with_debt()
    if not payees:
        await callback.answer('بدهی فعالی به فروشنده نیست', show_alert=True)
        return
    await state.clear()
    await state.set_state(SettlePayment.choose_payee)
    await state.update_data(settle_kind='supplier')
    await callback.message.answer(
        '🏪 **فروشنده را انتخاب کنید:**\n\n' + PAYEE_HINT,
        parse_mode='Markdown',
        reply_markup=settle_payee_keyboard(payees, kind='sup'),
    )
    await callback.answer()


@settle_router.callback_query(F.data.startswith('settle:tech:'))
async def settle_technician_selected(callback: CallbackQuery, state: FSMContext, repo: RepairRepository) -> None:
    tech_id = int(callback.data.split(':')[-1])
    payees = await repo.technicians_with_debt()
    tech = next((p for p in payees if int(p['id']) == tech_id), None)
    if not tech:
        await callback.answer('طلبی باقی نمانده', show_alert=True)
        return
    await state.update_data(
        settle_kind='technician',
        settle_entity_id=tech_id,
        settle_name=tech['name'],
        settle_total_debt=int(tech['debt']),
    )
    await _finalize_payee_selection(
        callback,
        state,
        repo,
        theme,
        kind='technician',
        entity_id=tech_id,
        name=tech['name'],
        debt=int(tech['debt']),
        prefix='👨‍🔧',
    )


@settle_router.callback_query(F.data.startswith('settle:sup:'))
async def settle_supplier_selected(callback: CallbackQuery, state: FSMContext, repo: RepairRepository) -> None:
    sup_id = int(callback.data.split(':')[-1])
    payees = await repo.suppliers_with_debt()
    sup = next((p for p in payees if int(p['id']) == sup_id), None)
    if not sup:
        await callback.answer('بدهی باقی نمانده', show_alert=True)
        return
    await state.update_data(
        settle_kind='supplier',
        settle_entity_id=sup_id,
        settle_name=sup['name'],
        settle_total_debt=int(sup['debt']),
    )
    await _finalize_payee_selection(
        callback,
        state,
        repo,
        theme,
        kind='supplier',
        entity_id=sup_id,
        name=sup['name'],
        debt=int(sup['debt']),
        prefix='🏪',
    )


@settle_router.callback_query(F.data.startswith('settle:cust:'))
async def settle_customer_selected(callback: CallbackQuery, state: FSMContext, repo: RepairRepository) -> None:
    cust_id = int(callback.data.split(':')[-1])
    customers = await repo.customers_with_debt()
    customer = next((c for c in customers if int(c['id']) == cust_id), None)
    if not customer:
        await callback.answer('بدهی باقی نمانده', show_alert=True)
        return
    await state.update_data(
        settle_kind='customer',
        settle_entity_id=cust_id,
        settle_name=customer['name'],
        settle_total_debt=int(customer['debt']),
    )
    await _finalize_payee_selection(
        callback,
        state,
        repo,
        theme,
        kind='customer',
        entity_id=cust_id,
        name=customer['name'],
        debt=int(customer['debt']),
        prefix='👥',
        receive=True,
    )


@settle_router.message(SettlePayment.choose_payee, F.text.regexp(r'^\d+$'))
async def settle_preset_amount(message: Message, state: FSMContext) -> None:
    amount = int(message.text.strip())
    if amount <= 0:
        await message.answer('مبلغ باید بزرگ‌تر از صفر باشد.')
        return
    await state.update_data(settle_preset_amount=amount)
    await message.answer(
        f'💵 مبلغ **{format_toman(amount)}** ثبت شد.\n'
        'حالا طرف حساب را از دکمه‌های بالا انتخاب کنید.',
        parse_mode='Markdown',
    )


@settle_router.callback_query(F.data == 'settle:full')
async def settle_pay_full(callback: CallbackQuery, state: FSMContext, repo: RepairRepository, theme: Theme) -> None:
    data = await state.get_data()
    kind = data.get('settle_kind')
    entity_id = data.get('settle_entity_id')
    name = data.get('settle_name', '')
    repair_id = data.get('settle_repair_id')
    receive = kind == 'customer'
    if not kind or entity_id is None:
        await callback.answer('ابتدا طرف حساب را انتخاب کنید', show_alert=True)
        return

    if kind == 'technician':
        if repair_id:
            repairs = await repo.repairs_with_technician_debt(int(entity_id))
            amount = next((int(r['debt']) for r in repairs if int(r['id']) == int(repair_id)), 0)
        else:
            amount = int(data.get('settle_total_debt') or 0)
        applied = await _apply_settle_payment(
            repo, kind='technician', entity_id=int(entity_id), amount=amount, repair_id=repair_id
        )
    elif kind == 'customer':
        if repair_id:
            repairs = await repo.repairs_with_customer_debt(int(entity_id))
            amount = next((int(r['debt']) for r in repairs if int(r['id']) == int(repair_id)), 0)
        else:
            amount = int(data.get('settle_total_debt') or 0)
        applied = await _apply_settle_payment(
            repo, kind='customer', entity_id=int(entity_id), amount=amount, repair_id=repair_id
        )
    else:
        if repair_id:
            repairs = await repo.repairs_with_supplier_debt(int(entity_id))
            amount = next((int(r['debt']) for r in repairs if int(r['id']) == int(repair_id)), 0)
        else:
            amount = int(data.get('settle_total_debt') or 0)
        applied = await _apply_settle_payment(
            repo, kind='supplier', entity_id=int(entity_id), amount=amount, repair_id=repair_id
        )

    await _finish_settle(callback.message, state, applied, name=name, theme=theme, receive=receive)
    await callback.answer('ثبت شد ✅')


@settle_router.callback_query(F.data == 'settle:custom')
async def settle_pay_custom(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get('settle_entity_id'):
        await callback.answer('ابتدا طرف حساب را انتخاب کنید', show_alert=True)
        return
    await state.set_state(Payment.amount)
    await state.update_data(settle_mode=True)
    label = 'دریافتی' if data.get('settle_kind') == 'customer' else 'پرداختی'
    await callback.message.answer(f'💵 مبلغ {label} (تومان) را وارد کنید:')
    await callback.answer()


@settle_router.callback_query(F.data == 'settle:pick')
async def settle_pick_repair(callback: CallbackQuery, state: FSMContext, repo: RepairRepository) -> None:
    data = await state.get_data()
    kind = data.get('settle_kind')
    entity_id = data.get('settle_entity_id')
    if not kind or entity_id is None:
        await callback.answer('ابتدا طرف حساب را انتخاب کنید', show_alert=True)
        return
    if kind == 'technician':
        repairs = await repo.repairs_with_technician_debt(int(entity_id))
    elif kind == 'customer':
        repairs = await repo.repairs_with_customer_debt(int(entity_id))
    else:
        repairs = await repo.repairs_with_supplier_debt(int(entity_id))
    if not repairs:
        await callback.answer('پرونده با بدهی باز یافت نشد', show_alert=True)
        return
    await callback.message.answer(
        'پرونده را انتخاب کنید:',
        reply_markup=settle_repair_keyboard(repairs),
    )
    await callback.answer()


@settle_router.callback_query(F.data == 'settle:back')
async def settle_back_to_actions(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    kind = data.get('settle_kind')
    name = data.get('settle_name', '')
    debt = int(data.get('settle_total_debt') or 0)
    await state.update_data(settle_repair_id=None)
    await _show_settle_actions(
        callback.message,
        name,
        debt,
        _settle_prefix(kind),
        receive=kind == 'customer',
    )
    await callback.answer()


@settle_router.callback_query(F.data.startswith('settle:repair:'))
async def settle_repair_selected(callback: CallbackQuery, state: FSMContext, repo: RepairRepository) -> None:
    repair_id = int(callback.data.split(':')[-1])
    data = await state.get_data()
    kind = data.get('settle_kind')
    entity_id = data.get('settle_entity_id')
    receive = kind == 'customer'
    if not kind or entity_id is None:
        await callback.answer('خطا — دوباره تلاش کنید', show_alert=True)
        return

    if kind == 'technician':
        repairs = await repo.repairs_with_technician_debt(int(entity_id))
    elif kind == 'customer':
        repairs = await repo.repairs_with_customer_debt(int(entity_id))
    else:
        repairs = await repo.repairs_with_supplier_debt(int(entity_id))
    repair = next((r for r in repairs if int(r['id']) == repair_id), None)
    if not repair:
        await callback.answer('بدهی این پرونده تسویه شده', show_alert=True)
        return

    await state.update_data(settle_repair_id=repair_id, settle_repair_debt=int(repair['debt']))
    action = 'دریافت' if receive else 'پرداخت'
    keyboard = settle_receive_action_keyboard() if receive else settle_action_keyboard()
    await callback.message.answer(
        f"📋 پرونده #{repair_id} — {repair.get('customer_name', '')}\n"
        f"مانده: **{format_toman(int(repair['debt']))}**\n\n"
        f'نوع {action} را انتخاب کنید:',
        parse_mode='Markdown',
        reply_markup=keyboard,
    )
    await callback.answer()


async def process_settle_payment(message: Message, state: FSMContext, repo: RepairRepository, amount: int, theme: Theme) -> bool:
    data = await state.get_data()
    if not data.get('settle_mode'):
        return False

    kind = data.get('settle_kind')
    entity_id = data.get('settle_entity_id')
    name = data.get('settle_name', '')
    repair_id = data.get('settle_repair_id')
    receive = kind == 'customer'
    if not kind or entity_id is None:
        await state.clear()
        await message.answer('خطا — دوباره از منوی حسابداری شروع کنید.', reply_markup=accounting_menu(theme))
        return True

    if kind == 'technician':
        applied = await _apply_settle_payment(
            repo,
            kind='technician',
            entity_id=int(entity_id),
            amount=amount,
            repair_id=int(repair_id) if repair_id else None,
        )
    elif kind == 'customer':
        applied = await _apply_settle_payment(
            repo,
            kind='customer',
            entity_id=int(entity_id),
            amount=amount,
            repair_id=int(repair_id) if repair_id else None,
        )
    else:
        applied = await _apply_settle_payment(
            repo,
            kind='supplier',
            entity_id=int(entity_id),
            amount=amount,
            repair_id=int(repair_id) if repair_id else None,
        )

    await _finish_settle(message, state, applied, name=name, theme=theme, receive=receive)
    return True
