"""页面对象基类：统一封装显式等待与常用元素操作。

设计要点：
- 元素操作前使用显式等待（WebDriverWait），避免 sleep 式盲目等待；
- 等待超时读取自 config.ini [web] explicit_wait，集中可配；
- 元素定位方式统一使用 (By.XXX, value) 元组，Page Object 内部维护。
"""
import logging
from typing import List, Optional, Tuple

from selenium.common.exceptions import TimeoutException
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
