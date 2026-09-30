from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    id: str
    name_fa: str
    banner: str
    primary: tuple[int, int, int]
    secondary: tuple[int, int, int]
    accent: tuple[int, int, int]
    labels: dict[str, str]

    def label(self, key: str) -> str:
        return self.labels[key]


MODERN_LABELS: dict[str, str] = {
    'root_reception': '📥 پذیرش',
    'root_accounting': '💼 حسابداری',
    'root_manage': '⚙️ مدیریت',
    'back_root': '⬅️ منوی اصلی',
    'help': 'ℹ️ راهنما',
    'mgmt_staff': '👥 پرسنل و دسترسی',
    'mgmt_tech': '👨‍🔧 تعمیرکاران',
    'mgmt_sup': '🏪 قطعه‌فروش',
    'mgmt_theme': '🎨 تم رنگی',
    'mgmt_staff_add': '➕ افزودن پرسنل',
    'mgmt_staff_invite': '🔗 لینک دعوت پرسنل',
    'mgmt_tech_add': '➕ افزودن تعمیرکار',
    'mgmt_sup_add': '➕ افزودن فروشنده',
    'rec_new': '📝 پذیرش جدید',
    'rec_list': '📋 لیست پرونده‌ها',
    'rec_search': '🔍 جستجو',
    'rec_invoice': '🧾 فاکتور',
    'rec_report': '📊 گزارش حسابداری',
    'acc_summary': '💰 خلاصه مالی',
    'acc_shop_profit': '🏢 سود فروشگاه',
    'acc_tech_share': '👨‍🔧 طلب تعمیرکاران',
    'acc_pay_debt': '💸 ثبت پرداخت بدهی',
    'acc_receive_customer': '💵 دریافت از مشتری',
    'acc_supplier_debt': '🏪 بدهی قطعه‌فروش',
    'acc_customer_debt': '👥 بدهی مشتریان',
    'acc_export_excel': '📊 خروجی Excel',
    'acc_export_pdf': '📄 خروجی PDF',
}


def _themed_labels(
    *,
    root_reception: str,
    root_accounting: str,
    root_manage: str,
    mgmt_staff: str,
    mgmt_tech: str,
    mgmt_sup: str,
    mgmt_theme: str,
    rec_new: str | None = None,
    acc_summary: str | None = None,
) -> dict[str, str]:
    labels = dict(MODERN_LABELS)
    labels['root_reception'] = root_reception
    labels['root_accounting'] = root_accounting
    labels['root_manage'] = root_manage
    labels['mgmt_staff'] = mgmt_staff
    labels['mgmt_tech'] = mgmt_tech
    labels['mgmt_sup'] = mgmt_sup
    labels['mgmt_theme'] = mgmt_theme
    if rec_new:
        labels['rec_new'] = rec_new
    if acc_summary:
        labels['acc_summary'] = acc_summary
    return labels


THEMES: dict[str, Theme] = {
    'warm': Theme(
        id='warm',
        name_fa='گرم',
        banner='🔥🌅 **تم گرم** — نارنجی و طلایی',
        primary=(210, 90, 45),
        secondary=(255, 210, 160),
        accent=(180, 60, 30),
        labels=_themed_labels(
            root_reception='🔥📥 پذیرش',
            root_accounting='🔥💼 حسابداری',
            root_manage='🔥⚙️ مدیریت',
            mgmt_staff='🔥👥 پرسنل و دسترسی',
            mgmt_tech='🔥👨‍🔧 تعمیرکاران',
            mgmt_sup='🔥🏪 قطعه‌فروش',
            mgmt_theme='🔥🎨 تم رنگی',
            rec_new='🔥📝 پذیرش جدید',
            acc_summary='🔥💰 خلاصه مالی',
        ),
    ),
    'cold': Theme(
        id='cold',
        name_fa='سرد',
        banner='❄️💎 **تم سرد** — آبی و یخی',
        primary=(45, 110, 190),
        secondary=(190, 220, 255),
        accent=(30, 80, 160),
        labels=_themed_labels(
            root_reception='❄️📥 پذیرش',
            root_accounting='❄️💼 حسابداری',
            root_manage='❄️⚙️ مدیریت',
            mgmt_staff='❄️👥 پرسنل و دسترسی',
            mgmt_tech='❄️👨‍🔧 تعمیرکاران',
            mgmt_sup='❄️🏪 قطعه‌فروش',
            mgmt_theme='❄️🎨 تم رنگی',
            rec_new='❄️📝 پذیرش جدید',
            acc_summary='❄️💰 خلاصه مالی',
        ),
    ),
    'autumn': Theme(
        id='autumn',
        name_fa='پاییزی',
        banner='🍂🍁 **تم پاییزی** — قهوه‌ای و نارنجی',
        primary=(150, 85, 40),
        secondary=(230, 190, 140),
        accent=(120, 60, 25),
        labels=_themed_labels(
            root_reception='🍂📥 پذیرش',
            root_accounting='🍂💼 حسابداری',
            root_manage='🍂⚙️ مدیریت',
            mgmt_staff='🍂👥 پرسنل و دسترسی',
            mgmt_tech='🍂👨‍🔧 تعمیرکاران',
            mgmt_sup='🍂🏪 قطعه‌فروش',
            mgmt_theme='🍂🎨 تم رنگی',
            rec_new='🍂📝 پذیرش جدید',
            acc_summary='🍂💰 خلاصه مالی',
        ),
    ),
    'spring': Theme(
        id='spring',
        name_fa='بهاری',
        banner='🌸🌿 **تم بهاری** — سبز و گل‌گون',
        primary=(70, 155, 95),
        secondary=(210, 245, 210),
        accent=(45, 120, 70),
        labels=_themed_labels(
            root_reception='🌸📥 پذیرش',
            root_accounting='🌸💼 حسابداری',
            root_manage='🌸⚙️ مدیریت',
            mgmt_staff='🌸👥 پرسنل و دسترسی',
            mgmt_tech='🌸👨‍🔧 تعمیرکاران',
            mgmt_sup='🌸🏪 قطعه‌فروش',
            mgmt_theme='🌸🎨 تم رنگی',
            rec_new='🌸📝 پذیرش جدید',
            acc_summary='🌸💰 خلاصه مالی',
        ),
    ),
    'pink': Theme(
        id='pink',
        name_fa='دخترونه صورتی',
        banner='💗🎀 **تم صورتی** — ملایم و شاد',
        primary=(220, 100, 150),
        secondary=(255, 220, 235),
        accent=(190, 70, 120),
        labels=_themed_labels(
            root_reception='💗📥 پذیرش',
            root_accounting='💗💼 حسابداری',
            root_manage='💗⚙️ مدیریت',
            mgmt_staff='💗👥 پرسنل و دسترسی',
            mgmt_tech='💗👨‍🔧 تعمیرکاران',
            mgmt_sup='💗🏪 قطعه‌فروش',
            mgmt_theme='💗🎨 تم رنگی',
            rec_new='💗📝 پذیرش جدید',
            acc_summary='💗💰 خلاصه مالی',
        ),
    ),
    'modern': Theme(
        id='modern',
        name_fa='مدرن',
        banner='✨ **تم مدرن** — پیش‌فرض CTTEL',
        primary=(55, 65, 85),
        secondary=(230, 232, 238),
        accent=(35, 45, 65),
        labels=dict(MODERN_LABELS),
    ),
    'wood': Theme(
        id='wood',
        name_fa='چوبی',
        banner='🪵🌳 **تم چوبی** — گرم و طبیعی',
        primary=(120, 78, 42),
        secondary=(215, 190, 160),
        accent=(90, 55, 28),
        labels=_themed_labels(
            root_reception='🪵📥 پذیرش',
            root_accounting='🪵💼 حسابداری',
            root_manage='🪵⚙️ مدیریت',
            mgmt_staff='🪵👥 پرسنل و دسترسی',
            mgmt_tech='🪵👨‍🔧 تعمیرکاران',
            mgmt_sup='🪵🏪 قطعه‌فروش',
            mgmt_theme='🪵🎨 تم رنگی',
            rec_new='🪵📝 پذیرش جدید',
            acc_summary='🪵💰 خلاصه مالی',
        ),
    ),
    'leather': Theme(
        id='leather',
        name_fa='چرم',
        banner='👜🟤 **تم چرم** — کلاسیک و مات',
        primary=(110, 75, 50),
        secondary=(210, 185, 155),
        accent=(80, 50, 30),
        labels=_themed_labels(
            root_reception='👜📥 پذیرش',
            root_accounting='👜💼 حسابداری',
            root_manage='👜⚙️ مدیریت',
            mgmt_staff='👜👥 پرسنل و دسترسی',
            mgmt_tech='👜👨‍🔧 تعمیرکاران',
            mgmt_sup='👜🏪 قطعه‌فروش',
            mgmt_theme='👜🎨 تم رنگی',
            rec_new='👜📝 پذیرش جدید',
            acc_summary='👜💰 خلاصه مالی',
        ),
    ),
    'glass': Theme(
        id='glass',
        name_fa='شیشه‌ای',
        banner='💎🫧 **تم شیشه‌ای** — روشن و شفاف',
        primary=(90, 160, 200),
        secondary=(225, 240, 250),
        accent=(60, 130, 180),
        labels=_themed_labels(
            root_reception='💎📥 پذیرش',
            root_accounting='💎💼 حسابداری',
            root_manage='💎⚙️ مدیریت',
            mgmt_staff='💎👥 پرسنل و دسترسی',
            mgmt_tech='💎👨‍🔧 تعمیرکاران',
            mgmt_sup='💎🏪 قطعه‌فروش',
            mgmt_theme='💎🎨 تم رنگی',
            rec_new='💎📝 پذیرش جدید',
            acc_summary='💎💰 خلاصه مالی',
        ),
    ),
    'metal': Theme(
        id='metal',
        name_fa='فلزی',
        banner='⚙️🔩 **تم فلزی** — صنعتی و مدرن',
        primary=(95, 100, 110),
        secondary=(210, 212, 218),
        accent=(60, 65, 75),
        labels=_themed_labels(
            root_reception='⚙️📥 پذیرش',
            root_accounting='⚙️💼 حسابداری',
            root_manage='⚙️⚙️ مدیریت',
            mgmt_staff='⚙️👥 پرسنل و دسترسی',
            mgmt_tech='⚙️👨‍🔧 تعمیرکاران',
            mgmt_sup='⚙️🏪 قطعه‌فروش',
            mgmt_theme='⚙️🎨 تم رنگی',
            rec_new='⚙️📝 پذیرش جدید',
            acc_summary='⚙️💰 خلاصه مالی',
        ),
    ),
}

DEFAULT_THEME_ID = 'modern'


def get_theme(theme_id: str | None) -> Theme:
    if theme_id and theme_id in THEMES:
        return THEMES[theme_id]
    return THEMES[DEFAULT_THEME_ID]


def list_themes() -> list[Theme]:
    order = ['warm', 'cold', 'autumn', 'spring', 'pink', 'modern', 'wood', 'leather', 'glass', 'metal']
    return [THEMES[tid] for tid in order]
