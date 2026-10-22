"""统一配置加载。

读取顺序（后者覆盖前者）：
1. config/config.defaults.yaml   —— 提交到仓库，只含非敏感配置
2. config/config.yaml            —— 兼容旧路径（已 gitignore，CI 上不存在）
3. config/config.local.yaml      —— 本地凭据覆盖（已 gitignore，永不提交）
4. 环境变量 / GitHub Secrets      —— 最高优先级（见 push_notifier / email_notifier）

凭据（飞书 Webhook / Server酱 SendKey / SMTP 密码）只允许出现在
config.local.yaml 或环境变量里，不允许进仓库。
"""
import logging
import os

try:
    import yaml
except ImportError:  # pragma: no cover - 轻量脚本可能未装 PyYAML
    yaml = None

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, "config")

# 加载优先级从低到高
CONFIG_CANDIDATES = (
    "config.defaults.yaml",   # 仓库内，非敏感默认值
    "config.yaml",            # 兼容旧路径（本地/CI 均可能存在）
    "config.local.yaml",      # 本地凭据，永不提交
)

# 含凭据的字段：只允许来自 local 文件或环境变量
CREDENTIAL_SECTIONS = ("feishu", "serverchan", "email", "smtp", "dingtalk")


def _read_yaml(path):
    if yaml is None:
        logger.warning("未安装 PyYAML，跳过配置文件 %s（仅支持环境变量配置）", path)
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}
    except Exception as e:
        logger.warning("读取配置失败 %s: %s", path, e)
        return {}


def _deep_merge(base: dict, override: dict) -> dict:
    """递归合并：override 覆盖 base，嵌套字典逐层合并。"""
    result = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        elif value is not None:
            result[key] = value
    return result


def load_config(config_dir: str = None, include_local: bool = True) -> dict:
    """加载合并后的配置。

    Args:
        config_dir: 配置目录，默认项目下的 config/
        include_local: 是否加载 config.local.yaml（本地开发用）
    """
    config_dir = config_dir or CONFIG_DIR
    merged = {}

    for name in CONFIG_CANDIDATES:
        if name == "config.local.yaml" and not include_local:
            continue
        path = os.path.join(config_dir, name)
        if not os.path.isfile(path):
            continue
        data = _read_yaml(path)
        if data:
            merged = _deep_merge(merged, data)
            logger.debug("已加载配置: %s", path)

    if not merged:
        logger.debug("未找到任何配置文件，仅使用环境变量")

    return merged


def load_credential_free_config(config_dir: str = None) -> dict:
    """加载配置但剔除凭据段（用于日志打印等场景，避免泄露）。"""
    config = load_config(config_dir)
    return {
        k: v for k, v in config.items()
        if k not in CREDENTIAL_SECTIONS
    }


def config_path(config_dir: str = None) -> str:
    """返回实际使用的配置文件路径（优先 local）。"""
    config_dir = config_dir or CONFIG_DIR
    for name in ("config.local.yaml", "config.yaml", "config.defaults.yaml"):
        path = os.path.join(config_dir, name)
        if os.path.isfile(path):
            return path
    return os.path.join(config_dir, "config.defaults.yaml")
