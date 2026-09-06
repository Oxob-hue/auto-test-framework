"""统一日志模块。

- 控制台 + 文件双输出，日志目录自动创建；
- 同一 name 只初始化一次 handler，避免重复打印；
- 文件输出不可用（如无写权限）时降级为仅控制台，不影响用例执行。
"""
import logging
import sys
from typing import Optional

from common.config_util import PROJECT_ROOT, get_config

LOG_DIR = PROJECT_ROOT / get_config("log", "dir", "logs")
LOG_FILE = LOG_DIR / get_config("log", "file", "test.log")


class _ConsoleHandler(logging.Handler):
    """控制台处理器：每次输出时动态获取当前 stdout。

    避免测试框架（如 pytest 的捕获机制）切换/关闭原始流后，
    日志仍写向已关闭流而抛出 ValueError。
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            stream = sys.stdout if sys.stdout is not None else sys.stderr
            stream.write(self.format(record) + "\n")
            stream.flush()
        except Exception:  # noqa: BLE001 控制台不可用时不中断主流程
            self.handleError(record)


def _build_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:  # 已初始化，直接复用
        return logger

    level_name = get_config("log", "level", "INFO").upper()
    logger.setLevel(getattr(logging, level_name, logging.INFO))
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 1) 控制台输出（动态 stdout，避免测试框架关闭流后报错）
    console_handler = _ConsoleHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2) 文件输出（失败时降级，仅保留控制台）
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        logger.warning("日志文件不可写，本次仅输出到控制台: %s", LOG_FILE)

    logger.propagate = False  # 避免向根 logger 重复传递
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取（或创建）统一配置的 logger。name 缺省按模块自动命名。"""
    logger_name = name or __name__
    return _build_logger(logger_name)
