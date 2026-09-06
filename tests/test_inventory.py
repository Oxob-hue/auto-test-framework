"""Web 用例：商品列表交互（排序正确性 / 多商品加购，SauceDemo）。"""
import allure
import pytest

from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage

pytestmark = [
    pytest.mark.web,
    allure.epic("Web 自动化"),
    allure.feature("商品列表交互"),
]


def _login(driver, base_url) -> InventoryPage:
    login_page = LoginPage(driver)
    login_page.open_url(base_url)
    login_page.login("standard_user", "secret_sauce")
    return InventoryPage(driver)


@allure.story("商品排序")
@allure.severity(allure.severity_level.NORMAL)
def test_sort_products_by_price_low_to_high(driver, base_url):
    """按价格从低到高排序后，页面展示的价格应为升序。"""
    with allure.step("登录并进入商品列表"):
        inventory_page = _login(driver, base_url)
    with allure.step("选择价格从低到高排序"):
        inventory_page.select_sort_option(InventoryPage.SORT_PRICE_LOW_TO_HIGH)
    with allure.step("断言价格列表升序"):
        prices = inventory_page.get_product_price_values()
        assert len(prices) >= 2, f"商品数量不足，无法校验排序: {prices}"
        assert prices == sorted(prices), f"价格未按升序展示: {prices}"


@allure.story("多商品加购")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.smoke
def test_add_two_items_to_cart(driver, base_url):
    """添加两件商品后：角标为 2，购物车内条目数为 2。"""
    with allure.step("登录并进入商品列表"):
        inventory_page = _login(driver, base_url)
    with allure.step("分别添加两件商品"):
        inventory_page.add_backpack_to_cart()
        inventory_page.add_bike_light_to_cart()
    with allure.step("断言购物车角标为 2"):
        assert inventory_page.get_cart_badge_count() == "2", "加购两件后角标应为 2"
    with allure.step("进入购物车断言条目数"):
        cart_page = inventory_page.go_to_cart()
        assert cart_page.get_cart_item_count() == 2, "购物车应有 2 件商品"
