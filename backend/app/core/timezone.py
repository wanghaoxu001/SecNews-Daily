from datetime import datetime, timezone, timedelta

CHINA_TZ = timezone(timedelta(hours=8))


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_china() -> datetime:
    return datetime.now(CHINA_TZ)


def today_china_str() -> str:
    return now_china().strftime("%Y-%m-%d")
