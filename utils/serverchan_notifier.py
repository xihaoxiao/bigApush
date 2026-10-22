"""Server酱通知（兼容 Server酱 Turbo 与 Server酱³）"""
import logging
import re

import requests

logger = logging.getLogger(__name__)

MAX_TITLE_LEN = 32
MAX_DESP_LEN = 30000  # Server酱单条消息上限约 32KB


class ServerChanNotifier:
    def __init__(self, sendkey: str = ""):
        self.sendkey = (sendkey or "").strip()

    @property
    def configured(self) -> bool:
        return bool(self.sendkey)

    def _build_url(self) -> str:
        key = self.sendkey
        # 允许直接填写完整推送地址
        if key.startswith("http://") or key.startswith("https://"):
            return key
        # Server酱³ 的 SendKey 形如 sctp12345t...，推送到 {uid}.push.ft07.com
        match = re.match(r"^sctp(\d+)t", key)
        if match:
            return f"https://{match.group(1)}.push.ft07.com/send/{key}.send"
        # Server酱 Turbo（旧版）
        return f"https://sctapi.ftqq.com/{key}.send"

    def send_text(self, text: str, title: str = "") -> bool:
        if not self.configured:
            logger.warning("Server酱 sendkey 未配置")
            return False

        title = (title or self._default_title(text))[:MAX_TITLE_LEN]
        desp = text
        if len(desp) > MAX_DESP_LEN:
            desp = desp[:MAX_DESP_LEN] + "\n\n...（内容过长已截断）"

        try:
            resp = requests.post(
                self._build_url(),
                data={"title": title, "desp": desp},
                timeout=15,
            )
            try:
                result = resp.json()
            except ValueError:
                logger.error(
                    "Server酱推送失败: HTTP %s %s",
                    resp.status_code,
                    (resp.text or "")[:200],
                )
                return False

            if result.get("code") == 0:
                logger.info("Server酱推送成功")
                return True
            logger.error("Server酱推送失败: %s", result)
            return False
        except Exception as e:
            logger.error("Server酱推送异常: %s", e)
            return False

    @staticmethod
    def _default_title(text: str) -> str:
        for line in text.splitlines():
            line = line.strip()
            if line:
                return line[:MAX_TITLE_LEN]
        return "缅A推送"
