from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.staff.roles import MANAGEABLE_ROLES, ROLE_LABELS


def staff_list_keyboard(staff_rows: list[dict], *, current_user_id: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for row in staff_rows:
        role_label = ROLE_LABELS.get(row['role'], row['role'])
        title = f"{row['name']} ({role_label})"
        rows.append(
            [
                InlineKeyboardButton(text=title, callback_data=f'adm:staff:view:{row["telegram_id"]}'),
            ],
        )
    rows.append([InlineKeyboardButton(text='➕ افزودن پرسنل', callback_data='adm:staff:add')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def staff_detail_keyboard(telegram_id: int, *, current_user_id: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text='✏️ ویرایش نام', callback_data=f'adm:staff:rename:{telegram_id}')],
    ]
    if telegram_id != current_user_id:
        role_row = [
            InlineKeyboardButton(
                text=ROLE_LABELS[role],
                callback_data=f'adm:staff:role:{telegram_id}:{role}',
            )
            for role in MANAGEABLE_ROLES
        ]
        rows.append(role_row)
        rows.append(
            [InlineKeyboardButton(text='🚫 حذف دسترسی', callback_data=f'adm:staff:del:{telegram_id}')],
        )
    rows.append([InlineKeyboardButton(text='⬅️ لیست پرسنل', callback_data='adm:staff:list')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def staff_role_pick_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=ROLE_LABELS[role],
                callback_data=f'adm:staff:newrole:{role}',
            )
            for role in MANAGEABLE_ROLES[:2]
        ],
        [
            InlineKeyboardButton(
                text=ROLE_LABELS[MANAGEABLE_ROLES[2]],
                callback_data=f'adm:staff:newrole:{MANAGEABLE_ROLES[2]}',
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def technician_list_keyboard(technicians: list[dict]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for tech in technicians:
        if not tech['active']:
            continue
        label = f"{tech['name']} ({tech['default_pct']}%)"
        rows.append(
            [
                InlineKeyboardButton(text=label, callback_data=f'adm:tech:view:{tech["id"]}'),
            ],
        )
    rows.append([InlineKeyboardButton(text='➕ افزودن تعمیرکار', callback_data='adm:tech:add')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def technician_detail_keyboard(tech_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='🚫 غیرفعال کردن', callback_data=f'adm:tech:del:{tech_id}')],
            [InlineKeyboardButton(text='⬅️ لیست تعمیرکاران', callback_data='adm:tech:list')],
        ],
    )


def supplier_list_keyboard(suppliers: list[dict]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for sup in suppliers:
        if not sup['active']:
            continue
        rows.append(
            [InlineKeyboardButton(text=sup['name'], callback_data=f'adm:sup:view:{sup["id"]}')],
        )
    rows.append([InlineKeyboardButton(text='➕ افزودن فروشنده', callback_data='adm:sup:add')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def supplier_detail_keyboard(sup_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='🚫 غیرفعال کردن', callback_data=f'adm:sup:del:{sup_id}')],
            [InlineKeyboardButton(text='⬅️ لیست فروشندگان', callback_data='adm:sup:list')],
        ],
    )


def invite_role_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=ROLE_LABELS[role],
                callback_data=f'adm:invite:create:{role}',
            )
            for role in MANAGEABLE_ROLES[:2]
        ],
        [
            InlineKeyboardButton(
                text=ROLE_LABELS[MANAGEABLE_ROLES[2]],
                callback_data=f'adm:invite:create:{MANAGEABLE_ROLES[2]}',
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def invite_list_keyboard(invites: list[dict]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for inv in invites[:10]:
        role_label = ROLE_LABELS.get(inv['role'], inv['role'])
        uses = f"{inv['use_count']}/{inv['max_uses']}" if inv['max_uses'] > 0 else f"{inv['use_count']}/∞"
        label = f"🚫 {role_label} ({uses})"
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f'adm:invite:revoke:{inv["token"]}')],
        )
    rows.append([InlineKeyboardButton(text='➕ لینک جدید', callback_data='adm:invite:new')])
    return InlineKeyboardMarkup(inline_keyboard=rows)
