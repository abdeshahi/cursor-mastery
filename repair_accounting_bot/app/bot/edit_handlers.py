from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import (
    cancel_keyboard,
    edit_parts_done_keyboard,
    edit_repair_menu_keyboard,
    edit_supplier_keyboard,
    reception_menu,
    repair_actions,
)
from app.bot.states import EditRepair
from app.services.accounting import format_toman
from app.services.formatters import format_repair_summary
from app.storage.repository import RepairRepository

edit_router = Router()


async def _show_repair(
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


async def _require_open_repair(repo: RepairRepository, repair_id: int) -> dict | None:
    repair = await repo.get_repair(repair_id)
    if not repair:
        return None
    if repair.get('status') != 'open':
        return None
    return repair


@edit_router.callback_query(F.data.startswith('edit:menu:'))
async def edit_menu(callback: CallbackQuery, repo: RepairRepository, can_edit_repair: bool = False) -> None:
    if not can_edit_repair:
        await callback.answer('⛔️ دسترسی ویرایش پرونده ندارید.', show_alert=True)
        return
    repair_id = int(callback.data.split(':')[-1])
    repair = await _require_open_repair(repo, repair_id)
    if not repair:
        await callback.answer('پرونده باز یافت نشد', show_alert=True)
        return
    await callback.message.answer(
        f"✏️ **ویرایش پرونده #{repair_id}**\n"
        f"مشتری: {repair['customer_name']}\n"
        f"اجرت فعلی: {format_toman(int(repair['labor_amount']))}\n"
        f"قطعات: {len(repair['parts'])} مورد\n\n"
        'چه چیزی را می‌خواهید تغییر دهید؟',
        parse_mode='Markdown',
        reply_markup=edit_repair_menu_keyboard(repair_id),
    )
    await callback.answer()


@edit_router.callback_query(F.data == 'edit:cancel')
async def edit_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer('ویرایش لغو شد.', reply_markup=reception_menu())
    await callback.answer()


@edit_router.callback_query(F.data.startswith('edit:labor:'))
async def edit_labor_start(
    callback: CallbackQuery,
    state: FSMContext,
    repo: RepairRepository,
    can_edit_repair: bool = False,
) -> None:
    if not can_edit_repair:
        await callback.answer('⛔️ دسترسی ویرایش پرونده ندارید.', show_alert=True)
        return
    repair_id = int(callback.data.split(':')[-1])
    repair = await _require_open_repair(repo, repair_id)
    if not repair:
        await callback.answer('پرونده باز یافت نشد', show_alert=True)
        return
    await state.clear()
    await state.set_state(EditRepair.labor_amount)
    await state.update_data(edit_repair_id=repair_id)
    await callback.message.answer(
        f"💼 اجرت فعلی: **{format_toman(int(repair['labor_amount']))}**\n\n"
        'مبلغ اجرت جدید (تومان):',
        parse_mode='Markdown',
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@edit_router.message(EditRepair.labor_amount)
async def edit_labor_save(
    message: Message,
    state: FSMContext,
    repo: RepairRepository,
    can_edit_repair: bool = False,
) -> None:
    if not can_edit_repair:
        await state.clear()
        await message.answer('⛔️ دسترسی ویرایش پرونده ندارید.', reply_markup=reception_menu())
        return
    if not message.text.strip().isdigit():
        await message.answer('لطفاً فقط عدد وارد کنید.')
        return
    data = await state.get_data()
    repair_id = int(data['edit_repair_id'])
    labor_amount = int(message.text.strip())
    if not await repo.update_repair_labor(repair_id, labor_amount):
        await state.clear()
        await message.answer('پرونده باز یافت نشد یا بسته شده.', reply_markup=reception_menu())
        return
    await state.clear()
    await message.answer(f'✅ اجرت پرونده #{repair_id} به‌روز شد.')
    await _show_repair(message, repo, repair_id, can_edit_repair=can_edit_repair)
    await message.answer('منوی پذیرش', reply_markup=reception_menu())


@edit_router.callback_query(F.data.startswith('edit:part:'))
async def edit_part_start(
    callback: CallbackQuery,
    state: FSMContext,
    repo: RepairRepository,
    can_edit_repair: bool = False,
) -> None:
    if not can_edit_repair:
        await callback.answer('⛔️ دسترسی ویرایش پرونده ندارید.', show_alert=True)
        return
    repair_id = int(callback.data.split(':')[-1])
    repair = await _require_open_repair(repo, repair_id)
    if not repair:
        await callback.answer('پرونده باز یافت نشد', show_alert=True)
        return
    await state.clear()
    await state.set_state(EditRepair.part_name)
    await state.update_data(edit_repair_id=repair_id, edit_parts_added=0)
    await callback.message.answer(
        f"➕ افزودن قطعه به پرونده #{repair_id}\n\n"
        'نام قطعه:',
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@edit_router.message(EditRepair.part_name, F.text == '✅ پایان ویرایش')
async def edit_parts_finish(
    message: Message,
    state: FSMContext,
    repo: RepairRepository,
    can_edit_repair: bool = False,
) -> None:
    data = await state.get_data()
    repair_id = int(data['edit_repair_id'])
    added = int(data.get('edit_parts_added') or 0)
    await state.clear()
    if added:
        await message.answer(f'✅ {added} قطعه به پرونده #{repair_id} اضافه شد.')
    else:
        await message.answer('قطعه‌ای اضافه نشد.')
    await _show_repair(message, repo, repair_id, can_edit_repair=can_edit_repair)
    await message.answer('منوی پذیرش', reply_markup=reception_menu())


@edit_router.message(EditRepair.part_name, F.text == '➕ قطعه دیگر')
async def edit_part_add_more(message: Message, state: FSMContext, can_edit_repair: bool = False) -> None:
    if not can_edit_repair:
        await state.clear()
        await message.answer('⛔️ دسترسی ویرایش پرونده ندارید.', reply_markup=reception_menu())
        return
    await message.answer('نام قطعه بعدی:', reply_markup=cancel_keyboard())


@edit_router.message(EditRepair.part_name)
async def edit_part_name(message: Message, state: FSMContext, can_edit_repair: bool = False) -> None:
    if not can_edit_repair:
        await state.clear()
        await message.answer('⛔️ دسترسی ویرایش پرونده ندارید.', reply_markup=reception_menu())
        return
    await state.update_data(current_part={'part_name': message.text.strip()})
    await state.set_state(EditRepair.part_cost)
    await message.answer('قیمت خرید قطعه از فروشنده (تومان):', reply_markup=cancel_keyboard())


@edit_router.message(EditRepair.part_cost)
async def edit_part_cost(message: Message, state: FSMContext, can_edit_repair: bool = False) -> None:
    if not can_edit_repair:
        await state.clear()
        await message.answer('⛔️ دسترسی ویرایش پرونده ندارید.', reply_markup=reception_menu())
        return
    if not message.text.strip().isdigit():
        await message.answer('لطفاً فقط عدد وارد کنید.')
        return
    data = await state.get_data()
    part = data.get('current_part', {})
    part['cost'] = int(message.text.strip())
    await state.update_data(current_part=part)
    await state.set_state(EditRepair.part_sell)
    await message.answer('قیمت فروش قطعه به مشتری (تومان):')


@edit_router.message(EditRepair.part_sell)
async def edit_part_sell(
    message: Message,
    state: FSMContext,
    repo: RepairRepository,
    can_edit_repair: bool = False,
) -> None:
    if not can_edit_repair:
        await state.clear()
        await message.answer('⛔️ دسترسی ویرایش پرونده ندارید.', reply_markup=reception_menu())
        return
    if not message.text.strip().isdigit():
        await message.answer('لطفاً فقط عدد وارد کنید.')
        return
    data = await state.get_data()
    part = data.get('current_part', {})
    part['sell_price'] = int(message.text.strip())
    await state.update_data(current_part=part)
    suppliers = await repo.list_suppliers()
    await state.set_state(EditRepair.part_supplier)
    if suppliers:
        await message.answer('فروشنده قطعه:', reply_markup=edit_supplier_keyboard(suppliers))
    else:
        await message.answer('نام فروشنده قطعه (یا `-`):')


@edit_router.callback_query(F.data.startswith('edit:sup:'))
async def edit_pick_supplier(
    callback: CallbackQuery,
    state: FSMContext,
    repo: RepairRepository,
    can_edit_repair: bool = False,
) -> None:
    if not can_edit_repair:
        await callback.answer('⛔️ دسترسی ویرایش پرونده ندارید.', show_alert=True)
        return
    value = callback.data.split(':', 2)[2]
    data = await state.get_data()
    part = data.get('current_part', {})
    if value == 'new':
        await state.update_data(edit_new_supplier=True)
        await callback.message.answer('نام فروشنده قطعه:')
        await callback.answer()
        return
    if value != 'skip':
        part['supplier_id'] = int(value)
    await state.update_data(current_part=part, edit_new_supplier=False)
    await _save_edit_part(callback.message, state, repo)
    await callback.answer()


@edit_router.message(EditRepair.part_supplier)
async def edit_part_supplier_text(
    message: Message,
    state: FSMContext,
    repo: RepairRepository,
    can_edit_repair: bool = False,
) -> None:
    if not can_edit_repair:
        await state.clear()
        await message.answer('⛔️ دسترسی ویرایش پرونده ندارید.', reply_markup=reception_menu())
        return
    data = await state.get_data()
    part = data.get('current_part', {})
    if data.get('edit_new_supplier'):
        part['supplier_id'] = await repo.add_supplier(message.text.strip())
        await state.update_data(current_part=part, edit_new_supplier=False)
        await _save_edit_part(message, state, repo)
        return
    name = message.text.strip()
    if name != '-':
        part['supplier_id'] = await repo.add_supplier(name)
    await state.update_data(current_part=part)
    await _save_edit_part(message, state, repo)


async def _save_edit_part(message: Message, state: FSMContext, repo: RepairRepository) -> None:
    data = await state.get_data()
    repair_id = int(data['edit_repair_id'])
    part = data['current_part']
    if not await repo.add_repair_part(repair_id, part):
        await state.clear()
        await message.answer('پرونده باز یافت نشد یا بسته شده.', reply_markup=reception_menu())
        return
    added = int(data.get('edit_parts_added') or 0) + 1
    await state.update_data(edit_parts_added=added, current_part={})
    await state.set_state(EditRepair.part_name)
    await message.answer(
        f"قطعه ثبت شد ({added} مورد).\n"
        'قطعه دیگر یا «✅ پایان ویرایش»:',
        reply_markup=edit_parts_done_keyboard(),
    )
