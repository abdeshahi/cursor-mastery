from __future__ import annotations

from app.analysis.schema import AnalysisResult
from app.services.rate_provider import RateSnapshot

DIRECTION_LABELS = {
    'rial_weaker': '⚠️ فشار تقویت دلار / تضعیف ریال',
    'rial_stronger': '🟢 فشار تقویت ریال / ارزان‌تر شدن دلار',
    'neutral': 'ℹ️ خبر خنثی',
}

HORIZON_LABELS = {
    'hours': 'چند ساعت',
    '1_3_days': '۱ تا ۳ روز',
    'medium': 'میان‌مدت',
}

CONFIDENCE_LABELS = {
    'high': 'بالا',
    'medium': 'متوسط',
    'low': 'پایین',
}


def _rate_line(rate: RateSnapshot) -> str:
    if rate.value is None:
        return '💵 نرخ دلار آزاد: نامشخص'
    return f'💵 نرخ دلار آزاد: {rate.value:,.0f} تومان ({rate.label})'


def format_instant_alert(
    *,
    analysis: AnalysisResult,
    source_name: str,
    link: str,
    weighted_score: float,
    rate: RateSnapshot,
) -> str:
    lines = [
        DIRECTION_LABELS.get(analysis.direction, analysis.direction),
        f'📊 شدت: {analysis.intensity}/10 | افق: {HORIZON_LABELS.get(analysis.horizon, analysis.horizon)}',
        f'🎯 اطمینان: {CONFIDENCE_LABELS.get(analysis.confidence, analysis.confidence)} | امتیاز وزنی: {weighted_score}',
        _rate_line(rate),
        '',
        f'📰 {analysis.summary_fa}',
        f'💡 {analysis.why_fa}',
        f'🔗 منبع: {source_name}',
        link,
        '',
        '⚖️ این توصیه سرمایه‌گذاری قطعی نیست.',
    ]
    return '\n'.join(lines)


def format_cluster_alert(*, direction: str, rows: list[dict], total: float, rate: RateSnapshot) -> str:
    title = DIRECTION_LABELS.get(direction, direction)
    lines = [
        f'📦 هشدار تجمعی اخبار ({title})',
        f'📊 مجموع امتیاز {int(total)} در {len(rows)} محرک اصلی',
        _rate_line(rate),
        '',
    ]
    for index, row in enumerate(rows, start=1):
        lines.append(f'{index}. {row.get("summary_fa") or row.get("title")}')
    lines.extend(['', '⚖️ این توصیه سرمایه‌گذاری قطعی نیست.'])
    return '\n'.join(lines)


def format_digest(*, rows: list[dict], rate: RateSnapshot, hours: int) -> str:
    if not rows:
        return '\n'.join(
            [
                f'🗞️ خلاصه {hours} ساعت اخیر',
                _rate_line(rate),
                '',
                'خبر تأثیرگذاری ثبت نشده است.',
            ]
        )

    weaker = sum(float(row.get('weighted_score') or 0) for row in rows if row.get('direction') == 'rial_weaker')
    stronger = sum(float(row.get('weighted_score') or 0) for row in rows if row.get('direction') == 'rial_stronger')
    lines = [
        f'🗞️ خلاصه {hours} ساعت اخیر',
        _rate_line(rate),
        f'📉 فشار ضعیف شدن ریال: {weaker:.1f}',
        f'📈 فشار تقویت ریال: {stronger:.1f}',
        '',
        '🔎 مهم‌ترین موارد:',
    ]
    for index, row in enumerate(rows[:5], start=1):
        direction = DIRECTION_LABELS.get(row.get('direction', 'neutral'), 'خنثی')
        lines.append(f"{index}. {direction} | {row.get('summary_fa') or row.get('title')}")
    lines.append('\n⚖️ این توصیه سرمایه‌گذاری قطعی نیست.')
    return '\n'.join(lines)


def format_status(*, rate: RateSnapshot, latest: dict | None, users: int, jobs_paused: bool) -> str:
    lines = [
        '🛰️ وضعیت ربات هشدار ریال',
        f'👥 کاربران: {users}',
        f'⏱️ job: {"متوقف" if jobs_paused else "فعال"}',
        _rate_line(rate),
    ]
    if latest:
        lines.extend(
            [
                '',
                'آخرین تحلیل:',
                f"- {latest.get('summary_fa') or latest.get('title')}",
                f"- جهت: {DIRECTION_LABELS.get(latest.get('direction', 'neutral'), 'خنثی')}",
                f"- شدت: {latest.get('intensity')}/10",
            ]
        )
    return '\n'.join(lines)
