from datetime import datetime
from holidays_ru import check_holiday
from config import START_HOUR, START_MINUTE, END_HOUR, END_MINUTE, WORKDAYS


def is_work_time(now: datetime) -> bool:
    """Проверяет: будний день, не праздник, время в окне показа."""
    if now.weekday() not in WORKDAYS:
        return False
    if check_holiday(now.date(), with_weekends=False):
        return False
    start = now.replace(hour=START_HOUR, minute=START_MINUTE, second=0, microsecond=0)
    end = now.replace(hour=END_HOUR, minute=END_MINUTE, second=0, microsecond=0)
    return start <= now < end
