"""被测系统缺陷探测脚本（不参与自动化回归，仅供人工复核/文档取证）。

背景：SauceDemo 提供 standard_user / problem_user 等账号，其中 problem_user
被官方定义为“存在 bug 的用户”。本脚本用真实浏览器观察差异行为，
用于产出 docs/缺陷复现演示.md 中的「预期 vs 实际」对照（确保文档事实可复现、不编造）。

运行（自动按 config.ini 启动浏览器；可用环境变量切换无头/浏览器）：
    python scripts/defect_probe.py
"""
import json
import sys
from pathlib import Path

# 支持直接执行：python scripts/defect_probe.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService

from common.config_util import get_bool, get_config
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage


def _new_browser():
    """按 config.ini + 环境变量创建一个浏览器会话（与 tests/conftest.py 同策略）。"""
    browser_name = get_config("web", "browser", "edge").strip().lower()
    headless = get_bool("web", "headless", False)
    options = EdgeOptions() if browser_name == "edge" else ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    if sys.platform.startswith("linux"):
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
    if browser_name == "chrome":
        browser = webdriver.Chrome(options=options)          # Selenium Manager 自动配驱动
    else:
        browser = webdriver.Edge(service=EdgeService(get_config("web", "driver_path")),
                                 options=options)
    browser.implicitly_wait(10)
    return browser


def _inspect(username: str) -> dict:
    browser = _new_browser()
    try:
        login_page = LoginPage(browser)
        login_page.open_url(get_config("web", "base_url"))
        login_page.login(username, "secret_sauce")

        inventory = InventoryPage(browser)
        img_srcs = [
            img.get_attribute("src") or ""
            for img in inventory.driver.find_elements(By.CSS_SELECTOR, "img.inventory_item_img")
        ]
        name_els = inventory.driver.find_elements(By.CLASS_NAME, "inventory_item_name")
        first_name_before = name_els[0].text if name_els else ""

        inventory.select_sort_option("za")                   # 名称降序
        names_after_za = [e.text for e in
                          inventory.driver.find_elements(By.CLASS_NAME, "inventory_item_name")]

        inventory.select_sort_option(InventoryPage.SORT_PRICE_LOW_TO_HIGH)  # 价格升序
        prices = inventory.get_product_price_values()

        return {
            "user": username,
            "product_count": len(img_srcs),
            "distinct_image_count": len(set(img_srcs)),
            "image_sample": img_srcs[:2],
            "first_name_before_sort": first_name_before,
            "first_name_after_za": names_after_za[0] if names_after_za else None,
            "za_reordered": names_after_za[:1] != [first_name_before],
            "prices_sample_after_lohi": prices[:5],
            "lohi_sorted_asc": prices == sorted(prices),
        }
    finally:
        browser.quit()


def main() -> int:
    results = [_inspect("standard_user"), _inspect("problem_user")]
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
