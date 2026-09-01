from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='📝 پذیرش جدید'), KeyboardButton(text='📋 پرونده‌های باز')],
            [KeyboardButton(text='💰 گزارش بدهی‌ها'), KeyboardButton(text='👥 بدهی مشتریان')],
            [KeyboardButton(text='ℹ️ راهنما')],
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
                InlineKeyboardButton(text='💵 دریافت از مشتری', callback_data=f'pay_c:{repair_id}'),
                InlineKeyboardButton(text='💸 پرداخت به قطعه‌فروش', callback_data=f'pay_s:{repair_id}'),
            ],
            [InlineKeyboardButton(text='✅ بستن پرونده', callback_data=f'close:{repair_id}')],
        ],
    )
