from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.admin_keyboards import (
    invite_list_keyboard,
    invite_role_keyboard,
    staff_detail_keyboard,
    staff_list_keyboard,
    staff_role_pick_keyboard,
    supplier_detail_keyboard,
    supplier_list_keyboard,
    technician_detail_keyboard,
    technician_list_keyboard,
)
from app.bot.invite_utils import build_invite_link
from app.bot.keyboards import (
    admin_menu,
    root_menu,
    staff_manage_menu,
    sup_manage_menu,
    tech_manage_menu,
    theme_picker_keyboard,
)
from app.bot.menu_filter import MenuFilter
from app.bot.parsing import parse_staff_args
from app.bot.states import AdminStaffAdd, AdminStaffRename, AdminSupAdd, AdminTechAdd
from app.staff.roles import ROLE_ADMIN, ROLE_LABELS
from app.ui.themes import Theme
from app.storage.settings_repository import SettingsRepository
from app.storage.repository import RepairRepository
from app.storage.staff_repository import StaffRepository

admin_router = Router()


async def deny_admin(message: Message) -> None:
    await message.answer('⛔️ این بخش فقط برای مدیر است.')


@admin_router.message(MenuFilter('root_manage'))
async def open_admin_menu(message: Message, state: FSMContext, is_admin: bool, theme: Theme) -> None:
    if not is_admin:
        await deny_admin(message)
        return
    await state.clear()
    await message.answer(f"{theme.banner}\n\n⚙️ **مدیریت سیستم**", reply_markup=admin_menu(theme), parse_mode='Markdown')


@admin_router.message(MenuFilter('mgmt_staff'))
async def admin_staff_menu(message: Message, state: FSMContext, staff_repo: StaffRepository, is_admin: bool, theme: Theme) -> None:
    if not is_admin:
        await deny_admin(message)
        return
    await state.clear()
    await message.answer('👥 **پرسنل و دسترسی**', reply_markup=staff_manage_menu(theme), parse_mode='Markdown')
    await show_staff_list(message, staff_repo)


@admin_router.message(MenuFilter('mgmt_tech'))
async def admin_tech_menu(message: Message, state: FSMContext, repo: RepairRepository, is_admin: bool, theme: Theme) -> None:
    if not is_admin:
        await deny_admin(message)
        return
    await state.clear()
    await message.answer('👨‍🔧 **تعمیرکاران**', reply_markup=tech_manage_menu(theme), parse_mode='Markdown')
    await show_technician_list(message, repo)


@admin_router.message(MenuFilter('mgmt_sup'))
async def admin_sup_menu(message: Message, state: FSMContext, repo: RepairRepository, is_admin: bool, theme: Theme) -> None:
    if not is_admin:
        await deny_admin(message)
        return
    await state.clear()
    await message.answer('🏪 **قطعه‌فروشان**', reply_markup=sup_manage_menu(theme), parse_mode='Markdown')
    await show_supplier_list(message, repo)


async def show_staff_list(message: Message, staff_repo: StaffRepository) -> None:
    rows = await staff_repo.list_staff()
    if not rows:
        await message.answer(
            'پرسنلی ثبت نشده.\nروی ➕ افزودن پرسنل بزنید.',
            reply_markup=staff_list_keyboard([], current_user_id=message.from_user.id),
        )
        return
    lines = ['**لیست پرسنل:**', '']
    for row in rows:
        role = ROLE_LABELS.get(row['role'], row['role'])
        lines.append(f"• {row['name']} — `{row['telegram_id']}` ({role})")
    await message.answer(
        '\n'.join(lines),
        parse_mode='Markdown',
        reply_markup=staff_list_keyboard(rows, current_user_id=message.from_user.id),
    )


async def show_technician_list(message: Message, repo: RepairRepository) -> None:
    techs = await repo.list_all_technicians()
    active = [t for t in techs if t['active']]
    if not active:
        await message.answer('تعمیرکاری ثبت نشده.', reply_markup=technician_list_keyboard(techs))
        return
    lines = ['**تعمیرکاران فعال:**', '']
    for tech in active:
        lines.append(f"• {tech['name']} — {tech['default_pct']}%")
    await message.answer('\n'.join(lines), parse_mode='Markdown', reply_markup=technician_list_keyboard(techs))


async def show_supplier_list(message: Message, repo: RepairRepository) -> None:
    suppliers = await repo.list_all_suppliers()
    active = [s for s in suppliers if s['active']]
    if not active:
        await message.answer('فروشنده‌ای ثبت نشده.', reply_markup=supplier_list_keyboard(suppliers))
        return
    lines = ['**قطعه‌فروشان فعال:**', '']
    for sup in active:
        lines.append(f"• {sup['name']}")
    await message.answer('\n'.join(lines), parse_mode='Markdown', reply_markup=supplier_list_keyboard(suppliers))


@admin_router.callback_query(F.data == 'adm:staff:list')
async def cb_staff_list(callback: CallbackQuery, staff_repo: StaffRepository, is_admin: bool) -> None:
    if not is_admin:
        await callback.answer('فقط مدیر', show_alert=True)
        return
    await show_staff_list(callback.message, staff_repo)
    await callback.answer()


@admin_router.callback_query(F.data.startswith('adm:staff:view:'))
async def cb_staff_view(callback: CallbackQuery, staff_repo: StaffRepository, is_admin: bool) -> None:
    if not is_admin:
        await callback.answer('فقط مدیر', show_alert=True)
        return
    telegram_id = int(callback.data.split(':')[-1])
    row = await staff_repo.get_staff(telegram_id)
    if not row or not row['active']:
        await callback.answer('پرسنل یافت نشد', show_alert=True)
        return
    role = ROLE_LABELS.get(row.get('role') or 'full', 'کارمند')
    is_admin_user = row.get('role') == ROLE_ADMIN or bool(row.get('is_admin'))
    if is_admin_user:
        edit_status = 'همیشه فعال (مدیر)'
    else:
        edit_status = '✅ فعال' if row.get('can_edit_repair') else '❌ غیرفعال'
    hint = 'نام یا نقش را ویرایش کنید:' if telegram_id == callback.from_user.id else 'نام، نقش، یا دسترسی ویرایش پرونده را تنظیم کنید:'
    text = (
        f"👤 **{row['name']}**\n\n"
        f"آیدی: `{telegram_id}`\n"
        f"نقش: {role}\n"
        f"✏️ ویرایش پرونده: {edit_status}\n\n"
        f'{hint}'
    )
    await callback.message.answer(
        text,
        parse_mode='Markdown',
        reply_markup=staff_detail_keyboard(
            telegram_id,
            current_user_id=callback.from_user.id,
            can_edit_repair=bool(row.get('can_edit_repair')),
            is_admin_user=is_admin_user,
        ),
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith('adm:staff:toggleedit:'))
async def cb_staff_toggle_edit(callback: CallbackQuery, staff_repo: StaffRepository, is_admin: bool) -> None:
    if not is_admin:
        await callback.answer('فقط مدیر', show_alert=True)
        return
    telegram_id = int(callback.data.split(':')[-1])
    if telegram_id == callback.from_user.id:
        await callback.answer('دسترسی مدیر همیشه فعال است.', show_alert=True)
        return
    new_value = await staff_repo.toggle_can_edit_repair(telegram_id)
    if new_value is None:
        await callback.answer('تغییر دسترسی ممکن نیست', show_alert=True)
        return
    status = 'فعال ✅' if new_value else 'غیرفعال ❌'
    await callback.answer(f'ویرایش پرونده: {status}')
    row = await staff_repo.get_staff(telegram_id)
    if row and row['active']:
        role = ROLE_LABELS.get(row.get('role') or 'full', 'کارمند')
        is_admin_user = row.get('role') == ROLE_ADMIN or bool(row.get('is_admin'))
        edit_status = '✅ فعال' if new_value else '❌ غیرفعال'
        await callback.message.edit_text(
            f"👤 **{row['name']}**\n\n"
            f"آیدی: `{telegram_id}`\n"
            f"نقش: {role}\n"
            f"✏️ ویرایش پرونده: {edit_status}\n\n"
            'نام، نقش، یا دسترسی ویرایش پرونده را تنظیم کنید:',
            parse_mode='Markdown',
            reply_markup=staff_detail_keyboard(
                telegram_id,
                current_user_id=callback.from_user.id,
                can_edit_repair=new_value,
                is_admin_user=is_admin_user,
            ),
        )


@admin_router.callback_query(F.data.startswith('adm:staff:role:'))
async def cb_staff_set_role(callback: CallbackQuery, staff_repo: StaffRepository, is_admin: bool) -> None:
    if not is_admin:
        await callback.answer('فقط مدیر', show_alert=True)
        return
    _, _, _, telegram_id_raw, role = callback.data.split(':', 4)
    telegram_id = int(telegram_id_raw)
    if telegram_id == callback.from_user.id:
        await callback.answer('نقش خودتان را نمی‌توانید تغییر دهید.', show_alert=True)
        return
    if await staff_repo.set_role(telegram_id, role):
        await callback.answer(f'نقش به «{ROLE_LABELS[role]}» تغییر کرد ✅')
        await show_staff_list(callback.message, staff_repo)
    else:
        await callback.answer('خطا در تغییر نقش', show_alert=True)


@admin_router.callback_query(F.data.startswith('adm:staff:del:'))
async def cb_staff_remove(callback: CallbackQuery, staff_repo: StaffRepository, is_admin: bool) -> None:
    if not is_admin:
        await callback.answer('فقط مدیر', show_alert=True)
        return
    telegram_id = int(callback.data.split(':')[-1])
    if telegram_id == callback.from_user.id:
        await callback.answer('نمی‌توانید خودتان را حذف کنید.', show_alert=True)
        return
    if await staff_repo.remove_staff(telegram_id):
        await callback.answer('دسترسی حذف شد ✅')
        await show_staff_list(callback.message, staff_repo)
    else:
        await callback.answer('پرسنل یافت نشد', show_alert=True)


@admin_router.callback_query(F.data.startswith('adm:staff:rename:'))
async def cb_staff_rename_start(
    callback: CallbackQuery,
    state: FSMContext,
    staff_repo: StaffRepository,
    is_admin: bool,
) -> None:
    if not is_admin:
        await callback.answer('فقط مدیر', show_alert=True)
        return
    telegram_id = int(callback.data.split(':')[-1])
    row = await staff_repo.get_staff(telegram_id)
    if not row or not row['active']:
        await callback.answer('پرسنل یافت نشد', show_alert=True)
        return
    await state.set_state(AdminStaffRename.name)
    await state.update_data(rename_staff_id=telegram_id, rename_staff_old=row['name'])
    await callback.message.answer(
        f"✏️ نام جدید برای **{row['name']}** را بنویسید:",
        parse_mode='Markdown',
    )
    await callback.answer()


@admin_router.message(AdminStaffRename.name)
async def admin_staff_rename_save(
    message: Message,
    state: FSMContext,
    staff_repo: StaffRepository,
    is_admin: bool,
) -> None:
    if not is_admin:
        await deny_admin(message)
        return
    new_name = message.text.strip()
    if len(new_name) < 2:
        await message.answer('نام باید حداقل ۲ حرف باشد.')
        return
    data = await state.get_data()
    telegram_id = data.get('rename_staff_id')
    old_name = data.get('rename_staff_old', '')
    if not telegram_id:
        await state.clear()
        await message.answer('خطا — دوباره از لیست پرسنل شروع کنید.')
        return
    if await staff_repo.set_name(int(telegram_id), new_name):
        await state.clear()
        await message.answer(
            f'✅ نام «{old_name}» به «{new_name}» تغییر کرد.',
            reply_markup=staff_manage_menu(theme),
        )
        await show_staff_list(message, staff_repo)
    else:
        await message.answer('خطا در ذخیره نام.')


@admin_router.callback_query(F.data == 'adm:staff:add')
async def cb_staff_add_start(callback: CallbackQuery, state: FSMContext, is_admin: bool) -> None:
    if not is_admin:
        await callback.answer('فقط مدیر', show_alert=True)
        return
    await state.set_state(AdminStaffAdd.telegram_id)
    await callback.message.answer(
        '🆔 آیدی تلگرام پرسنل را وارد کنید:\n\n'
        'مثال: `5123456789`\n'
        'یا: `5123456789|نهال`',
        parse_mode='Markdown',
    )
    await callback.answer()


@admin_router.message(MenuFilter('mgmt_staff_add'))
async def admin_staff_add_start(message: Message, state: FSMContext, is_admin: bool, theme: Theme) -> None:
    if not is_admin:
        await deny_admin(message)
        return
    await state.set_state(AdminStaffAdd.telegram_id)
    await message.answer(
        '🆔 آیدی تلگرام پرسنل را وارد کنید:\n\n'
        'مثال: `5123456789`\n'
        'یا: `5123456789|نهال`',
        parse_mode='Markdown',
    )


@admin_router.message(AdminStaffAdd.telegram_id)
async def admin_staff_add_id(message: Message, state: FSMContext) -> None:
    raw = message.text.strip()
    parsed = parse_staff_args(raw) if '|' in raw else None
    if parsed:
        telegram_id, name = parsed
        await state.update_data(staff_telegram_id=telegram_id, staff_name=name)
        await state.set_state(AdminStaffAdd.role)
        await message.answer(
            f'نقش «{name}» را انتخاب کنید:',
            reply_markup=staff_role_pick_keyboard(),
        )
        return
    if not raw.isdigit():
        await message.answer('آیدی باید عدد باشد. مثال: 5123456789')
        return
    await state.update_data(staff_telegram_id=int(raw))
    await state.set_state(AdminStaffAdd.name)
    await message.answer('نام پرسنل را وارد کنید:')


@admin_router.message(AdminStaffAdd.name)
async def admin_staff_add_name(message: Message, state: FSMContext) -> None:
    await state.update_data(staff_name=message.text.strip())
    await state.set_state(AdminStaffAdd.role)
    await message.answer('نقش دسترسی را انتخاب کنید:', reply_markup=staff_role_pick_keyboard())


@admin_router.callback_query(F.data.startswith('adm:staff:newrole:'))
async def admin_staff_add_role(
    callback: CallbackQuery,
    state: FSMContext,
    staff_repo: StaffRepository,
    is_admin: bool,
    can_reception: bool,
    can_accounting: bool,
    can_manage: bool,
) -> None:
    if not is_admin:
        await callback.answer('فقط مدیر', show_alert=True)
        return
    role = callback.data.split(':')[-1]
    data = await state.get_data()
    telegram_id = data.get('staff_telegram_id')
    name = data.get('staff_name')
    if not telegram_id or not name:
        await callback.answer('اطلاعات ناقص — دوباره تلاش کنید', show_alert=True)
        await state.clear()
        return
    await staff_repo.add_staff(int(telegram_id), name, role=role)
    await state.clear()
    await callback.message.answer(
        f'✅ پرسنل اضافه شد: {name} ({ROLE_LABELS[role]})',
        reply_markup=admin_menu(theme),
    )
    await show_staff_list(callback.message, staff_repo)
    await callback.answer()


@admin_router.callback_query(F.data == 'adm:tech:list')
async def cb_tech_list(callback: CallbackQuery, repo: RepairRepository, is_admin: bool) -> None:
    if not is_admin:
        await callback.answer('فقط مدیر', show_alert=True)
        return
    await show_technician_list(callback.message, repo)
    await callback.answer()


@admin_router.callback_query(F.data.startswith('adm:tech:view:'))
async def cb_tech_view(callback: CallbackQuery, repo: RepairRepository, is_admin: bool) -> None:
    if not is_admin:
        await callback.answer('فقط مدیر', show_alert=True)
        return
    tech_id = int(callback.data.split(':')[-1])
    techs = await repo.list_all_technicians()
    tech = next((t for t in techs if t['id'] == tech_id), None)
    if not tech:
        await callback.answer('یافت نشد', show_alert=True)
        return
    status = 'فعال' if tech['active'] else 'غیرفعال'
    await callback.message.answer(
        f"👨‍🔧 **{tech['name']}**\n\nدرصد: {tech['default_pct']}%\nوضعیت: {status}",
        parse_mode='Markdown',
        reply_markup=technician_detail_keyboard(tech_id),
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith('adm:tech:del:'))
async def cb_tech_deactivate(callback: CallbackQuery, repo: RepairRepository, is_admin: bool) -> None:
    if not is_admin:
        await callback.answer('فقط مدیر', show_alert=True)
        return
    tech_id = int(callback.data.split(':')[-1])
    if await repo.deactivate_technician(tech_id):
        await callback.answer('غیرفعال شد ✅')
        await show_technician_list(callback.message, repo)
    else:
        await callback.answer('یافت نشد', show_alert=True)


@admin_router.callback_query(F.data == 'adm:tech:add')
async def cb_tech_add_start(callback: CallbackQuery, state: FSMContext, is_admin: bool) -> None:
    if not is_admin:
        await callback.answer('فقط مدیر', show_alert=True)
        return
    await state.set_state(AdminTechAdd.name)
    await callback.message.answer('نام تعمیرکار جدید:')
    await callback.answer()


@admin_router.message(MenuFilter('mgmt_tech_add'))
async def admin_tech_add_start(message: Message, state: FSMContext, is_admin: bool, theme: Theme) -> None:
    if not is_admin:
        await deny_admin(message)
        return
    await state.set_state(AdminTechAdd.name)
    await message.answer('نام تعمیرکار جدید:')


@admin_router.message(AdminTechAdd.name)
async def admin_tech_add_name(message: Message, state: FSMContext) -> None:
    await state.update_data(admin_tech_name=message.text.strip())
    await state.set_state(AdminTechAdd.pct)
    await message.answer('درصد سهم تعمیرکار (مثلاً 40):')


@admin_router.message(AdminTechAdd.pct)
async def admin_tech_add_pct(message: Message, state: FSMContext, repo: RepairRepository) -> None:
    if not message.text.strip().replace('.', '', 1).isdigit():
        await message.answer('درصد نامعتبر.')
        return
    data = await state.get_data()
    pct = float(message.text.strip())
    tech_id = await repo.add_technician(data['admin_tech_name'], pct)
    await state.clear()
    await message.answer(
        f'✅ تعمیرکار #{tech_id} ثبت شد: {data["admin_tech_name"]} ({pct}%)',
        reply_markup=tech_manage_menu(theme),
    )


@admin_router.callback_query(F.data == 'adm:sup:list')
async def cb_sup_list(callback: CallbackQuery, repo: RepairRepository, is_admin: bool) -> None:
    if not is_admin:
        await callback.answer('فقط مدیر', show_alert=True)
        return
    await show_supplier_list(callback.message, repo)
    await callback.answer()


@admin_router.callback_query(F.data.startswith('adm:sup:view:'))
async def cb_sup_view(callback: CallbackQuery, repo: RepairRepository, is_admin: bool) -> None:
    if not is_admin:
        await callback.answer('فقط مدیر', show_alert=True)
        return
    sup_id = int(callback.data.split(':')[-1])
    suppliers = await repo.list_all_suppliers()
    sup = next((s for s in suppliers if s['id'] == sup_id), None)
    if not sup:
        await callback.answer('یافت نشد', show_alert=True)
        return
    status = 'فعال' if sup['active'] else 'غیرفعال'
    await callback.message.answer(
        f"🏪 **{sup['name']}**\n\nوضعیت: {status}",
        parse_mode='Markdown',
        reply_markup=supplier_detail_keyboard(sup_id),
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith('adm:sup:del:'))
async def cb_sup_deactivate(callback: CallbackQuery, repo: RepairRepository, is_admin: bool) -> None:
    if not is_admin:
        await callback.answer('فقط مدیر', show_alert=True)
        return
    sup_id = int(callback.data.split(':')[-1])
    if await repo.deactivate_supplier(sup_id):
        await callback.answer('غیرفعال شد ✅')
        await show_supplier_list(callback.message, repo)
    else:
        await callback.answer('یافت نشد', show_alert=True)


@admin_router.callback_query(F.data == 'adm:sup:add')
async def cb_sup_add_start(callback: CallbackQuery, state: FSMContext, is_admin: bool) -> None:
    if not is_admin:
        await callback.answer('فقط مدیر', show_alert=True)
        return
    await state.set_state(AdminSupAdd.name)
    await callback.message.answer('نام فروشنده قطعه:')
    await callback.answer()


@admin_router.message(MenuFilter('mgmt_sup_add'))
async def admin_sup_add_start(message: Message, state: FSMContext, is_admin: bool, theme: Theme) -> None:
    if not is_admin:
        await deny_admin(message)
        return
    await state.set_state(AdminSupAdd.name)
    await message.answer('نام فروشنده قطعه:')


@admin_router.message(AdminSupAdd.name)
async def admin_sup_add_name(message: Message, state: FSMContext, repo: RepairRepository) -> None:
    sup_id = await repo.add_supplier(message.text.strip())
    await state.clear()
    await message.answer(f'✅ فروشنده #{sup_id} ثبت شد.', reply_markup=sup_manage_menu(theme))


async def show_invite_menu(message: Message, staff_repo: StaffRepository) -> None:
    invites = await staff_repo.list_invites(active_only=True)
    if not invites:
        await message.answer(
            '🔗 **لینک دعوت پرسنل**\n\n'
            'هنوز لینک فعالی نیست. نقش را انتخاب کنید تا لینک ساخته شود:',
            parse_mode='Markdown',
            reply_markup=invite_role_keyboard(),
        )
        return
    lines = ['🔗 **لینک‌های دعوت فعال**', '']
    for inv in invites:
        role = ROLE_LABELS.get(inv['role'], inv['role'])
        uses = f"{inv['use_count']}/{inv['max_uses']}" if inv['max_uses'] > 0 else f"{inv['use_count']}/∞"
        lines.append(f'• {role} — استفاده: {uses}')
    lines.append('\nبرای لغو روی دکمه 🚫 بزنید، یا ➕ لینک جدید بسازید.')
    await message.answer(
        '\n'.join(lines),
        parse_mode='Markdown',
        reply_markup=invite_list_keyboard(invites),
    )


@admin_router.message(MenuFilter('mgmt_staff_invite'))
async def admin_invite_menu(message: Message, staff_repo: StaffRepository, is_admin: bool) -> None:
    if not is_admin:
        await deny_admin(message)
        return
    await show_invite_menu(message, staff_repo)


@admin_router.callback_query(F.data == 'adm:invite:new')
async def cb_invite_new(callback: CallbackQuery, is_admin: bool) -> None:
    if not is_admin:
        await callback.answer('فقط مدیر', show_alert=True)
        return
    await callback.message.answer(
        'نقش پرسنل دعوت‌شده را انتخاب کنید:',
        reply_markup=invite_role_keyboard(),
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith('adm:invite:create:'))
async def cb_invite_create(
    callback: CallbackQuery,
    staff_repo: StaffRepository,
    is_admin: bool,
) -> None:
    if not is_admin:
        await callback.answer('فقط مدیر', show_alert=True)
        return
    role = callback.data.split(':')[-1]
    token = await staff_repo.create_invite(callback.from_user.id, role, max_uses=1)
    bot_info = await callback.message.bot.get_me()
    link = build_invite_link(bot_info.username, token)
    role_label = ROLE_LABELS.get(role, role)
    await callback.message.answer(
        f'✅ **لینک دعوت ساخته شد**\n\n'
        f'نقش: {role_label}\n'
        f'یک‌بار مصرف — بعد از اولین عضویت غیرفعال می‌شود.\n\n'
        f'🔗 `{link}`\n\n'
        'این لینک را برای همکار بفرستید. با کلیک و Start خودکار عضو پرسنل می‌شود.',
        parse_mode='Markdown',
        reply_markup=staff_manage_menu(theme),
    )
    await callback.answer('لینک ساخته شد ✅')


@admin_router.callback_query(F.data.startswith('adm:invite:revoke:'))
async def cb_invite_revoke(callback: CallbackQuery, staff_repo: StaffRepository, is_admin: bool) -> None:
    if not is_admin:
        await callback.answer('فقط مدیر', show_alert=True)
        return
    token = callback.data.replace('adm:invite:revoke:', '', 1)
    if await staff_repo.revoke_invite(token):
        await callback.answer('لینک لغو شد ✅')
        await show_invite_menu(callback.message, staff_repo)
    else:
        await callback.answer('لینک یافت نشد', show_alert=True)

@admin_router.message(MenuFilter('mgmt_theme'))
async def admin_theme_menu(message: Message, settings_repo: SettingsRepository, is_admin: bool, theme: Theme) -> None:
    if not is_admin:
        await deny_admin(message)
        return
    current_id = await settings_repo.get_theme_id()
    await message.answer(
        f"{theme.banner}\n\n🎨 **انتخاب تم رنگی**\n\n"
        'تم فعال با ✅ مشخص شده است.\n'
        'تم روی **منوها** و **رنگ فاکتور PDF** اعمال می‌شود.',
        parse_mode='Markdown',
        reply_markup=theme_picker_keyboard(current_id),
    )


@admin_router.callback_query(F.data.startswith('adm:theme:'))
async def cb_set_theme(
    callback: CallbackQuery,
    settings_repo: SettingsRepository,
    is_admin: bool,
    theme: Theme,
) -> None:
    if not is_admin:
        await callback.answer('فقط مدیر', show_alert=True)
        return
    theme_id = callback.data.split(':')[-1]
    if theme_id == 'back':
        await callback.message.answer(
            f"{theme.banner}\n\n⚙️ **مدیریت سیستم**",
            parse_mode='Markdown',
            reply_markup=admin_menu(theme),
        )
        await callback.answer()
        return
    from app.ui.themes import THEMES, get_theme
    if theme_id not in THEMES:
        await callback.answer('تم نامعتبر', show_alert=True)
        return
    await settings_repo.set_theme_id(theme_id)
    new_theme = get_theme(theme_id)
    await callback.message.answer(
        f"{new_theme.banner}\n\n✅ تم **{new_theme.name_fa}** فعال شد.\n"
        'منوها با تم جدید به‌روز شدند.',
        parse_mode='Markdown',
        reply_markup=admin_menu(new_theme),
    )
    await callback.answer('تم ذخیره شد ✅')

