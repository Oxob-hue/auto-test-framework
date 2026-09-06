"""SauceDemo 商品列表页对象。"""
from typing import List, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from pages.base_page import BasePage
from pages.cart_page import CartPage


class InventoryPage(BasePage):
    """商品列表（Products）页：标题、加购、排序、购物车角标与购物车入口。"""

    TITLE = (By.CLASS_NAME, "title")
    ADD_TO_CART_BUTTON = (By.ID, "add-to-cart-sauce-labs-backpack")
    ADD_BIKE_LIGHT_BUTTON = (By.ID, "add-to-cart-sauce-labs-bike-light")
    CART_BADGE = (By.CLASS_NAME, "shopping_cart_badge")
    CART_LINK = (By.CLASS_NAME, "shopping_cart_link")
    SORT_SELECT = (By.CLASS_NAME, "product_sort_container")
    PRODUCT_PRICES = (By.CLASS_NAME, "inventory_item_price")

    # 排序选项 value：az 名称升序 / za 名称降序 / lohi 价格升序 / hilo 价格降序
    SORT_PRICE_LOW_TO_HIGH = "lohi"
    SORT_PRICE_HIGH_TO_LOW = "hilo"

    # React 提交加购后，add 按钮会替换为 remove 按钮（id 形如 remove-<商品>）
    _REMOVE_BACKPACK_JS = "return !!document.querySelector('#remove-sauce-labs-backpack')"
    _REMOVE_BIKE_LIGHT_JS = "return !!document.querySelector('#remove-sauce-labs-bike-light')"

    def get_title_text(self) -> str:
        return self.get_text(self.TITLE)

    def add_backpack_to_cart(self) -> None:
        """把“Sauce Labs Backpack”加入购物车，并等待 React 状态提交完成。"""
        self.click_until(self.ADD_TO_CART_BUTTON, self._REMOVE_BACKPACK_JS, "加购后出现移除按钮")

    def add_bike_light_to_cart(self) -> None:
        """把“Sauce Labs Bike Light”加入购物车，并等待 React 状态提交完成。"""
        self.click_until(self.ADD_BIKE_LIGHT_BUTTON, self._REMOVE_BIKE_LIGHT_JS, "加购后出现移除按钮")

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

    def go_to_cart(self) -> CartPage:
        """点击购物车入口跳转购物车页（等待跳转完成，防 React 丢点击）。"""
        self.click_until(self.CART_LINK,
                         "return location.pathname.includes('/cart')",
                         "跳转购物车页")
        return CartPage(self.driver)
