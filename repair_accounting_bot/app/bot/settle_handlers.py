from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import (
    ACC_PAY_DEBT,
    accounting_menu,
    settle_action_keyboard,
    settle_kind_keyboard,
    settle_payee_keyboard,
    settle_repair_keyboard,
)
from app.bot.states import Payment
from app.services.accounting import format_toman
from app.storage.repository import RepairRepository

settle_router = Router()


async def _show_settle_actions(message: Message, state: FSMContext, name: str, debt: int, prefix: str) -> None:
    await message.answer(
        f'{prefix} **{name}**\n'
        f'مانده: **{format_toman(debt)}**\n\n'
        'نوع پرداخت را انتخاب کنید:',
        parse_mode='Markdown',
        reply_markup=settle_action_keyboard(),
    )


async def _finish_settle(
    message: Message,
    state: FSMContext,
    repo: RepairRepository,
    applied: list[tuple[int, int]],
    *,
    name: str,
) -> None:
    await state.clear()
    if not applied:
        await message.answer('مبلغی ثبت نشد یا بدهی باقی نمانده.', reply_markup=accounting_menu())
        return
    total = sum(amount for _, amount in applied)
    lines = [f'✅ پرداخت ثبت شد — {name}', f'جمع: {format_toman(total)}', '']
    for repair_id, amount in applied:
        lines.append(f'• پرونده #{repair_id}: {format_toman(amount)}')
    await message.answer('\n'.join(lines), reply_markup=accounting_menu())


@settle_router.message(F.text == ACC_PAY_DEBT)
async def accounting_pay_debt_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        '💸 **ثبت پرداخت بدهی**\n\n'
        'پرداخت به تعمیرکار یا فروشنده قطعه (جزئی یا کامل):',
        parse_mode='Markdown',
        reply_markup=settle_kind_keyboard(),
    )


@settle_router.callback_query(F.data == 'settle:cancel')
async def settle_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer('لغو شد.', reply_markup=accounting_menu())
    await callback.answer()


@settle_router.callback_query(F.data == 'settle:kind:tech')
async def settle_pick_technician(callback: CallbackQuery, state: FSMContext, repo: RepairRepository) -> None:
    payees = await repo.technicians_with_debt()
    if not payees:
        await callback.answer('طلب فعالی برای تعمیرکار نیست', show_alert=True)
        return
    await state.clear()
    await state.update_data(settle_kind='technician')
    await callback.message.answer(
        '👨‍🔧 تعمیرکار را انتخاب کنید:',
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
    await state.update_data(settle_kind='supplier')
    await callback.message.answer(
        '🏪 فروشنده را انتخاب کنید:',
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
    await _show_settle_actions(callback.message, state, tech['name'], int(tech['debt']), '👨‍🔧')
    await callback.answer()


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
    await _show_settle_actions(callback.message, state, sup['name'], int(sup['debt']), '🏪')
    await callback.answer()


@settle_router.callback_query(F.data == 'settle:full')
async def settle_pay_full(callback: CallbackQuery, state: FSMContext, repo: RepairRepository) -> None:
    data = await state.get_data()
    kind = data.get('settle_kind')
    entity_id = data.get('settle_entity_id')
    name = data.get('settle_name', '')
    repair_id = data.get('settle_repair_id')
    if not kind or entity_id is None:
        await callback.answer('ابتدا طرف حساب را انتخاب کنید', show_alert=True)
        return

    if kind == 'technician':
        if repair_id:
            repairs = await repo.repairs_with_technician_debt(int(entity_id))
            amount = next((int(r['debt']) for r in repairs if int(r['id']) == int(repair_id)), 0)
            applied = await repo.allocate_technician_payment(int(entity_id), amount, repair_id=int(repair_id))
        else:
            amount = int(data.get('settle_total_debt') or 0)
            applied = await repo.allocate_technician_payment(int(entity_id), amount)
    else:
        if repair_id:
            repairs = await repo.repairs_with_supplier_debt(int(entity_id))
            amount = next((int(r['debt']) for r in repairs if int(r['id']) == int(repair_id)), 0)
            applied = await repo.allocate_supplier_payment(int(entity_id), amount, repair_id=int(repair_id))
        else:
            amount = int(data.get('settle_total_debt') or 0)
            applied = await repo.allocate_supplier_payment(int(entity_id), amount)

    await _finish_settle(callback.message, state, repo, applied, name=name)
    await callback.answer('ثبت شد ✅')


@settle_router.callback_query(F.data == 'settle:custom')
async def settle_pay_custom(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get('settle_entity_id'):
        await callback.answer('ابتدا طرف حساب را انتخاب کنید', show_alert=True)
        return
    await state.set_state(Payment.amount)
    await state.update_data(settle_mode=True)
    await callback.message.answer('💵 مبلغ پرداختی (تومان) را وارد کنید:')
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
    name = data.get('settle_name', '')
    debt = int(data.get('settle_total_debt') or 0)
    prefix = '👨‍🔧' if data.get('settle_kind') == 'technician' else '🏪'
    await state.update_data(settle_repair_id=None)
    await _show_settle_actions(callback.message, state, name, debt, prefix)
    await callback.answer()


@settle_router.callback_query(F.data.startswith('settle:repair:'))
async def settle_repair_selected(callback: CallbackQuery, state: FSMContext, repo: RepairRepository) -> None:
    repair_id = int(callback.data.split(':')[-1])
    data = await state.get_data()
    kind = data.get('settle_kind')
    entity_id = data.get('settle_entity_id')
    if not kind or entity_id is None:
        await callback.answer('خطا — دوباره تلاش کنید', show_alert=True)
        return

    if kind == 'technician':
        repairs = await repo.repairs_with_technician_debt(int(entity_id))
    else:
        repairs = await repo.repairs_with_supplier_debt(int(entity_id))
    repair = next((r for r in repairs if int(r['id']) == repair_id), None)
    if not repair:
        await callback.answer('بدهی این پرونده تسویه شده', show_alert=True)
        return

    await state.update_data(settle_repair_id=repair_id, settle_repair_debt=int(repair['debt']))
    await callback.message.answer(
        f"📋 پرونده #{repair_id} — {repair.get('customer_name', '')}\n"
        f"مانده: **{format_toman(int(repair['debt']))}**\n\n"
        'نوع پرداخت را انتخاب کنید:',
        parse_mode='Markdown',
        reply_markup=settle_action_keyboard(),
    )
    await callback.answer()


async def process_settle_payment(message: Message, state: FSMContext, repo: RepairRepository, amount: int) -> bool:
    data = await state.get_data()
    if not data.get('settle_mode'):
        return False

    kind = data.get('settle_kind')
    entity_id = data.get('settle_entity_id')
    name = data.get('settle_name', '')
    repair_id = data.get('settle_repair_id')
    if not kind or entity_id is None:
        await state.clear()
        await message.answer('خطا — دوباره از منوی حسابداری شروع کنید.', reply_markup=accounting_menu())
        return True

    if kind == 'technician':
        applied = await repo.allocate_technician_payment(
            int(entity_id),
            amount,
            repair_id=int(repair_id) if repair_id else None,
        )
    else:
        applied = await repo.allocate_supplier_payment(
            int(entity_id),
            amount,
            repair_id=int(repair_id) if repair_id else None,
        )

    await _finish_settle(message, state, repo, applied, name=name)
    return True
