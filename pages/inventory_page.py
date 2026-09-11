"""SauceDemo 商品列表页对象。"""
from typing import List, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from pages.base_page import BasePage
from pages.cart_page import CartPage
from pages.login_page import LoginPage


class InventoryPage(BasePage):
    """商品列表（Products）页：标题、加购、排序、商品详情、菜单退出、购物车入口。"""

    TITLE = (By.CLASS_NAME, "title")
    ADD_TO_CART_BUTTON = (By.ID, "add-to-cart-sauce-labs-backpack")
    ADD_BIKE_LIGHT_BUTTON = (By.ID, "add-to-cart-sauce-labs-bike-light")
    REMOVE_BACKPACK_BUTTON = (By.ID, "remove-sauce-labs-backpack")
    CART_BADGE = (By.CLASS_NAME, "shopping_cart_badge")
    CART_LINK = (By.CLASS_NAME, "shopping_cart_link")
    SORT_SELECT = (By.CLASS_NAME, "product_sort_container")
    PRODUCT_PRICES = (By.CLASS_NAME, "inventory_item_price")
    PRODUCT_NAMES = (By.CLASS_NAME, "inventory_item_name")
    MENU_BUTTON = (By.ID, "react-burger-menu-btn")
    LOGOUT_LINK = (By.ID, "logout_sidebar_link")

    # 排序选项 value：az 名称升序 / za 名称降序 / lohi 价格升序 / hilo 价格降序
    SORT_NAME_ASC = "az"
    SORT_NAME_DESC = "za"
    SORT_PRICE_LOW_TO_HIGH = "lohi"
    SORT_PRICE_HIGH_TO_LOW = "hilo"

    # React 提交加购后，add 按钮会替换为 remove 按钮（id 形如 remove-<商品>）
    _REMOVE_BACKPACK_JS = "return !!document.querySelector('#remove-sauce-labs-backpack')"
    _REMOVE_BIKE_LIGHT_JS = "return !!document.querySelector('#remove-sauce-labs-bike-light')"
    _ADD_BACKPACK_JS = "return !!document.querySelector('#add-to-cart-sauce-labs-backpack')"

    def get_title_text(self) -> str:
        return self.get_text(self.TITLE)

    def add_backpack_to_cart(self) -> None:
        """把“Sauce Labs Backpack”加入购物车，并等待 React 状态提交完成。"""
        self.click_until(self.ADD_TO_CART_BUTTON, self._REMOVE_BACKPACK_JS, "加购后出现移除按钮")

    def add_bike_light_to_cart(self) -> None:
        """把“Sauce Labs Bike Light”加入购物车，并等待 React 状态提交完成。"""
        self.click_until(self.ADD_BIKE_LIGHT_BUTTON, self._REMOVE_BIKE_LIGHT_JS, "加购后出现移除按钮")

    def remove_backpack_from_list(self) -> None:
        """在商品列表页直接移除背包（按钮重新变回 Add to cart）。"""
        self.click_until(self.REMOVE_BACKPACK_BUTTON, self._ADD_BACKPACK_JS, "列表页移除背包")

    def get_cart_badge_count(self) -> Optional[str]:
        """购物车角标数量；尚未加购（角标不存在）时返回 None。"""
        badges = self.find_elements(self.CART_BADGE)
        return badges[0].text if badges else None

    def select_sort_option(self, value: str) -> None:
        """按 value 选择商品排序方式（az/za/lohi/hilo）。"""
        Select(self.find_element(self.SORT_SELECT)).select_by_value(value)

    def get_product_price_values(self) -> List[float]:
        """返回当前列表全部商品的价格（数字列表），用于排序正确性断言。"""
        prices = []
        for element in self.find_elements(self.PRODUCT_PRICES):
            prices.append(float(element.text.replace("$", "").strip()))
        return prices

    def get_product_name_values(self) -> List[str]:
        """返回当前列表全部商品的名称（按展示顺序）。"""
        return [element.text for element in self.find_elements(self.PRODUCT_NAMES)]

    def open_product_detail(self, product_name: str) -> "ProductDetailPage":
        """点击商品名称进入详情页并返回详情页对象。"""
        from pages.product_detail_page import ProductDetailPage  # 局部导入避免循环依赖
        self.click_until((By.LINK_TEXT, product_name),
                         "return location.pathname.includes('inventory-item')",
                         f"进入商品详情页: {product_name}")
        return ProductDetailPage(self.driver)

    def logout(self) -> LoginPage:
        """通过左侧菜单退出登录，返回登录页对象。"""
        self.click_until(self.MENU_BUTTON,
                         "return !!document.querySelector('#logout_sidebar_link')",
                         "展开侧边菜单")
        self.click_until(self.LOGOUT_LINK,
                         "return !location.pathname.includes('inventory') && "
                         "!location.pathname.includes('cart')",
                         "退出登录回到登录页")
        return LoginPage(self.driver)

    def go_to_cart(self) -> CartPage:
        """点击购物车入口跳转购物车页（等待跳转完成，防 React 丢点击）。"""
        self.click_until(self.CART_LINK,
                         "return location.pathname.includes('/cart')",
                         "跳转购物车页")
        return CartPage(self.driver)
