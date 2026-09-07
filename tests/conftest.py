"""全局夹具与钩子（唯一的 conftest，避免在其它层级重复定义导致 fixture 遮蔽 / hook 重复执行）。"""
import sys

import allure
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService

from api.pet_api import PetApi
from common.config_util import get_bool, get_config, get_int
from common.logger import LOG_FILE, get_logger
from common.request_util import RequestUtil

logger = get_logger("conftest")


# ---------------------------------------------------------------- fixtures
@pytest.fixture(scope="session")
def base_url() -> str:
    """Web 被测环境地址（来自 config.ini）。"""
    return get_config("web", "base_url")


@pytest.fixture(scope="function")
def driver():
    """Web 测试浏览器驱动：按配置启动（edge/chrome、无头、等待、超时），用例结束自动退出。

    - 浏览器类型与无头模式支持环境变量覆盖（TEST_WEB_BROWSER / TEST_WEB_HEADLESS），
      便于 CI 无界面环境直接复用同一套用例；
    - chrome 未指定驱动路径时交由 Selenium Manager 自动匹配，开箱即用。
    """
    browser_name = get_config("web", "browser", "edge").strip().lower()
    headless = get_bool("web", "headless", False)

    if browser_name == "chrome":
        options = ChromeOptions()
        service = None  # Selenium Manager 自动处理 chromedriver
        driver_cls = webdriver.Chrome
    else:  # 默认 edge
        options = EdgeOptions()
        service = EdgeService(get_config("web", "driver_path"))
        driver_cls = webdriver.Edge

    # 开启浏览器 console 日志，便于失败时分析前端 JS 错误（如 React 异常）
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    if sys.platform.startswith("linux"):  # CI/容器内必需
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    browser = driver_cls(service=service, options=options)
    browser.implicitly_wait(get_int("web", "implicit_wait", 10))
    browser.set_page_load_timeout(get_int("web", "page_load_timeout", 30))
    logger.info("浏览器已启动 browser=%s 版本=%s", browser_name,
                browser.capabilities.get("browserVersion"))
    yield browser
    browser.quit()
    logger.info("浏览器已退出")


@pytest.fixture(scope="module")
def api() -> RequestUtil:
    """接口请求客户端（base_url 来自 config.ini）。"""
    return RequestUtil()


@pytest.fixture(scope="module")
def pet_api(api) -> PetApi:
    """Petstore 宠物业务接口对象。"""
    return PetApi(client=api)


@pytest.fixture(scope="module")
def created_pet_id(pet_api) -> int:
    """创建宠物并返回其 id，模块用例结束后自动清理，保证用例可重复运行。"""
    pet_id, resp = pet_api.create_pet(name="fixture_doggie")
    assert resp.status_code == 200, f"前置创建宠物失败: {resp.status_code} {resp.text[:200]}"
    logger.info("前置数据创建成功 pet_id=%s", pet_id)
    yield pet_id
    pet_api.delete_pet(pet_id)
    logger.info("前置数据已清理 pet_id=%s", pet_id)


# ---------------------------------------------------------------- hooks
def _attach_log_tail(max_lines: int = 300) -> None:
    """用例失败时，把日志尾部附加到 Allure 便于定位上下文。"""
    if not LOG_FILE.exists():
        return
    lines = LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()
    allure.attach("\n".join(lines[-max_lines:]),
                  name="运行日志(尾部)",
                  attachment_type=allure.attachment_type.TEXT)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """用例失败时自动收集：运行日志 + Web 页面截图 + 页面源码。"""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        try:
            _attach_log_tail()
        except Exception as exc:  # noqa: BLE001
            logger.warning("附加运行日志失败: %s", exc)
        driver = item.funcargs.get("driver")
        if driver is not None:
            try:
                allure.attach(driver.get_screenshot_as_png(),
                              name="失败页面截图",
                              attachment_type=allure.attachment_type.PNG)
            except Exception as exc:  # noqa: BLE001
                logger.warning("失败截图失败: %s", exc)
            try:
                allure.attach(driver.page_source,
                              name="失败页面源码",
                              attachment_type=allure.attachment_type.TEXT)
            except Exception as exc:  # noqa: BLE001
                logger.warning("抓取页面源码失败: %s", exc)
            try:
                entries = driver.get_log("browser")
                lines = [f"[{e.get('level')}] {e.get('message')}" for e in entries]
                if lines:
                    allure.attach("\n".join(lines[-100:]),
                                  name="浏览器Console日志",
                                  attachment_type=allure.attachment_type.TEXT)
            except Exception as exc:  # noqa: BLE001 部分驱动不支持取日志
                logger.warning("获取浏览器日志失败: %s", exc)
