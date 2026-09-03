from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.ui.themes import Theme, list_themes


def _btn(theme: Theme, key: str) -> KeyboardButton:
    return KeyboardButton(text=theme.label(key))


def root_menu(
    theme: Theme,
    *,
    can_reception: bool = True,
    can_accounting: bool = True,
    can_manage: bool = False,
) -> ReplyKeyboardMarkup:
    row: list[KeyboardButton] = []
    rows: list[list[KeyboardButton]] = []
    if can_reception:
        row.append(_btn(theme, 'root_reception'))
    if can_accounting:
        if row:
            rows.append(row)
            row = []
        row.append(_btn(theme, 'root_accounting'))
    if row:
        rows.append(row)
    if can_manage:
        rows.append([_btn(theme, 'root_manage')])
    rows.append([_btn(theme, 'help')])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def admin_menu(theme: Theme) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [_btn(theme, 'mgmt_staff'), _btn(theme, 'mgmt_theme')],
            [_btn(theme, 'mgmt_tech'), _btn(theme, 'mgmt_sup')],
            [_btn(theme, 'back_root')],
        ],
        resize_keyboard=True,
    )


def staff_manage_menu(theme: Theme) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [_btn(theme, 'mgmt_staff_add'), _btn(theme, 'mgmt_staff_invite')],
            [_btn(theme, 'back_root'), _btn(theme, 'root_manage')],
        ],
        resize_keyboard=True,
    )


def tech_manage_menu(theme: Theme) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [_btn(theme, 'mgmt_tech_add')],
            [_btn(theme, 'back_root'), _btn(theme, 'root_manage')],
        ],
        resize_keyboard=True,
    )


def sup_manage_menu(theme: Theme) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [_btn(theme, 'mgmt_sup_add')],
            [_btn(theme, 'back_root'), _btn(theme, 'root_manage')],
        ],
        resize_keyboard=True,
    )


def reception_menu(theme: Theme) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [_btn(theme, 'rec_new'), _btn(theme, 'rec_search')],
            [_btn(theme, 'rec_invoice'), _btn(theme, 'rec_report')],
            [_btn(theme, 'acc_export_excel'), _btn(theme, 'acc_export_pdf')],
            [_btn(theme, 'back_root')],
        ],
        resize_keyboard=True,
    )


def accounting_menu(theme: Theme) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [_btn(theme, 'acc_summary'), _btn(theme, 'acc_shop_profit')],
            [_btn(theme, 'acc_tech_share'), _btn(theme, 'acc_supplier_debt')],
            [_btn(theme, 'acc_pay_debt'), _btn(theme, 'acc_receive_customer')],
            [_btn(theme, 'acc_customer_debt')],
            [_btn(theme, 'acc_export_excel'), _btn(theme, 'acc_export_pdf')],
            [_btn(theme, 'back_root')],
        ],
        resize_keyboard=True,
    )


def theme_picker_keyboard(current_id: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for theme in list_themes():
        mark = '✅ ' if theme.id == current_id else ''
        rows.append(
            [
                InlineKeyboardButton(
                    text=f'{mark}{theme.name_fa}',
                    callback_data=f'adm:theme:{theme.id}',
                ),
            ],
        )
    rows.append([InlineKeyboardButton(text='⬅️ بازگشت', callback_data='adm:theme:back')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def labor_amount_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='⏭ بدون اجرت / ادامه')],
            [KeyboardButton(text='❌ انصراف')],
        ],
        resize_keyboard=True,
    )


def skip_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='⏭ بدون قطعه / ادامه')]],
        resize_keyboard=True,
    )


def parts_more_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='➕ قطعه دیگر')],
            [KeyboardButton(text='✅ ثبت نهایی پذیرش')],
        ],
        resize_keyboard=True,
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='❌ انصراف')]],
        resize_keyboard=True,
    )


def technician_keyboard(technicians: list[dict]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"{t['name']} ({t['default_pct']}%)", callback_data=f"tech:{t['id']}")]
        for t in technicians
    ]
    rows.append([InlineKeyboardButton(text='➕ تعمیرکار جدید', callback_data='tech:new')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def supplier_keyboard(suppliers: list[dict]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=s['name'], callback_data=f"sup:{s['id']}")]
        for s in suppliers
    ]
    rows.append([InlineKeyboardButton(text='➕ فروشنده قطعه جدید', callback_data='sup:new')])
    rows.append([InlineKeyboardButton(text='⏭ بدون فروشنده', callback_data='sup:skip')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def repair_actions(repair_id: int, *, is_open: bool = True, can_edit: bool = False) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(text='📊 Excel', callback_data=f'xlsx:{repair_id}'),
            InlineKeyboardButton(text='📄 PDF', callback_data=f'pdf:{repair_id}'),
        ],
        [
            InlineKeyboardButton(text='🧾 فاکتور', callback_data=f'inv:{repair_id}'),
            InlineKeyboardButton(text='💼 حسابداری', callback_data=f'acc:{repair_id}'),
        ],
    ]
    if is_open and can_edit:
        rows.append([InlineKeyboardButton(text='✏️ ویرایش پرونده', callback_data=f'edit:menu:{repair_id}')])
    rows.extend(
        [
            [
                InlineKeyboardButton(text='💵 دریافت مشتری', callback_data=f'pay_c:{repair_id}'),
                InlineKeyboardButton(text='💸 پرداخت قطعه‌فروش', callback_data=f'pay_s:{repair_id}'),
            ],
            [
                InlineKeyboardButton(text='💸 پرداخت تعمیرکار', callback_data=f'pay_t:{repair_id}'),
            ],
        ],
    )
    if is_open:
        rows.append([InlineKeyboardButton(text='✅ بستن پرونده', callback_data=f'close:{repair_id}')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def edit_repair_menu_keyboard(repair_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='💼 تغییر اجرت', callback_data=f'edit:labor:{repair_id}')],
            [InlineKeyboardButton(text='➕ افزودن قطعه', callback_data=f'edit:part:{repair_id}')],
            [InlineKeyboardButton(text='❌ انصراف', callback_data='edit:cancel')],
        ],
    )


def edit_parts_done_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='➕ قطعه دیگر')],
            [KeyboardButton(text='✅ پایان ویرایش')],
        ],
        resize_keyboard=True,
    )


def edit_supplier_keyboard(suppliers: list[dict]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=s['name'], callback_data=f'edit:sup:{s["id"]}')]
        for s in suppliers
    ]
    rows.append([InlineKeyboardButton(text='➕ فروشنده قطعه جدید', callback_data='edit:sup:new')])
    rows.append([InlineKeyboardButton(text='⏭ بدون فروشنده', callback_data='edit:sup:skip')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def search_result_keyboard(results: list[dict]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"#{r['id']} {r['customer_name'][:12]}", callback_data=f"view:{r['id']}")]
        for r in results[:8]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def settle_kind_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='👨‍🔧 تعمیرکار', callback_data='settle:kind:tech'),
                InlineKeyboardButton(text='🏪 فروشنده قطعه', callback_data='settle:kind:sup'),
            ],
        ],
    )


def settle_payee_keyboard(payees: list[dict], *, kind: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for row in payees[:12]:
        debt = int(row.get('debt') or 0)
        label = f"{row['name']} — مانده {debt:,}"
        entity_id = int(row['id'])
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f'settle:{kind}:{entity_id}')],
        )
    rows.append([InlineKeyboardButton(text='❌ انصراف', callback_data='settle:cancel')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def settle_action_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅ پرداخت کامل', callback_data='settle:full')],
            [InlineKeyboardButton(text='✏️ مبلغ جزئی', callback_data='settle:custom')],
            [InlineKeyboardButton(text='📋 انتخاب پرونده', callback_data='settle:pick')],
            [InlineKeyboardButton(text='❌ انصراف', callback_data='settle:cancel')],
        ],
    )


def settle_receive_action_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅ دریافت کامل', callback_data='settle:full')],
            [InlineKeyboardButton(text='✏️ مبلغ جزئی', callback_data='settle:custom')],
            [InlineKeyboardButton(text='📋 انتخاب پرونده', callback_data='settle:pick')],
            [InlineKeyboardButton(text='❌ انصراف', callback_data='settle:cancel')],
        ],
    )


def settle_repair_keyboard(repairs: list[dict]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for repair in repairs[:10]:
        debt = int(repair.get('debt') or 0)
        label = f"#{repair['id']} {repair.get('customer_name', '')[:10]} — {debt:,}"
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f"settle:repair:{repair['id']}")],
        )
    rows.append([InlineKeyboardButton(text='⬅️ بازگشت', callback_data='settle:back')])
    return InlineKeyboardMarkup(inline_keyboard=rows)
