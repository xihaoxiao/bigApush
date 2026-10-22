"""统一时间处理：所有业务时间一律使用北京时间（UTC+8）。

为什么需要这个模块：
    GitHub Actions 的 runner 使用 UTC 时区，而 A 股的交易时间、
    收盘判断、推送时间戳都是北京时间。若直接用 datetime.now()，
    在 runner 上会得到 UTC 时间，导致：
      - 北京 15:19 被误判为"未收盘"（UTC 07:19 < 15:00）→ 跳过数据更新
      - 推送标题显示 UTC 时间，与实际推送时刻对不上

本模块提供不依赖 runner 时区的北京时间接口。
"""
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

# 中国自 1991 年起不再使用夏令时，固定 UTC+8 即可，
# 这样即使系统缺少 tzdata 也能正确工作。
CN_UTC_OFFSET = timedelta(hours=8)

try:
    from zoneinfo import ZoneInfo
    CN_TZ = ZoneInfo("Asia/Shanghai")
except Exception:  # pragma: no cover - 缺少 tzdata 时降级
    CN_TZ = timezone(CN_UTC_OFFSET, name="Asia/Shanghai")

# 收盘时间（北京时间）
MARKET_CLOSE_HOUR = 15
MARKET_CLOSE_MINUTE = 0


def now_cn() -> datetime:
    """当前北京时间（带 +08:00 时区）。"""
    return datetime.now(CN_TZ)


def today_cn() -> str:
    """今天的北京时间日期，格式 YYYY-MM-DD。"""
    return now_cn().strftime("%Y-%m-%d")


def now_cn_str(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """当前北京时间字符串。"""
    return now_cn().strftime(fmt)


def is_after_close(now=None, close_hour: int = MARKET_CLOSE_HOUR,
                   close_minute: int = MARKET_CLOSE_MINUTE) -> bool:
    """给定时刻是否已过收盘时间。

    Args:
        now: 待判断的时刻；None 表示取当前北京时间。
             传入 naive datetime 时按北京时间解释。
        close_hour: 收盘小时（北京时间），默认 15
        close_minute: 收盘分钟，默认 0

    修复前 _smart_update() 用 datetime.now()（runner 本地时间，CI 上是 UTC）
    判断，导致北京时间 15:19 被误判为"未收盘"而跳过数据更新。
    """
    if now is None:
        now = now_cn()
    elif now.tzinfo is None:
        now = now.replace(tzinfo=CN_TZ)
    else:
        # 带时区的时间先换算到北京时间再比较
        now = now.astimezone(CN_TZ)
    return (now.hour, now.minute) >= (close_hour, close_minute)


def describe() -> str:
    """描述当前时区信息，便于日志排查。"""
    local = datetime.now()
    return (
        f"runner_local={local.strftime('%Y-%m-%d %H:%M:%S')} "
        f"beijing={now_cn_str()} (UTC+8)"
    )
