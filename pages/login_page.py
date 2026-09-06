"""SauceDemo 登录页对象。"""
from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class LoginPage(BasePage):
    """登录页：用户名 / 密码输入、登录操作与错误提示读取。"""

    USERNAME_INPUT = (By.ID, "user-name")
    PASSWORD_INPUT = (By.NAME, "password")
    LOGIN_BUTTON = (By.ID, "login-button")
    ERROR_MESSAGE = (By.CSS_SELECTOR, "h3[data-test='error']")

    def enter_username(self, username: str) -> None:
        self.input_text(self.USERNAME_INPUT, username)

    def enter_password(self, password: str) -> None:
        self.input_text(self.PASSWORD_INPUT, password)

    def click_login(self) -> None:
        self.click(self.LOGIN_BUTTON)

    def login(self, username: str, password: str) -> None:
        """完整登录操作，供用例直接调用。"""
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()

    def get_error_message(self) -> str:
        return self.get_text(self.ERROR_MESSAGE)
