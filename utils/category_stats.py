"""选股信号的分类统计与过滤。

背景：早期系统只有「回落碗中 / 靠近多空线 / 靠近短期趋势线」一个策略，
      分类信息写在信号的 'category' 字段里。后来扩展到 15 个策略，
      只有 MultiPartyCannon 仍写 'category'，其余策略的信号没有该字段。

      早期代码直接 `category_count.get('bowl_center', 0)` 统计，
      于是推送里这三个分类恒为 0 只，且 --category 过滤形同虚设。

本模块提供统一的统计与过滤逻辑：
  - 无 category 的信号统一归入 'unknown'（未分类），不会被静默丢弃
  - 过滤时 'all' 保留全部，具名分类只保留真正匹配的
"""

# 分类的展示顺序与图标
CATEGORY_ORDER = ("bowl_center", "near_duokong", "near_short_trend")
CATEGORY_LABELS = {
    "bowl_center": "回落碗中",
    "near_duokong": "靠近多空线",
    "near_short_trend": "靠近短期趋势线",
    "unknown": "未分类",
}
CATEGORY_EMOJIS = {
    "bowl_center": "🥣",
    "near_duokong": "📊",
    "near_short_trend": "📈",
    "unknown": "🏷️",
}

UNKNOWN = "unknown"


def _category_of(signal) -> str:
    """取出信号的分类，缺失统一记为 'unknown'。"""
    if not isinstance(signal, dict):
        return UNKNOWN
    cat = signal.get("category")
    if not cat or not isinstance(cat, str):
        return UNKNOWN
    return cat


def summarize_categories(signals) -> dict:
    """统计各分类数量。

    Returns:
        {"bowl_center": 2, "unknown": 5, ..., "total": 7}
    """
    summary = {cat: 0 for cat in CATEGORY_ORDER}
    summary[UNKNOWN] = 0
    total = 0
    for s in signals or []:
        cat = _category_of(s)
        summary[cat] = summary.get(cat, 0) + 1
        total += 1
    summary["total"] = total
    return summary


def filter_by_category(signals, category: str = "all") -> list:
    """按分类过滤信号。

    - category 为 'all' 或空 → 全部保留
    - category 为 'unknown' → 只保留没有分类或 category 为 unknown 的
    - 其它 → 只保留 category 完全匹配的
    """
    signals = list(signals or [])
    if not category or category == "all":
        return signals
    return [s for s in signals if _category_of(s) == category]


def format_category_lines(summary: dict) -> list:
    """把统计结果格式化成可打印的多行文本。"""
    lines = []
    for cat in CATEGORY_ORDER:
        emoji = CATEGORY_EMOJIS.get(cat, "❓")
        label = CATEGORY_LABELS.get(cat, cat)
        lines.append(f"  {emoji} {label}: {summary.get(cat, 0)} 只")
    if summary.get(UNKNOWN, 0):
        emoji = CATEGORY_EMOJIS[UNKNOWN]
        lines.append(f"  {emoji} {CATEGORY_LABELS[UNKNOWN]}: {summary[UNKNOWN]} 只")
    lines.append(f"  📌 合计: {summary.get('total', 0)} 只")
    return lines
