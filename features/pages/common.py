from abc import ABC

import pypom
from selenium.webdriver.common.by import By

from features.fields.fields import InputField, SubmitField


class AjaxModal(pypom.Page, ABC):
    def loaded(self):
        return self.find_element(By.ID, "form-modal-ajax-content")


class SuccessMessageRegion(pypom.Region):
    _root_locator = (By.ID, 'pnl_succes_messages')

    def loaded(self):
        return self.root.is_displayed()

    @property
    def text(self):
        return self.root.text


class CommonPageMixin:
    @property
    def success_messages(self):
        region = SuccessMessageRegion(self)
        region.wait_for_region_to_load()
        return region


class LoginPage(pypom.Page):
    URL_TEMPLATE = '/login/'

    username = InputField(By.ID, 'id_username')
    password = InputField(By.ID, 'id_password')
    submit = SubmitField(By.ID, 'post_login_btn')

    def login(self, username, password='password123'):
        self.username = username
        self.password = password
        self.submit.click()