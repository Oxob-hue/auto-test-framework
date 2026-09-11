"""SauceDemo 购物车页对象。"""
from typing import List, Optional

from selenium.webdriver.common.by import By

from pages.base_page import BasePage
from pages.checkout_page import CheckoutPage


class CartPage(BasePage):
    """购物车页：商品数量/名称校验、移除商品、继续购物、进入结算。"""

    CART_ITEM = (By.CLASS_NAME, "cart_item")
    ITEM_QUANTITY = (By.CLASS_NAME, "cart_quantity")
    ITEM_NAMES = (By.CLASS_NAME, "inventory_item_name")
    CART_BADGE = (By.CLASS_NAME, "shopping_cart_badge")
    REMOVE_BACKPACK_BUTTON = (By.ID, "remove-sauce-labs-backpack")
    REMOVE_BIKE_LIGHT_BUTTON = (By.ID, "remove-sauce-labs-bike-light")
    CONTINUE_SHOPPING_BUTTON = (By.ID, "continue-shopping")
    CHECKOUT_BUTTON = (By.ID, "checkout")

    def get_cart_item_count(self) -> int:
        """购物车内的商品条目数。"""
        return len(self.find_elements(self.CART_ITEM))

    def get_first_item_quantity(self) -> str:
        """第一件商品的数量。"""
        return self.get_text(self.ITEM_QUANTITY)

    def get_item_names(self) -> List[str]:
        """购物车内商品名称列表（按展示顺序）。"""
        return [element.text for element in self.find_elements(self.ITEM_NAMES)]

    def get_cart_badge_count(self) -> Optional[str]:
        """购物车角标数量；无角标（购物车为空）时返回 None。"""
        badges = self.find_elements(self.CART_BADGE)
        return badges[0].text if badges else None

    def remove_backpack(self) -> None:
        """移除背包商品，并等待 React 状态提交（该行移除按钮从 DOM 消失）。"""
        self.click_until(self.REMOVE_BACKPACK_BUTTON,
                         "return !document.querySelector('#remove-sauce-labs-backpack')",
                         "移除背包后按钮消失")

    def remove_bike_light(self) -> None:
        """移除单车灯商品，并等待 React 状态提交。"""
        self.click_until(self.REMOVE_BIKE_LIGHT_BUTTON,
                         "return !document.querySelector('#remove-sauce-labs-bike-light')",
                         "移除单车灯后按钮消失")

    def continue_shopping(self) -> "InventoryPage":
        """点击 Continue Shopping 返回商品列表页。"""
        from pages.inventory_page import InventoryPage  # 局部导入避免循环依赖
        self.click_until(self.CONTINUE_SHOPPING_BUTTON,
                         "return location.pathname.includes('inventory')",
                         "返回商品列表页")
        return InventoryPage(self.driver)

    def click_checkout(self) -> CheckoutPage:
        """点击 Checkout 进入结算信息填写页（等待跳转完成，防 React 丢点击）。"""
        self.click_until(self.CHECKOUT_BUTTON,
                         "return location.pathname.includes('checkout-step-one')",
                         "跳转结算信息页")
        return CheckoutPage(self.driver)
