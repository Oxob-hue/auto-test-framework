"""SauceDemo 商品详情页对象。"""
from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class ProductDetailPage(BasePage):
    """商品详情页：名称、价格、描述与返回列表。"""

    NAME = (By.CLASS_NAME, "inventory_details_name")
    PRICE = (By.CLASS_NAME, "inventory_details_price")
    DESCRIPTION = (By.CLASS_NAME, "inventory_details_desc")
    BACK_BUTTON = (By.ID, "back-to-products")

    def get_name(self) -> str:
        return self.get_text(self.NAME)

    def get_price(self) -> str:
        return self.get_text(self.PRICE)

    def get_description(self) -> str:
        return self.get_text(self.DESCRIPTION)

    def is_description_visible(self) -> bool:
        return self.is_element_visible(self.DESCRIPTION, timeout=5)

    def back_to_products(self) -> "InventoryPage":
        """返回商品列表页。"""
        from pages.inventory_page import InventoryPage  # 局部导入避免循环依赖
        self.click_until(self.BACK_BUTTON,
                         "return location.pathname.includes('inventory')",
                         "返回商品列表页")
        return InventoryPage(self.driver)
