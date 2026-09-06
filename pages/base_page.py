"""页面对象基类：统一封装显式等待与常用元素操作。

设计要点：
- 元素操作前使用显式等待（WebDriverWait），避免 sleep 式盲目等待；
- 等待超时读取自 config.ini [web] explicit_wait，集中可配；
- 元素定位方式统一使用 (By.XXX, value) 元组，Page Object 内部维护。
"""
import logging
import time
from typing import Callable, List, Optional, Tuple

from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from common.config_util import get_int
from common.logger import get_logger

logger = get_logger("base_page")

# 定位器类型：(By.ID, "xxx")
Locator = Tuple[By, str]

# JS 条件脚本可用占位：页面对象传参时用它校验点击后的状态
JsCondition = Callable[[WebDriver], bool]


class BasePage:
    """所有页面对象的基类。"""

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.timeout = get_int("web", "explicit_wait", 10)

    # ---------------- 基础操作 ----------------
    def open_url(self, url: str) -> None:
        logger.info("打开页面: %s", url)
        self.driver.get(url)

    def find_element(self, locator: Locator, timeout: Optional[float] = None) -> WebElement:
        """等待元素可见后返回；超时抛 TimeoutException。"""
        wait = WebDriverWait(self.driver, timeout if timeout is not None else self.timeout)
        return wait.until(EC.visibility_of_element_located(locator))

    def find_elements(self, locator: Locator) -> List[WebElement]:
        """直接查找一组元素（可能为空，配合隐式等待使用）。"""
        return self.driver.find_elements(*locator)

    def is_element_visible(self, locator: Locator, timeout: float = 5.0) -> bool:
        """在给定时间内元素是否可见（不抛异常）。"""
        try:
            WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(locator))
            return True
        except TimeoutException:
            return False

    def click(self, locator: Locator) -> None:
        """等待元素可点击后点击。"""
        wait = WebDriverWait(self.driver, self.timeout)
        element = wait.until(EC.element_to_be_clickable(locator))
        logger.info("点击元素: %s", locator)
        element.click()

    def input_text(self, locator: Locator, text: str, need_clear: bool = True) -> None:
        """输入文本；默认先清空再输入。"""
        element = self.find_element(locator)
        if need_clear:
            element.clear()
        element.send_keys(text)
        logger.info("输入文本: %s -> %s", locator[1], text)

    def get_text(self, locator: Locator) -> str:
        return self.find_element(locator).text

    def get_title(self) -> str:
        return self.driver.title

    def get_current_url(self) -> str:
        return self.driver.current_url

    # ---------------- React 重渲染稳健操作 ----------------
    def _wait_js_until(self, js_script: str, timeout: float) -> bool:
        """轮询执行 JS 表达式直到返回真值（不依赖隐式等待，避免空查询阻塞）。"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                if self.driver.execute_script(js_script):
                    return True
            except Exception:  # noqa: BLE001 页面切换等瞬时异常按未达成处理
                pass
            time.sleep(0.3)
        return False

    def click_until(self, locator: Locator, js_condition: str,
                    description: str, attempts: int = 3, per_timeout: float = 6.0) -> None:
        """点击元素并等待 JS 条件成立；未成立则重新点击（最多 attempts 次）。

        背景：被测站点为 React 应用，慢速环境（CI）下点击可能落在 React 重渲染
        替换前的旧节点上导致“点击丢失”（无报错但无效果）。点击后校验状态提交
        （URL 变化 / 元素增删）可消除此类偶发失败。
        """
        for attempt in range(1, attempts + 1):
            try:
                element = WebDriverWait(self.driver, self.timeout).until(
                    EC.element_to_be_clickable(locator), message=f"元素不可点击: {locator}")
                element.click()
            except (StaleElementReferenceException, ElementClickInterceptedException):
                # React 恰好替换节点/出现瞬时遮挡：等一拍后整轮重试
                logger.warning("点击 %s 遇到元素被替换(%s)，重试", locator, attempt)
                time.sleep(0.5)
                continue
            if self._wait_js_until(js_condition, per_timeout):
                return
            logger.warning("点击后状态未达成(%s)，第 %s 次重试点击 %s", description, attempt, locator)
        raise TimeoutException(f"点击 {locator} 后状态未达成: {description}（已尝试 {attempts} 次）")
