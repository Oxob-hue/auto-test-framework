"""Web 用例：登录（正向/反向）+ 购物车主流程（SauceDemo）。"""
import allure
import pytest

from pages.cart_page import CartPage
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage

pytestmark = [
    pytest.mark.web,
    allure.epic("Web 自动化"),
    allure.feature("登录与购物车"),
]


@allure.story("正向登录")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.smoke
@pytest.mark.parametrize("username,password", [
    ("standard_user", "secret_sauce"),
    ("problem_user", "secret_sauce"),
], ids=["standard_user", "problem_user"])
def test_login_success(driver, base_url, username, password):
    """正确账号密码应登录成功并进入商品列表页。"""
    with allure.step("打开登录页"):
        login_page = LoginPage(driver)
        login_page.open_url(base_url)
    with allure.step(f"使用账号 {username} 登录"):
        login_page.login(username, password)
    with allure.step("断言已进入商品列表页"):
        inventory_page = InventoryPage(driver)
        assert inventory_page.get_title_text() == "Products", "登录后应展示商品列表标题 Products"


@allure.story("登录异常场景")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.negative
@pytest.mark.parametrize("username,password,expected_msg", [
    ("locked_out_user", "secret_sauce", "Epic sadface: Sorry, this user has been locked out."),
    ("standard_user", "wrong_password", "Epic sadface: Username and password do not match any user in this service"),
    ("standard_user", "", "Epic sadface: Password is required"),
    ("", "", "Epic sadface: Username is required"),
], ids=["locked_out", "wrong_password", "empty_password", "empty_username"])
def test_login_failed(driver, base_url, username, password, expected_msg):
    """非法输入（锁定账号/错误密码/空输入）应被拦截并给出错误提示。"""
    with allure.step("打开登录页并提交登录"):
        login_page = LoginPage(driver)
        login_page.open_url(base_url)
        login_page.login(username, password)
    with allure.step("断言页面出现预期错误提示"):
        assert expected_msg in login_page.get_error_message()


@allure.story("购物车主流程")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.smoke
def test_add_to_cart_then_remove(driver, base_url):
    """登录 → 加购（角标校验）→ 购物车（数量校验）→ 移除商品。"""
    with allure.step("登录"):
        login_page = LoginPage(driver)
        login_page.open_url(base_url)
        login_page.login("standard_user", "secret_sauce")

    with allure.step("添加背包并校验购物车角标"):
        inventory_page = InventoryPage(driver)
        inventory_page.add_backpack_to_cart()
        assert inventory_page.get_cart_badge_count() == "1", "加购后购物车角标应为 1"

    with allure.step("进入购物车并校验商品条目"):
        cart_page: CartPage = inventory_page.go_to_cart()
        assert cart_page.get_cart_item_count() == 1, "购物车中应有 1 件商品"
        assert cart_page.get_first_item_quantity() == "1", "商品数量应为 1"

    with allure.step("移除商品后数量归零"):
        cart_page.remove_backpack()
        assert cart_page.get_cart_item_count() == 0, "移除后购物车应为空"
