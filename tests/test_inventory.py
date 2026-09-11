"""Web 用例：商品列表交互（排序 / 详情页 / 列表页移除 / 多商品加购，SauceDemo）。"""
import allure
import pytest

from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage
from pages.product_detail_page import ProductDetailPage

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
@pytest.mark.parametrize("sort_value,kind", [
    (InventoryPage.SORT_NAME_ASC, "name_asc"),
    (InventoryPage.SORT_NAME_DESC, "name_desc"),
    (InventoryPage.SORT_PRICE_LOW_TO_HIGH, "price_asc"),
    (InventoryPage.SORT_PRICE_HIGH_TO_LOW, "price_desc"),
], ids=["name_asc", "name_desc", "price_asc", "price_desc"])
def test_sort_products(driver, base_url, sort_value, kind):
    """四种排序方式下，页面实际展示的名称/价格顺序都应符合预期。"""
    with allure.step("登录并进入商品列表"):
        inventory_page = _login(driver, base_url)
    with allure.step(f"选择排序方式 {sort_value}"):
        inventory_page.select_sort_option(sort_value)
    with allure.step("断言展示顺序正确"):
        if kind.startswith("name"):
            names = inventory_page.get_product_name_values()
            assert len(names) >= 2, f"商品数量不足: {names}"
            expected = sorted(names, reverse=(kind == "name_desc"))
            assert names == expected, f"名称排序不符({kind}): {names}"
        else:
            prices = inventory_page.get_product_price_values()
            assert len(prices) >= 2, f"商品数量不足: {prices}"
            expected = sorted(prices, reverse=(kind == "price_desc"))
            assert prices == expected, f"价格排序不符({kind}): {prices}"


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


@allure.story("商品详情页")
@allure.severity(allure.severity_level.NORMAL)
def test_product_detail_matches_list(driver, base_url):
    """从列表进入商品详情页：名称与价格应与列表展示一致，且可返回列表。"""
    with allure.step("登录并读取列表首个商品信息"):
        inventory_page = _login(driver, base_url)
        list_name = inventory_page.get_product_name_values()[0]
        list_price = inventory_page.driver.find_elements(
            *InventoryPage.PRODUCT_PRICES)[0].text

    with allure.step(f"点击商品进入详情页: {list_name}"):
        detail_page: ProductDetailPage = inventory_page.open_product_detail(list_name)

    with allure.step("断言详情页名称/价格与列表一致"):
        assert detail_page.get_name() == list_name, "详情页名称与列表不一致"
        assert detail_page.get_price() == list_price, "详情页价格与列表不一致"
        assert detail_page.is_description_visible(), "详情页描述未展示"

    with allure.step("返回商品列表页"):
        back_page = detail_page.back_to_products()
        assert back_page.get_title_text() == "Products", "返回后未回到商品列表页"


@allure.story("列表页移除商品")
@allure.severity(allure.severity_level.NORMAL)
def test_remove_item_from_inventory_list(driver, base_url):
    """在商品列表页直接移除已加购商品：按钮恢复为 Add to cart 且角标消失。"""
    with allure.step("登录并加购背包"):
        inventory_page = _login(driver, base_url)
        inventory_page.add_backpack_to_cart()
        assert inventory_page.get_cart_badge_count() == "1"

    with allure.step("在列表页点击 Remove"):
        inventory_page.remove_backpack_from_list()

    with allure.step("断言角标消失"):
        assert inventory_page.get_cart_badge_count() is None, "移除后角标应消失"
