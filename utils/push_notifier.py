"""统一推送入口。

按已配置的渠道推送（飞书 Webhook / Server酱 SendKey）：
- 只配置一个时只推该渠道；
- 两个都配置时同时推送。
"""
import logging
import os

from utils.feishu_notifier import FeishuNotifier
from utils.serverchan_notifier import ServerChanNotifier

logger = logging.getLogger(__name__)

FEISHU_ENV_KEYS = ("FEISHU_WEBHOOK",)
SERVERCHAN_ENV_KEYS = ("SERVERCHAN_SENDKEY", "SERVER_CHAN_SENDKEY", "SCKEY")


def _first_env(names) -> str:
    for name in names:
        value = (os.environ.get(name) or "").strip()
        if value:
            return value
    return ""


def resolve_channels(config=None) -> dict:
    """读取环境变量与配置文件，返回已配置的渠道 {渠道名: 配置值}。"""
    config = config or {}
    feishu_cfg = config.get("feishu") or {}
    serverchan_cfg = config.get("serverchan") or {}

    feishu_webhook = _first_env(FEISHU_ENV_KEYS) or str(
        feishu_cfg.get("webhook_url") or ""
    ).strip()
    sendkey = _first_env(SERVERCHAN_ENV_KEYS) or str(
        serverchan_cfg.get("sendkey") or serverchan_cfg.get("sckey") or ""
    ).strip()

    channels = {}
    if feishu_webhook:
        channels["feishu"] = feishu_webhook
    if sendkey:
        channels["serverchan"] = sendkey
    return channels


def has_channel(config=None) -> bool:
    return bool(resolve_channels(config))


def push_text(text: str, config=None, title: str = "") -> dict:
    """向所有已配置的渠道推送文本。

    返回 {"feishu": bool | None, "serverchan": bool | None}，
    None 表示该渠道未配置。
    """
    channels = resolve_channels(config)
    result = {"feishu": None, "serverchan": None}

    if not channels:
        logger.warning("未配置任何推送渠道（飞书 / Server酱），跳过推送")
        return result

    if "feishu" in channels:
        try:
            result["feishu"] = FeishuNotifier(channels["feishu"]).send_text(text)
        except Exception as e:
            logger.error("飞书推送异常: %s", e)
            result["feishu"] = False

    if "serverchan" in channels:
        try:
            result["serverchan"] = ServerChanNotifier(channels["serverchan"]).send_text(
                text, title
            )
        except Exception as e:
            logger.error("Server酱推送异常: %s", e)
            result["serverchan"] = False

    return result
