"""SauceDemo 结算页对象。

覆盖下单流程中的三个连续页面：
  checkout-step-one（填写收货信息） → checkout-step-two（订单总览） → checkout-complete（下单完成）
因三个页面由同一个页面对象按步骤推进即可完成，故合并封装为 CheckoutPage。
"""
import re

from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class CheckoutPage(BasePage):
    """结算相关页面：填写信息、查看金额、确认订单、取消订单、完成下单。"""

    FIRST_NAME_INPUT = (By.ID, "first-name")
    LAST_NAME_INPUT = (By.ID, "last-name")
    POSTAL_CODE_INPUT = (By.ID, "postal-code")
    CONTINUE_BUTTON = (By.ID, "continue")
    CANCEL_BUTTON = (By.ID, "cancel")
    FINISH_BUTTON = (By.ID, "finish")
    COMPLETE_HEADER = (By.CLASS_NAME, "complete-header")
    # 错误提示容器（不限标签，兼容 h3/div 渲染差异）
    ERROR_MESSAGE = (By.CSS_SELECTOR, "[data-test='error']")
    # 订单总览页金额
    ITEM_TOTAL = (By.CLASS_NAME, "summary_subtotal_label")
    TAX = (By.CLASS_NAME, "summary_tax_label")
    TOTAL = (By.CLASS_NAME, "summary_total_label")

    def fill_customer_info(self, first_name: str, last_name: str, postal_code: str) -> None:
        """填写收货人姓名与邮编。"""
        self.input_text(self.FIRST_NAME_INPUT, first_name)
        self.input_text(self.LAST_NAME_INPUT, last_name)
        self.input_text(self.POSTAL_CODE_INPUT, postal_code)

    def submit_form(self) -> None:
        """点击 Continue 提交表单（不等待跳转），用于表单校验失败场景：
        期望页面停留并展示错误提示。"""
        self.click(self.CONTINUE_BUTTON)

    def continue_to_overview(self) -> None:
        """正向流程：信息填写页 → 订单总览页（等待跳转完成）。"""
        self.click_until(self.CONTINUE_BUTTON,
                         "return location.pathname.includes('checkout-step-two')",
                         "跳转订单总览页")

    def finish_order(self) -> None:
        """订单总览页 → 点击 Finish 完成下单（等待跳转完成）。"""
        self.click_until(self.FINISH_BUTTON,
                         "return location.pathname.includes('checkout-complete')",
                         "跳转下单完成页")

    def cancel_order(self) -> "CartPage":
        """信息填写页 → 点击 Cancel 返回购物车页。"""
        from pages.cart_page import CartPage  # 局部导入避免循环依赖
        self.click_until(self.CANCEL_BUTTON,
                         "return location.pathname.includes('/cart')",
                         "取消下单返回购物车")
        return CartPage(self.driver)

    def get_complete_header(self) -> str:
        """下单成功后的提示文案。"""
        return self.get_text(self.COMPLETE_HEADER)

    def get_error_message(self) -> str:
        """表单校验失败时的错误提示。"""
        return self.get_text(self.ERROR_MESSAGE)

    def try_get_error_message(self, timeout: float = 3.0):
        """获取错误提示；提示未渲染（存在浏览器渲染差异）时返回 None，不抛异常。"""
        if self.is_element_visible(self.ERROR_MESSAGE, timeout=timeout):
            return self.get_text(self.ERROR_MESSAGE)
        return None

    # ---------------- 订单金额 ----------------
    @staticmethod
    def _parse_amount(text: str) -> float:
        """从 'Item total: $29.99' 之类的文案中解析金额。"""
        match = re.search(r"\$([\d.]+)", text)
        assert match, f"未能从文案解析金额: {text!r}"
        return float(match.group(1))

    def get_item_total(self) -> float:
        return self._parse_amount(self.get_text(self.ITEM_TOTAL))

    def get_tax(self) -> float:
        return self._parse_amount(self.get_text(self.TAX))

    def get_total(self) -> float:
        return self._parse_amount(self.get_text(self.TOTAL))
