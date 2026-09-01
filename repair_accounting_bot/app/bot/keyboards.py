from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

ROOT_RECEPTION = '📥 پذیرش'
ROOT_ACCOUNTING = '💼 حسابداری'
BACK_ROOT = '⬅️ منوی اصلی'

REC_NEW = '📝 پذیرش جدید'
REC_SEARCH = '🔍 جستجو'
REC_INVOICE = '🧾 فاکتور'
REC_REPORT = '📊 گزارش حسابداری'

ACC_SUMMARY = '💰 خلاصه مالی'
ACC_SHOP_PROFIT = '🏢 سود فروشگاه'
ACC_TECH_SHARE = '👨‍🔧 سهم تعمیرکاران'
ACC_SUPPLIER_DEBT = '🏪 بدهی قطعه‌فروش'
ACC_CUSTOMER_DEBT = '👥 بدهی مشتریان'


def root_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ROOT_RECEPTION), KeyboardButton(text=ROOT_ACCOUNTING)],
            [KeyboardButton(text='ℹ️ راهنما')],
        ],
        resize_keyboard=True,
    )


def reception_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=REC_NEW), KeyboardButton(text=REC_SEARCH)],
            [KeyboardButton(text=REC_INVOICE), KeyboardButton(text=REC_REPORT)],
            [KeyboardButton(text=BACK_ROOT)],
        ],
        resize_keyboard=True,
    )


def accounting_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ACC_SUMMARY), KeyboardButton(text=ACC_SHOP_PROFIT)],
            [KeyboardButton(text=ACC_TECH_SHARE), KeyboardButton(text=ACC_SUPPLIER_DEBT)],
            [KeyboardButton(text=ACC_CUSTOMER_DEBT)],
            [KeyboardButton(text=BACK_ROOT)],
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


def repair_actions(repair_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='🧾 فاکتور', callback_data=f'inv:{repair_id}'),
                InlineKeyboardButton(text='💼 حسابداری', callback_data=f'acc:{repair_id}'),
            ],
            [
                InlineKeyboardButton(text='💵 دریافت مشتری', callback_data=f'pay_c:{repair_id}'),
                InlineKeyboardButton(text='💸 پرداخت قطعه‌فروش', callback_data=f'pay_s:{repair_id}'),
            ],
            [InlineKeyboardButton(text='✅ بستن پرونده', callback_data=f'close:{repair_id}')],
        ],
    )


def search_result_keyboard(results: list[dict]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"#{r['id']} {r['customer_name'][:12]}", callback_data=f"view:{r['id']}")]
        for r in results[:8]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
