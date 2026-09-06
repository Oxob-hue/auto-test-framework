"""配置读取工具。

- 统一从项目根目录的 config.ini 读取配置，与“运行命令时所在目录”无关；
- 支持**环境变量覆盖**：`TEST_<SECTION>_<KEY>`（大写）优先级高于 config.ini，
  便于在 CI（如 GitHub Actions）不改配置文件即可切换浏览器、无头模式等；
- 提供字符串 / 整型 / 布尔 / 路径等类型化读取方法；
- 暴露 PROJECT_ROOT（项目根目录），供测试数据、日志等路径统一拼接。
"""
import configparser
import os
from pathlib import Path
from typing import Optional

# 项目根目录：本文件位于 <root>/common/config_util.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent

_config = configparser.ConfigParser()
_config.read(PROJECT_ROOT / "config.ini", encoding="utf-8")


def _env_key(section: str, key: str) -> str:
    """环境变量命名：TEST_WEB_HEADLESS / TEST_API_BASE_URL 等。"""
    return f"TEST_{section}_{key}".upper()


def _env_value(section: str, key: str) -> Optional[str]:
    value = os.environ.get(_env_key(section, key))
    return value if value is not None else None


def get_config(section: str, key: str, fallback: Optional[str] = None) -> str:
    """读取配置项（字符串）。优先级：环境变量 > config.ini > fallback。"""
    env_value = _env_value(section, key)
    if env_value is not None:
        return env_value
    if fallback is not None:
        return _config.get(section, key, fallback=fallback)
    try:
        return _config.get(section, key)
    except (configparser.NoSectionError, configparser.NoOptionError) as exc:
        raise KeyError(f"config.ini 缺少配置项 [{section}] {key}") from exc


def get_int(section: str, key: str, fallback: Optional[int] = None) -> int:
    """读取整型配置项。"""
    env_value = _env_value(section, key)
    if env_value is not None:
        return int(env_value)
    if fallback is not None:
        return _config.getint(section, key, fallback=fallback)
    return _config.getint(section, key)


def get_bool(section: str, key: str, fallback: Optional[bool] = None) -> bool:
    """读取布尔配置项（true/false/1/0/yes/no）。"""
    env_value = _env_value(section, key)
    if env_value is not None:
        normalized = env_value.strip().lower()
        if normalized in ("1", "true", "yes", "on"):
            return True
        if normalized in ("0", "false", "no", "off"):
            return False
        raise ValueError(f"非法布尔配置: {_env_key(section, key)}={env_value!r}")
    if fallback is not None:
        return _config.getboolean(section, key, fallback=fallback)
    return _config.getboolean(section, key)


def get_path(section: str, key: str) -> Path:
    """读取路径配置项；相对路径基于项目根目录解析。"""
    raw = get_config(section, key)
    path = Path(raw)
    return path if path.is_absolute() else PROJECT_ROOT / path
