"""Web 端到端用例：完整下单流程（SauceDemo）。

覆盖：登录 → 添加商品 → 进入购物车 → 填写收货信息 → 订单总览 → 下单完成，
是面试中最能体现“全流程业务理解 + 页面对象封装”的核心用例。
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


@allure.story("下单表单校验异常")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.negative
def test_checkout_requires_postal_code(driver, base_url):
    """反向：收货信息缺少邮编时，点击 Continue 应被拦截并提示。"""
    with allure.step("登录、加购并进入结算页"):
        login_page = LoginPage(driver)
        login_page.open_url(base_url)
        login_page.login("standard_user", "secret_sauce")

        inventory_page = InventoryPage(driver)
        inventory_page.add_backpack_to_cart()
        cart_page = inventory_page.go_to_cart()
        checkout_page = cart_page.click_checkout()

    with allure.step("填写姓名但留空邮编并继续"):
        checkout_page.fill_customer_info("San", "Zhang", "")
        checkout_page.continue_to_overview()

    with allure.step("断言停留在填写页并提示邮编必填"):
        assert "Postal Code is required" in checkout_page.get_error_message(), \
            "未出现邮编必填的错误提示"
        assert "checkout-step-one" in checkout_page.get_current_url(), \
            "缺少邮编时不应进入订单总览页"
