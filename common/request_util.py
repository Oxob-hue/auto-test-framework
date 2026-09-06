"""HTTP 接口请求统一封装。

设计要点：
1. Session 复用 —— 底层连接复用（keep-alive），多次请求性能更好；
2. base_url 拼接 —— 支持绝对地址与相对路径两种写法；
3. 统一超时 —— 防止个别请求长时间挂死拖垮用例；
4. 请求 / 响应日志 —— 便于排障与 Allure 报告中定位问题。
"""
from typing import Any, Optional

import requests

from common.config_util import get_config, get_int
from common.logger import get_logger

logger = get_logger("request_util")


class RequestUtil:
    """接口请求工具类。"""

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[int] = None):
        self.base_url = (base_url or get_config("api", "base_url")).rstrip("/")
        self.timeout = timeout if timeout is not None else get_int("api", "timeout", 15)
        self.session = requests.Session()
        logger.info("RequestUtil 初始化 base_url=%s timeout=%s", self.base_url, self.timeout)

    def _build_url(self, url: str) -> str:
        """相对路径自动拼上 base_url，绝对地址原样返回。"""
        if url.startswith(("http://", "https://")):
            return url
        return f"{self.base_url}/{url.lstrip('/')}"

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        """通用请求入口，参数与 requests.request 一致。"""
        method = method.upper()
        full_url = self._build_url(url)
        kwargs.setdefault("timeout", self.timeout)

        # 日志仅记录关键信息，避免把敏感报文刷屏
        body_preview = ""
        if "json" in kwargs:
            body_preview = f" body={str(kwargs['json'])[:200]}"
        logger.info(">>> %s %s%s", method, full_url, body_preview)

        resp = self.session.request(method, full_url, **kwargs)

        try:
            text_preview = resp.text[:300]
        except Exception:  # noqa: BLE001 响应体读取失败不影响日志
            text_preview = "<response body unreadable>"
        logger.info("<<< %s %s 状态码=%s 耗时=%.2fs body=%s",
                    method, full_url, resp.status_code,
                    resp.elapsed.total_seconds(), text_preview)
        return resp

    # ---------- 常用方法快捷封装 ----------
    def get(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("DELETE", url, **kwargs)


# 模块级单例：兼容旧式 send_request(method, url, **kwargs) 调用
send_request = RequestUtil().request
