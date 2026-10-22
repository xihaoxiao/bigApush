"""邮件通知（通用 SMTP，兼容 QQ邮箱 / 163 / Gmail / Outlook 等）。

与飞书、Server酱 一样：只有配置完整了才会发送，未配置则跳过。
配置来源优先级：环境变量 > config.yaml 的 email 段。
"""
import logging
import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr, formatdate, parseaddr

logger = logging.getLogger(__name__)

# 常见邮箱服务商的默认 SMTP 端口（用于自动判断 SSL / STARTTLS）
DEFAULT_PORTS = {
    "smtp.qq.com": 465,
    "smtp.163.com": 465,
    "smtp.126.com": 465,
    "smtp.yahoo.com": 465,
    "smtp.gmail.com": 587,
    "smtp.office365.com": 587,
    "smtp.exmail.qq.com": 465,
}

DEFAULT_SUBJECT = "缅A推送"


def _env(*names, default=""):
    for name in names:
        value = os.environ.get(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


def _as_bool(value, default=False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("1", "true", "yes", "on", "y"):
        return True
    if text in ("0", "false", "no", "off", "n"):
        return False
    return default


class EmailConfig:
    """SMTP 配置。"""

    def __init__(self, host="", port=None, user="", password="", sender="",
                 to="", use_ssl=None, use_tls=None, timeout=15):
        self.host = (host or "").strip()
        self.user = (user or "").strip()
        self.password = (password or "").strip()
        self.sender = (sender or "").strip()
        self.to = [addr.strip() for addr in (to or "").replace(";", ",").split(",") if addr.strip()]
        # 收件人留空时，默认发给登录账号（与 README 描述保持一致）
        if not self.to and self.user:
            self.to = [self.user]

        if port in (None, ""):
            self.port = DEFAULT_PORTS.get(self.host.lower(), 465)
        else:
            try:
                self.port = int(port)
            except (TypeError, ValueError):
                self.port = DEFAULT_PORTS.get(self.host.lower(), 465)

        # 未显式指定时按端口推断：465 走隐式 SSL，其它走 STARTTLS
        if use_ssl is None:
            self.use_ssl = self.port == 465
        else:
            self.use_ssl = _as_bool(use_ssl, self.port == 465)
        if use_tls is None:
            self.use_tls = not self.use_ssl
        else:
            self.use_tls = _as_bool(use_tls, not self.use_ssl)

        self.timeout = timeout

    @property
    def configured(self) -> bool:
        """发送方 + 收件方 + 密码齐全才算可发送。"""
        return bool(self.host and self.user and self.password and self.to)

    @property
    def missing_fields(self) -> list:
        """列出缺失的必填项（用于给出可操作的报错，而不是静默跳过）。"""
        missing = []
        if not self.host:
            missing.append("SMTP_HOST")
        if not self.user:
            missing.append("SMTP_USER")
        if not self.password:
            missing.append("SMTP_PASSWORD")
        if not self.to:
            missing.append("SMTP_TO(或 SMTP_USER)")
        return missing

    @property
    def partially_configured(self) -> bool:
        """有配置但不全 —— 说明用户想用邮箱推送，只是缺了某几项。"""
        return not self.configured and bool(
            self.host or self.user or self.password or self.to or self.sender
        )

    @classmethod
    def from_env_and_config(cls, config=None) -> "EmailConfig":
        config = config or {}
        email_cfg = config.get("email") or config.get("smtp") or {}

        host = _env("SMTP_HOST", "EMAIL_HOST") or str(email_cfg.get("host") or "")
        env_port = _env("SMTP_PORT", "EMAIL_PORT")
        port = env_port or email_cfg.get("port")
        user = (_env("SMTP_USER", "EMAIL_USER", "SMTP_USERNAME")
                or str(email_cfg.get("user") or email_cfg.get("username") or ""))
        password = (_env("SMTP_PASSWORD", "EMAIL_PASSWORD", "SMTP_PASS", "EMAIL_PASS")
                    or str(email_cfg.get("password") or email_cfg.get("pass") or ""))
        sender = (_env("SMTP_FROM", "EMAIL_FROM", "SMTP_SENDER")
                  or str(email_cfg.get("from") or email_cfg.get("sender") or ""))
        to = (_env("SMTP_TO", "EMAIL_TO", "SMTP_RECIPIENTS")
              or str(email_cfg.get("to") or email_cfg.get("recipients") or ""))

        env_use_ssl = _env("SMTP_USE_SSL", "EMAIL_USE_SSL")
        env_use_tls = _env("SMTP_USE_TLS", "EMAIL_USE_TLS")

        # SSL/TLS 决策优先级：
        # 1) 环境变量显式指定 → 遵从
        # 2) 端口由环境变量指定但没给 SSL/TLS 标志 → 按端口推断
        #    （否则 config.yaml 里的 use_ssl: true 会把 587 端口也强制成 SSL）
        # 3) 否则用配置文件的值 → 都没有则按端口推断
        if env_use_ssl:
            use_ssl = env_use_ssl
        elif env_use_tls:
            use_ssl = False         # 显式要 STARTTLS → 不再用隐式 SSL
        elif env_port:
            use_ssl = None          # 交给 __init__ 按端口推断
        else:
            use_ssl = email_cfg.get("use_ssl")

        if env_use_tls:
            use_tls = env_use_tls
        elif env_use_ssl:
            use_tls = False         # 显式要 SSL → 不再叠加 STARTTLS
        elif env_port:
            use_tls = None          # 交给 __init__ 按端口推断
        else:
            use_tls = email_cfg.get("use_tls")

        return cls(
            host=host,
            port=port,
            user=user,
            password=password,
            sender=sender,
            to=to,
            use_ssl=None if use_ssl in (None, "") else use_ssl,
            use_tls=None if use_tls in (None, "") else use_tls,
        )

    def resolved_sender(self):
        """发件人：优先用显式配置，否则用登录账号。"""
        return self.sender or self.user


def _build_html(subject: str, text: str) -> str:
    """把纯文本消息转成简单 HTML（保留换行）。"""
    from html import escape

    body = escape(text or "").replace("\n", "<br>\n")
    return (
        "<!DOCTYPE html><html><body style=\"font-family:-apple-system,Segoe UI,"
        "Helvetica,Arial,sans-serif;font-size:14px;line-height:1.7;color:#1f2329;\">"
        f"<h2 style=\"margin:0 0 12px;font-size:18px;\">{escape(subject)}</h2>"
        f"<div style=\"white-space:pre-wrap;\">{body}</div>"
        "</body></html>"
    )


class EmailNotifier:
    """SMTP 邮件发送器。"""

    def __init__(self, config: EmailConfig = None):
        self.config = config or EmailConfig()

    def send_text(self, text: str, title: str = "") -> bool:
        cfg = self.config
        if not cfg.configured:
            logger.warning("邮箱 SMTP 配置不完整，跳过邮件推送")
            return False

        subject = (title or _first_line(text) or DEFAULT_SUBJECT).strip()[:100]
        sender = cfg.resolved_sender()

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = formataddr((_display_name(sender), sender))
        message["To"] = ", ".join(cfg.to)
        message["Date"] = formatdate(localtime=True)
        message.set_content(text or "", cte="base64")
        message.add_alternative(_build_html(subject, text or ""), subtype="html", cte="base64")

        try:
            if cfg.use_ssl:
                server = smtplib.SMTP_SSL(cfg.host, cfg.port, timeout=cfg.timeout)
            else:
                server = smtplib.SMTP(cfg.host, cfg.port, timeout=cfg.timeout)

            with server:
                server.ehlo()
                if cfg.use_tls and not cfg.use_ssl:
                    server.starttls()
                    server.ehlo()
                server.login(cfg.user, cfg.password)
                server.send_message(message)
            logger.info("邮件推送成功: %s -> %s", sender, ", ".join(cfg.to))
            return True
        except smtplib.SMTPAuthenticationError as e:
            logger.error("邮件推送失败（认证错误，请检查授权码/密码）: %s", e)
            return False
        except smtplib.SMTPException as e:
            logger.error("邮件推送失败（SMTP 错误）: %s", e)
            return False
        except Exception as e:
            logger.error("邮件推送异常: %s", e)
            return False


def _first_line(text: str) -> str:
    for line in (text or "").splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def _display_name(address: str) -> str:
    """从 '名称 <地址>' 中取出名称部分。"""
    name, _addr = parseaddr(address or "")
    return name or ""
