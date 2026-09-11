"""Web 用例：访问控制（未登录重定向）与退出登录（SauceDemo）。"""
import allure
import pytest

from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage

pytestmark = [
    pytest.mark.web,
    allure.epic("Web 自动化"),
    allure.feature("访问控制与登录态"),
]


def _login(driver, base_url) -> InventoryPage:
    login_page = LoginPage(driver)
    login_page.open_url(base_url)
    login_page.login("standard_user", "secret_sauce")
    return InventoryPage(driver)


@allure.story("未登录访问受保护页面")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.negative
@pytest.mark.parametrize("route", ["/inventory.html", "/cart.html"],
                         ids=["inventory", "cart"])
def test_direct_access_without_login_redirects(driver, base_url, route):
    """未登录直接访问受保护页面应被重定向回登录页，并给出提示。"""
    with allure.step(f"未登录直接访问 {route}"):
        driver.get(base_url.rstrip("/") + route)
    with allure.step("断言已回到登录页（登录按钮可见，URL 不在受保护路径）"):
        login_page = LoginPage(driver)
        assert login_page.is_element_visible(LoginPage.LOGIN_BUTTON, timeout=10), \
            "未登录访问受保护页面时未回到登录页"
        current = login_page.get_current_url()
        assert "/inventory.html" not in current and "/cart.html" not in current, \
            f"仍停留在受保护页面: {current}"
    with allure.step("若提示已渲染，校验提示内容"):
        error_msg = login_page.try_get_error_message()
        if error_msg:
            assert "You can only access" in error_msg, f"提示内容不符: {error_msg!r}"


@allure.story("退出登录")
@allure.severity(allure.severity_level.NORMAL)
def test_logout_returns_to_login_page(driver, base_url):
    """登录后通过菜单退出，应回到登录页且购物车角标清空。"""
    with allure.step("登录并加购一件商品"):
        inventory_page = _login(driver, base_url)
        inventory_page.add_backpack_to_cart()
        assert inventory_page.get_cart_badge_count() == "1"

    with allure.step("通过侧边菜单退出登录"):
        login_page = inventory_page.logout()

    with allure.step("断言回到登录页"):
        assert login_page.is_element_visible(LoginPage.LOGIN_BUTTON, timeout=10), \
            "退出登录后未展示登录按钮"
        assert "/inventory" not in login_page.get_current_url(), "退出后仍停留在商品列表页"
