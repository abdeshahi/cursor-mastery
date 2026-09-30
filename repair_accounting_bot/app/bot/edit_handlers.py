from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import (
    cancel_keyboard,
    edit_parts_done_keyboard,
    edit_parts_menu_keyboard,
    edit_repair_menu_keyboard,
    edit_supplier_keyboard,
    edit_technician_keyboard,
    labor_amount_keyboard,
    reception_menu,
    repair_actions,
)
from app.bot.states import EditRepair
from app.services.accounting import format_toman
from app.services.formatters import format_repair_summary
from app.storage.repository import RepairRepository
from app.ui.themes import Theme

edit_router = Router()


async def _show_repair(
    message: Message,
    repo: RepairRepository,
    repair_id: int,
    theme: Theme,
    *,
    can_edit_repair: bool = True,
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


def _edit_menu_text(repair: dict, repair_id: int) -> str:
    return (
        f"✏️ **ویرایش پرونده #{repair_id}**\n\n"
        f"👤 {repair['customer_name']} | 📞 {repair['customer_phone'] or '—'}\n"
        f"📱 {repair['device']}\n"
        f"🔧 {repair['issue']}\n"
        f"👨‍🔧 {repair['technician_name'] or '—'} ({repair['technician_pct']}%)\n"
        f"💼 اجرت: {format_toman(int(repair['labor_amount']))}\n"
        f"🔩 قطعات: {len(repair['parts'])} مورد\n\n"
        'کدام بخش را می‌خواهید تغییر دهید؟'
    )


@edit_router.callback_query(F.data.startswith('edit:menu:'))
async def edit_menu(callback: CallbackQuery, repo: RepairRepository, theme: Theme, can_edit_repair: bool = True) -> None:
    if not can_edit_repair:
        await callback.answer('⛔️ دسترسی ویرایش پرونده ندارید.', show_alert=True)
        return
    repair_id = int(callback.data.split(':')[-1])
    repair = await _require_open_repair(repo, repair_id)
    if not repair:
        await callback.answer('پرونده باز یافت نشد', show_alert=True)
        return
    await callback.message.answer(
        _edit_menu_text(repair, repair_id),
        parse_mode='Markdown',
        reply_markup=edit_repair_menu_keyboard(repair_id),
    )
    await callback.answer()


@edit_router.callback_query(F.data == 'edit:cancel')
async def edit_cancel(callback: CallbackQuery, state: FSMContext, theme: Theme) -> None:
    await state.clear()
    await callback.message.answer('ویرایش لغو شد.', reply_markup=reception_menu(theme))
    await callback.answer()


@edit_router.callback_query(F.data.startswith('edit:cname:'))
async def edit_customer_name_start(callback: CallbackQuery, state: FSMContext, repo: RepairRepository) -> None:
    repair_id = int(callback.data.split(':')[-1])
    repair = await _require_open_repair(repo, repair_id)
    if not repair:
        await callback.answer('پرونده باز یافت نشد', show_alert=True)
        return
    await state.clear()
    await state.set_state(EditRepair.customer_name)
    await state.update_data(edit_repair_id=repair_id)
    await callback.message.answer(
        f"نام فعلی: **{repair['customer_name']}**\n\nنام جدید مشتری:",
        parse_mode='Markdown',
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@edit_router.message(EditRepair.customer_name)
async def edit_customer_name_save(
    message: Message,
    state: FSMContext,
    repo: RepairRepository,
    theme: Theme,
    can_edit_repair: bool = True,
) -> None:
    data = await state.get_data()
    repair_id = int(data['edit_repair_id'])
    if not await repo.update_repair_customer(repair_id, name=message.text.strip()):
        await state.clear()
        await message.answer('پرونده باز یافت نشد.', reply_markup=reception_menu(theme))
        return
    await state.clear()
    await message.answer('✅ نام مشتری به‌روز شد.')
    await _show_repair(message, repo, repair_id, theme, can_edit_repair=can_edit_repair)


@edit_router.callback_query(F.data.startswith('edit:cphone:'))
async def edit_customer_phone_start(callback: CallbackQuery, state: FSMContext, repo: RepairRepository) -> None:
    repair_id = int(callback.data.split(':')[-1])
    repair = await _require_open_repair(repo, repair_id)
    if not repair:
        await callback.answer('پرونده باز یافت نشد', show_alert=True)
        return
    await state.clear()
    await state.set_state(EditRepair.customer_phone)
    await state.update_data(edit_repair_id=repair_id)
    await callback.message.answer(
        f"تماس فعلی: **{repair['customer_phone'] or '—'}**\n\n"
        'شماره جدید (یا `-` برای خالی):',
        parse_mode='Markdown',
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@edit_router.message(EditRepair.customer_phone)
async def edit_customer_phone_save(
    message: Message,
    state: FSMContext,
    repo: RepairRepository,
    theme: Theme,
    can_edit_repair: bool = True,
) -> None:
    phone = message.text.strip()
    if phone == '-':
        phone = ''
    data = await state.get_data()
    repair_id = int(data['edit_repair_id'])
    if not await repo.update_repair_customer(repair_id, phone=phone):
        await state.clear()
        await message.answer('پرونده باز یافت نشد.', reply_markup=reception_menu(theme))
        return
    await state.clear()
    await message.answer('✅ شماره تماس به‌روز شد.')
    await _show_repair(message, repo, repair_id, theme, can_edit_repair=can_edit_repair)


@edit_router.callback_query(F.data.startswith('edit:device:'))
async def edit_device_start(callback: CallbackQuery, state: FSMContext, repo: RepairRepository) -> None:
    repair_id = int(callback.data.split(':')[-1])
    repair = await _require_open_repair(repo, repair_id)
    if not repair:
        await callback.answer('پرونده باز یافت نشد', show_alert=True)
        return
    await state.clear()
    await state.set_state(EditRepair.device)
    await state.update_data(edit_repair_id=repair_id)
    await callback.message.answer(
        f"مدل فعلی: **{repair['device']}**\n\nمدل جدید دستگاه:",
        parse_mode='Markdown',
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@edit_router.message(EditRepair.device)
async def edit_device_save(
    message: Message,
    state: FSMContext,
    repo: RepairRepository,
    theme: Theme,
    can_edit_repair: bool = True,
) -> None:
    data = await state.get_data()
    repair_id = int(data['edit_repair_id'])
    if not await repo.update_repair_device(repair_id, message.text.strip()):
        await state.clear()
        await message.answer('پرونده باز یافت نشد.', reply_markup=reception_menu(theme))
        return
    await state.clear()
    await message.answer('✅ مدل دستگاه به‌روز شد.')
    await _show_repair(message, repo, repair_id, theme, can_edit_repair=can_edit_repair)


@edit_router.callback_query(F.data.startswith('edit:issue:'))
async def edit_issue_start(callback: CallbackQuery, state: FSMContext, repo: RepairRepository) -> None:
    repair_id = int(callback.data.split(':')[-1])
    repair = await _require_open_repair(repo, repair_id)
    if not repair:
        await callback.answer('پرونده باز یافت نشد', show_alert=True)
        return
    await state.clear()
    await state.set_state(EditRepair.issue)
    await state.update_data(edit_repair_id=repair_id)
    await callback.message.answer(
        f"ایراد فعلی: **{repair['issue']}**\n\nشرح جدید مشکل:",
        parse_mode='Markdown',
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@edit_router.message(EditRepair.issue)
async def edit_issue_save(
    message: Message,
    state: FSMContext,
    repo: RepairRepository,
    theme: Theme,
    can_edit_repair: bool = True,
) -> None:
    data = await state.get_data()
    repair_id = int(data['edit_repair_id'])
    if not await repo.update_repair_issue(repair_id, message.text.strip()):
        await state.clear()
        await message.answer('پرونده باز یافت نشد.', reply_markup=reception_menu(theme))
        return
    await state.clear()
    await message.answer('✅ شرح ایراد به‌روز شد.')
    await _show_repair(message, repo, repair_id, theme, can_edit_repair=can_edit_repair)


@edit_router.callback_query(F.data.startswith('edit:techmenu:'))
async def edit_technician_menu(callback: CallbackQuery, repo: RepairRepository) -> None:
    repair_id = int(callback.data.split(':')[-1])
    repair = await _require_open_repair(repo, repair_id)
    if not repair:
        await callback.answer('پرونده باز یافت نشد', show_alert=True)
        return
    technicians = await repo.list_technicians()
    if not technicians:
        await callback.answer('تعمیرکاری ثبت نشده', show_alert=True)
        return
    await callback.message.answer(
        f"تعمیرکار فعلی: **{repair['technician_name'] or '—'}** ({repair['technician_pct']}%)\n\n"
        'تعمیرکار جدید:',
        parse_mode='Markdown',
        reply_markup=edit_technician_keyboard(repair_id, technicians),
    )
    await callback.answer()


@edit_router.callback_query(F.data.startswith('edit:techpick:'))
async def edit_technician_pick(
    callback: CallbackQuery,
    repo: RepairRepository,
    theme: Theme,
    can_edit_repair: bool = True,
) -> None:
    _, _, repair_id_raw, tech_id_raw = callback.data.split(':', 3)
    repair_id = int(repair_id_raw)
    tech_id = int(tech_id_raw)
    technicians = await repo.list_technicians()
    tech = next((t for t in technicians if t['id'] == tech_id), None)
    if not tech:
        await callback.answer('تعمیرکار یافت نشد', show_alert=True)
        return
    if not await repo.update_repair_technician(repair_id, tech_id, float(tech['default_pct'])):
        await callback.answer('پرونده باز یافت نشد', show_alert=True)
        return
    await callback.message.answer(f"✅ تعمیرکار به {tech['name']} ({tech['default_pct']}%) تغییر کرد.")
    await _show_repair(callback.message, repo, repair_id, theme, can_edit_repair=can_edit_repair)
    await callback.answer()


@edit_router.callback_query(F.data.startswith('edit:labor:'))
async def edit_labor_start(callback: CallbackQuery, state: FSMContext, repo: RepairRepository) -> None:
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
        'مبلغ اجرت جدید (تومان) یا «⏭ بدون اجرت / ادامه»:',
        parse_mode='Markdown',
        reply_markup=labor_amount_keyboard(),
    )
    await callback.answer()


@edit_router.message(EditRepair.labor_amount)
async def edit_labor_save(
    message: Message,
    state: FSMContext,
    repo: RepairRepository,
    theme: Theme,
    can_edit_repair: bool = True,
) -> None:
    text = message.text.strip()
    if text == '⏭ بدون اجرت / ادامه':
        labor_amount = 0
    elif not text.isdigit():
        await message.answer('لطفاً عدد یا «⏭ بدون اجرت / ادامه» وارد کنید.', reply_markup=labor_amount_keyboard())
        return
    else:
        labor_amount = int(text)
    data = await state.get_data()
    repair_id = int(data['edit_repair_id'])
    if not await repo.update_repair_labor(repair_id, labor_amount):
        await state.clear()
        await message.answer('پرونده باز یافت نشد.', reply_markup=reception_menu(theme))
        return
    await state.clear()
    await message.answer(f'✅ اجرت پرونده #{repair_id} به‌روز شد.')
    await _show_repair(message, repo, repair_id, theme, can_edit_repair=can_edit_repair)


@edit_router.callback_query(F.data.startswith('edit:parts:'))
async def edit_parts_menu(callback: CallbackQuery, repo: RepairRepository) -> None:
    repair_id = int(callback.data.split(':')[-1])
    repair = await _require_open_repair(repo, repair_id)
    if not repair:
        await callback.answer('پرونده باز یافت نشد', show_alert=True)
        return
    lines = [f"🔩 **قطعات پرونده #{repair_id}**", '']
    if repair['parts']:
        for part in repair['parts']:
            lines.append(
                f"• {part['part_name']}: خرید {format_toman(int(part['cost']))} → "
                f"فروش {format_toman(int(part['sell_price']))}",
            )
    else:
        lines.append('• قطعه‌ای ثبت نشده')
    lines.append('\nویرایش، حذف، یا افزودن قطعه:')
    await callback.message.answer(
        '\n'.join(lines),
        parse_mode='Markdown',
        reply_markup=edit_parts_menu_keyboard(repair_id, repair['parts']),
    )
    await callback.answer()


@edit_router.callback_query(F.data.startswith('edit:patdel:'))
async def edit_part_delete(
    callback: CallbackQuery,
    repo: RepairRepository,
    theme: Theme,
    can_edit_repair: bool = True,
) -> None:
    _, _, repair_id_raw, part_id_raw = callback.data.split(':', 3)
    repair_id = int(repair_id_raw)
    part_id = int(part_id_raw)
    if not await repo.delete_repair_part(repair_id, part_id):
        await callback.answer('حذف ممکن نیست', show_alert=True)
        return
    await callback.answer('قطعه حذف شد ✅')
    repair = await _require_open_repair(repo, repair_id)
    if repair:
        await callback.message.answer(
            '🔩 لیست به‌روز قطعات:',
            reply_markup=edit_parts_menu_keyboard(repair_id, repair['parts']),
        )
    await _show_repair(callback.message, repo, repair_id, theme, can_edit_repair=can_edit_repair)


@edit_router.callback_query(F.data.startswith('edit:patmod:'))
async def edit_part_modify_start(callback: CallbackQuery, state: FSMContext, repo: RepairRepository) -> None:
    _, _, repair_id_raw, part_id_raw = callback.data.split(':', 3)
    repair_id = int(repair_id_raw)
    part_id = int(part_id_raw)
    repair = await _require_open_repair(repo, repair_id)
    if not repair:
        await callback.answer('پرونده باز یافت نشد', show_alert=True)
        return
    part = next((p for p in repair['parts'] if int(p['id']) == part_id), None)
    if not part:
        await callback.answer('قطعه یافت نشد', show_alert=True)
        return
    await state.clear()
    await state.set_state(EditRepair.part_name)
    await state.update_data(
        edit_repair_id=repair_id,
        edit_part_id=part_id,
        edit_modifying_part=True,
        current_part={'part_name': part['part_name']},
    )
    await callback.message.answer(
        f"ویرایش قطعه: **{part['part_name']}**\n\nنام جدید (یا همان را بفرستید):",
        parse_mode='Markdown',
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@edit_router.callback_query(F.data.startswith('edit:part:'))
async def edit_part_start(callback: CallbackQuery, state: FSMContext, repo: RepairRepository) -> None:
    repair_id = int(callback.data.split(':')[-1])
    repair = await _require_open_repair(repo, repair_id)
    if not repair:
        await callback.answer('پرونده باز یافت نشد', show_alert=True)
        return
    await state.clear()
    await state.set_state(EditRepair.part_name)
    await state.update_data(
        edit_repair_id=repair_id,
        edit_parts_added=0,
        edit_modifying_part=False,
        edit_part_id=None,
    )
    await callback.message.answer(
        f"➕ افزودن قطعه به پرونده #{repair_id}\n\nنام قطعه:",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@edit_router.message(EditRepair.part_name, F.text == '✅ پایان ویرایش')
async def edit_parts_finish(
    message: Message,
    state: FSMContext,
    repo: RepairRepository,
    theme: Theme,
    can_edit_repair: bool = True,
) -> None:
    data = await state.get_data()
    repair_id = int(data['edit_repair_id'])
    added = int(data.get('edit_parts_added') or 0)
    modifying = data.get('edit_modifying_part')
    await state.clear()
    if modifying:
        await message.answer('✅ ویرایش قطعه ذخیره شد.')
    elif added:
        await message.answer(f'✅ {added} قطعه به پرونده #{repair_id} اضافه شد.')
    else:
        await message.answer('قطعه‌ای اضافه نشد.')
    await _show_repair(message, repo, repair_id, theme, can_edit_repair=can_edit_repair)


@edit_router.message(EditRepair.part_name, F.text == '➕ قطعه دیگر')
async def edit_part_add_more(message: Message, state: FSMContext) -> None:
    await message.answer('نام قطعه بعدی:', reply_markup=cancel_keyboard())


@edit_router.message(EditRepair.part_name)
async def edit_part_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    part = data.get('current_part', {})
    part['part_name'] = message.text.strip()
    await state.update_data(current_part=part)
    await state.set_state(EditRepair.part_cost)
    await message.answer('قیمت خرید قطعه از فروشنده (تومان):', reply_markup=cancel_keyboard())


@edit_router.message(EditRepair.part_cost)
async def edit_part_cost(message: Message, state: FSMContext) -> None:
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
async def edit_part_sell(message: Message, state: FSMContext, repo: RepairRepository) -> None:
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
async def edit_pick_supplier(callback: CallbackQuery, state: FSMContext, repo: RepairRepository) -> None:
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
async def edit_part_supplier_text(message: Message, state: FSMContext, repo: RepairRepository) -> None:
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
    part_id = data.get('edit_part_id')
    modifying = data.get('edit_modifying_part')
    if modifying and part_id:
        ok = await repo.update_repair_part(repair_id, int(part_id), part)
        fail_msg = 'ویرایش قطعه ممکن نبود.'
    else:
        ok = await repo.add_repair_part(repair_id, part)
        fail_msg = 'پرونده باز یافت نشد یا بسته شده.'
    if not ok:
        await state.clear()
        await message.answer(fail_msg, reply_markup=cancel_keyboard())
        return
    if modifying and part_id:
        await state.clear()
        await message.answer('✅ قطعه به‌روز شد.')
        return
    added = int(data.get('edit_parts_added') or 0) + 1
    await state.update_data(edit_parts_added=added, current_part={})
    await state.set_state(EditRepair.part_name)
    await message.answer(
        f"قطعه ثبت شد ({added} مورد).\n"
        'قطعه دیگر یا «✅ پایان ویرایش»:',
        reply_markup=edit_parts_done_keyboard(),
    )
