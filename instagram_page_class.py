from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException

class Instagram(object):
    def __init__(self, address='https://www.instagram.com'):
        assert address
        self.__address = address
        self.__login_page = address + '/accounts/login/'
        self.__browser = self.open_browser_with_options()
        self.__browser.get(self.__login_page)



    @property
    def user_login_field(self):
        return self.find_by_name("username")

    @property
    def user_password_field(self):
        return self.find_by_name("password")

    @property
    def login_button(self):
        return self.find_by_name()

    def log_in(self, login, password):
        login_field = self.user_login_field
        password_field = self.user_password_field

        login_field.click()
        login_field.send_keys(login)

        password_field.click()
        password_field.send_keys(password)

        self.login_button.click()

    def find_by_name(self, element_name):
        return self.find_by(By.NAME, element_name)

    def find_by(self, type_, mask):
        try:
            element = WebDriverWait(self.__browser, self.__wait_in_secs).until(
                expected_conditions.visibility_of_element_located((type_, mask)))
        except TimeoutException:
            element = None
        finally:
            return element

    @staticmethod
    def open_browser_with_options():
        """
        opens Chrome browser with some special attributes
        :return: webdriver object
        """
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")  # This make Chromium reachable
        options.add_argument("--no-default-browser-check")  # Overrides default choices
        options.add_argument("--no-first-run")
        options.add_argument("--disable-default-apps")
        return webdriver.Chrome(chrome_options=options)