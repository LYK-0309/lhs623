"""时间工具 — 统一使用北京时间（UTC+8）"""

from datetime import datetime, timezone, timedelta

# 北京时区（UTC+8）
BEIJING_TZ = timezone(timedelta(hours=8))


def beijing_now():
    """
    返回当前北京时间（naive datetime，无时区信息）
    用于 SQLAlchemy default 参数和代码中的时间获取
    """
    return datetime.now(BEIJING_TZ).replace(tzinfo=None)


def format_beijing(dt, fmt='%Y-%m-%d %H:%M:%S'):
    """
    将 datetime 格式化为北京时间字符串
    如果 dt 是 naive（无时区），直接格式化；
    如果 dt 是 aware（有时区），先转为北京时间再格式化。
    """
    if dt is None:
        return ''
    if dt.tzinfo is None:
        # 假设存储的是北京时间（naive），直接格式化
        return dt.strftime(fmt)
    else:
        # 有时区信息，转换为北京时间
        beijing_dt = dt.astimezone(BEIJING_TZ)
        return beijing_dt.strftime(fmt)
