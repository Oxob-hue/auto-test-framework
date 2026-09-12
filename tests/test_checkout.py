"""Web 用例：下单流程与结算校验（SauceDemo）。

覆盖：完整下单 E2E、订单金额计算、取消下单、表单必填校验（三种缺失场景）。
"""
import allure
import pytest

from pages.cart_page import CartPage
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage

pytestmark = [
    pytest.mark.web,
    allure.epic("Web 自动化"),
    allure.feature("下单全流程"),
]

BACKPACK_PRICE = 29.99


def _goto_checkout_step_one(driver, base_url):
    """公共前置：登录 → 加购背包 → 进入购物车 → 进入结算信息页。"""
    login_page = LoginPage(driver)
    login_page.open_url(base_url)
    login_page.login("standard_user", "secret_sauce")

    inventory_page = InventoryPage(driver)
    inventory_page.add_backpack_to_cart()
    cart_page = inventory_page.go_to_cart()
    return cart_page.click_checkout()


@allure.story("下单成功主流程")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.smoke
def test_checkout_happy_path(driver, base_url):
    """端到端验证一次完整购买成功。"""
    with allure.step("登录系统"):
        login_page = LoginPage(driver)
        login_page.open_url(base_url)
        login_page.login("standard_user", "secret_sauce")

    with allure.step("添加商品并进入购物车"):
        inventory_page = InventoryPage(driver)
        inventory_page.add_backpack_to_cart()
        assert inventory_page.get_cart_badge_count() == "1", "加购后角标应为 1"
        cart_page: CartPage = inventory_page.go_to_cart()
        assert cart_page.get_cart_item_count() == 1, "购物车应有 1 件商品"

    with allure.step("点击 Checkout 并填写收货信息"):
        checkout_page = cart_page.click_checkout()
        checkout_page.fill_customer_info("San", "Zhang", "100000")
        checkout_page.continue_to_overview()

    with allure.step("在订单总览页点击 Finish 完成下单"):
        checkout_page.finish_order()

    with allure.step("断言下单成功提示"):
        assert checkout_page.get_complete_header() == "Thank you for your order!", \
            "未出现下单成功提示"


@allure.story("订单金额计算")
@allure.severity(allure.severity_level.CRITICAL)
def test_checkout_totals_calculation(driver, base_url):
    """订单总览页金额应满足：商品小计正确、税费>0、总计 = 小计 + 税费。"""
    with allure.step("进入结算信息页并填写收货信息"):
        checkout_page = _goto_checkout_step_one(driver, base_url)
        checkout_page.fill_customer_info("San", "Zhang", "100000")
        checkout_page.continue_to_overview()

    with allure.step("读取订单总览金额"):
        item_total = checkout_page.get_item_total()
        tax = checkout_page.get_tax()
        total = checkout_page.get_total()

    with allure.step("断言金额计算正确"):
        assert abs(item_total - BACKPACK_PRICE) < 0.01, \
            f"商品小计应为 {BACKPACK_PRICE}，实际 {item_total}"
        assert tax > 0, f"税费应大于 0，实际 {tax}"
        assert abs(total - (item_total + tax)) < 0.01, \
            f"总计({total}) 应等于 小计({item_total}) + 税费({tax})"


@allure.story("取消下单")
@allure.severity(allure.severity_level.NORMAL)
def test_cancel_checkout_returns_to_cart(driver, base_url):
    """在结算信息页点击 Cancel：返回购物车且已加购商品仍在。"""
    with allure.step("进入结算信息页"):
        checkout_page = _goto_checkout_step_one(driver, base_url)

    with allure.step("点击 Cancel 取消下单"):
        cart_page = checkout_page.cancel_order()

    with allure.step("断言回到购物车且商品保留"):
        assert cart_page.get_cart_item_count() == 1, "取消后购物车商品应保留"
        assert cart_page.get_item_names() == ["Sauce Labs Backpack"], \
            f"购物车商品不正确: {cart_page.get_item_names()}"


@allure.story("下单表单必填校验")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.negative
@pytest.mark.parametrize("first_name,last_name,postal_code,expected_msg", [
    ("", "Zhang", "100000", "First Name is required"),
    ("San", "", "100000", "Last Name is required"),
    ("San", "Zhang", "", "Postal Code is required"),
], ids=["missing_first_name", "missing_last_name", "missing_postal_code"])
def test_checkout_required_fields(driver, base_url,
                                  first_name, last_name, postal_code, expected_msg):
    """反向：姓名/邮编任一必填项缺失时应被拦截，停留在结算信息页。"""
    with allure.step("进入结算信息页"):
        checkout_page = _goto_checkout_step_one(driver, base_url)

    with allure.step("填写不完整信息并提交"):
        checkout_page.fill_customer_info(first_name, last_name, postal_code)
        checkout_page.submit_form()

    with allure.step("断言校验拦截（未进入订单总览页）"):
        assert "checkout-step-one" in checkout_page.get_current_url(), \
            f"缺失必填项({expected_msg})时不应进入订单总览页"
        error_msg = checkout_page.try_get_error_message()
        if error_msg:
            assert expected_msg in error_msg, f"错误提示内容不符: {error_msg!r}"


@allure.story("跨页面金额一致性")
@allure.severity(allure.severity_level.CRITICAL)
def test_two_items_totals_match_inventory_prices(driver, base_url):
    """业务一致性：结算页的小计应等于商品列表页读取到的两件商品价格之和。"""
    with allure.step("登录并从商品列表读取两件商品价格"):
        login_page = LoginPage(driver)
        login_page.open_url(base_url)
        login_page.login("standard_user", "secret_sauce")
        inventory_page = InventoryPage(driver)
        price_map = inventory_page.get_product_price_map()
        assert len(price_map) >= 2, f"商品价格读取失败: {price_map}"
        expected_total = price_map["Sauce Labs Backpack"] + price_map["Sauce Labs Bike Light"]

    with allure.step("加购两件商品并进入结算页"):
        inventory_page.add_backpack_to_cart()
        inventory_page.add_bike_light_to_cart()
        assert inventory_page.get_cart_badge_count() == "2", "加购两件后角标应为 2"
        cart_page = inventory_page.go_to_cart()
        assert cart_page.get_cart_item_count() == 2, "购物车应有 2 件商品"
        checkout_page = cart_page.click_checkout()

    with allure.step("填写信息并读取订单总览金额"):
        checkout_page.fill_customer_info("San", "Zhang", "100000")
        checkout_page.continue_to_overview()
        item_total = checkout_page.get_item_total()
        tax = checkout_page.get_tax()
        total = checkout_page.get_total()

    with allure.step("断言小计与列表价格一致、总计 = 小计 + 税费"):
        assert abs(item_total - expected_total) < 0.01, \
            f"结算小计({item_total}) 与列表价格之和({expected_total:.2f}) 不一致"
        assert abs(total - (item_total + tax)) < 0.01, \
            f"总计({total}) 应等于 小计({item_total}) + 税费({tax})"
