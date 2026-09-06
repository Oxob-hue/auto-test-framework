"""SauceDemo 购物车页对象。"""
from selenium.webdriver.common.by import By

from pages.base_page import BasePage
from pages.checkout_page import CheckoutPage


class CartPage(BasePage):
    """购物车页：商品数量校验、移除商品、进入结算。"""

    CART_ITEM = (By.CLASS_NAME, "cart_item")
    ITEM_QUANTITY = (By.CLASS_NAME, "cart_quantity")
    REMOVE_BACKPACK_BUTTON = (By.ID, "remove-sauce-labs-backpack")
    CONTINUE_SHOPPING_BUTTON = (By.ID, "continue-shopping")
    CHECKOUT_BUTTON = (By.ID, "checkout")

    def get_cart_item_count(self) -> int:
        """购物车内的商品条目数。"""
        return len(self.find_elements(self.CART_ITEM))

    def get_first_item_quantity(self) -> str:
        """第一件商品的数量。"""
        return self.get_text(self.ITEM_QUANTITY)

    def remove_backpack(self) -> None:
        """移除背包商品。"""
        self.click(self.REMOVE_BACKPACK_BUTTON)

    def continue_shopping(self) -> None:
        """返回商品列表继续购物。"""
        self.click(self.CONTINUE_SHOPPING_BUTTON)

    def click_checkout(self) -> CheckoutPage:
        """点击 Checkout 进入结算信息填写页。"""
        self.click(self.CHECKOUT_BUTTON)
        return CheckoutPage(self.driver)
