"""Web 用例：购物车状态与操作（SauceDemo）。"""
import allure
import pytest

from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage

pytestmark = [
    pytest.mark.web,
    allure.epic("Web 自动化"),
    allure.feature("购物车"),
]


def _login(driver, base_url) -> InventoryPage:
    login_page = LoginPage(driver)
    login_page.open_url(base_url)
    login_page.login("standard_user", "secret_sauce")
    return InventoryPage(driver)


@allure.story("空购物车状态")
@allure.severity(allure.severity_level.NORMAL)
def test_empty_cart_state(driver, base_url):
    """未加购直接进入购物车：条目为 0 且无角标。"""
    with allure.step("登录后直接进入购物车"):
        inventory_page = _login(driver, base_url)
        cart_page = inventory_page.go_to_cart()
    with allure.step("断言购物车为空"):
        assert cart_page.get_cart_item_count() == 0, "空购物车不应有条目"
        assert cart_page.get_cart_badge_count() is None, "空购物车不应展示角标"


@allure.story("继续购物")
@allure.severity(allure.severity_level.NORMAL)
def test_continue_shopping_returns_to_inventory(driver, base_url):
    """Continue Shopping 应返回商品列表，且已加购商品保留。"""
    with allure.step("登录、加购并进入购物车"):
        inventory_page = _login(driver, base_url)
        inventory_page.add_backpack_to_cart()
        cart_page = inventory_page.go_to_cart()
    with allure.step("点击 Continue Shopping"):
        back_inventory = cart_page.continue_shopping()
    with allure.step("断言回到列表页且角标保留"):
        assert back_inventory.get_title_text() == "Products", "未返回商品列表页"
        assert back_inventory.get_cart_badge_count() == "1", "返回后加购状态应保留"


@allure.story("部分移除商品")
@allure.severity(allure.severity_level.NORMAL)
def test_remove_one_of_two_items(driver, base_url):
    """购物车中有两件商品时移除其中一件：剩余条目与名称应正确。"""
    with allure.step("加购两件商品并进入购物车"):
        inventory_page = _login(driver, base_url)
        inventory_page.add_backpack_to_cart()
        inventory_page.add_bike_light_to_cart()
        cart_page = inventory_page.go_to_cart()
        assert cart_page.get_cart_item_count() == 2

    with allure.step("移除背包"):
        cart_page.remove_backpack()

    with allure.step("断言仅剩单车灯"):
        assert cart_page.get_cart_item_count() == 1, "移除一件后应剩 1 件"
        assert cart_page.get_item_names() == ["Sauce Labs Bike Light"], \
            f"剩余商品不正确: {cart_page.get_item_names()}"
        assert cart_page.get_cart_badge_count() == "1", "角标应更新为 1"


@allure.story("移除最后一件商品")
@allure.severity(allure.severity_level.CRITICAL)
def test_badge_disappears_after_removing_last_item(driver, base_url):
    """移除最后一件商品后：购物车为空且角标消失。"""
    with allure.step("加购一件并进入购物车"):
        inventory_page = _login(driver, base_url)
        inventory_page.add_backpack_to_cart()
        cart_page = inventory_page.go_to_cart()

    with allure.step("移除唯一商品"):
        cart_page.remove_backpack()

    with allure.step("断言购物车为空且角标消失"):
        assert cart_page.get_cart_item_count() == 0, "购物车应为空"
        assert cart_page.get_cart_badge_count() is None, "角标应消失"


@allure.story("角标与购物车条目跨页面一致性")
@allure.severity(allure.severity_level.CRITICAL)
def test_badge_and_cart_items_consistent_for_three_products(driver, base_url):
    """业务一致性：加购 3 件后移除 1 件，角标数与购物车条目/商品名始终保持一致。"""
    with allure.step("登录并依次加购 3 件商品"):
        inventory_page = _login(driver, base_url)
        inventory_page.add_backpack_to_cart()
        inventory_page.add_bike_light_to_cart()
        inventory_page.add_bolt_tshirt_to_cart()
        assert inventory_page.get_cart_badge_count() == "3", "加购三件后角标应为 3"

    with allure.step("进入购物车校验条目与商品名"):
        cart_page = inventory_page.go_to_cart()
        assert cart_page.get_cart_item_count() == 3, "购物车应有 3 件商品"
        names = set(cart_page.get_item_names())
        assert names == {"Sauce Labs Backpack", "Sauce Labs Bike Light",
                         "Sauce Labs Bolt T-Shirt"}, f"购物车商品不正确: {names}"

    with allure.step("移除背包后角标与条目应同步为 2"):
        cart_page.remove_backpack()
        assert cart_page.get_cart_item_count() == 2, "移除一件后应剩 2 件"
        assert cart_page.get_cart_badge_count() == "2", "角标应更新为 2"
        assert "Sauce Labs Backpack" not in cart_page.get_item_names(), "背包应已被移除"
