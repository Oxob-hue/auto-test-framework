"""SauceDemo 结算页对象。

覆盖下单流程中的三个连续页面：
  checkout-step-one（填写收货信息） → checkout-step-two（订单总览） → checkout-complete（下单完成）
因三个页面由同一个页面对象按步骤推进即可完成，故合并封装为 CheckoutPage。
"""
from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class CheckoutPage(BasePage):
    """结算相关页面：填写信息、确认订单、完成下单。"""

    FIRST_NAME_INPUT = (By.ID, "first-name")
    LAST_NAME_INPUT = (By.ID, "last-name")
    POSTAL_CODE_INPUT = (By.ID, "postal-code")
    CONTINUE_BUTTON = (By.ID, "continue")
    FINISH_BUTTON = (By.ID, "finish")
    COMPLETE_HEADER = (By.CLASS_NAME, "complete-header")
    ERROR_MESSAGE = (By.CSS_SELECTOR, "h3[data-test='error']")

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

    def get_complete_header(self) -> str:
        """下单成功后的提示文案。"""
        return self.get_text(self.COMPLETE_HEADER)

    def get_error_message(self) -> str:
        """表单校验失败时的错误提示。"""
        return self.get_text(self.ERROR_MESSAGE)
