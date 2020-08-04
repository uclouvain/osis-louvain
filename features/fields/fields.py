# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select

from base.models.entity_version import EntityVersion


class Field:
    """
        Field respects the descriptor pattern for the setter but not for the getter.
        The purpose of this method, it is to allow the user to fetch the selenium node and to manipulate it.
    """
    def __init__(self, *locator):
        self.locator = locator
        self.element = None
        self.current_page = None

    def __get__(self, obj, owner):
        self.element = obj.wait.until(lambda o: obj.find_element(*self.locator))
        self.current_page = obj
        return self

    def is_enabled(self):
        return self.element.is_enabled()

    @property
    def text(self):
        return self.element.text


class Link(Field):

    def __init__(self, page, by, selector, waiting_time=0):
        super().__init__(by, selector)
        self.page = page
        self.waiting_time = waiting_time

    def click(self):
        # Scroll to the top. The button can be under the navbar.
        self.current_page.driver.execute_script("window.scrollTo(0, 0);")
        self.element.click()
        if isinstance(self.page, str):
            mod = __import__('features.steps.utils.pages', fromlist=[self.page])
            self.page = getattr(mod, self.page)

        new_page = self.page(self.current_page.driver, self.current_page.driver.current_url)

        # Sometimes the wait_for_page_to_load does not work because the redirection is on the same page.
        # In that case, we have to impose a waiting time to be sure that the page is reloaded.
        time.sleep(self.waiting_time)

        new_page.wait_for_page_to_load()

        return new_page


class LinkBis(Field):
    def __init__(self, by, selector):
        super().__init__(by, selector)

    def click(self):
        # Scroll to the top. The button can be under the navbar.
        self.current_page.driver.execute_script("window.scrollTo(0, 0);")
        self.element.click()


class InputField(Field):

    def __set__(self, obj, value):
        element = obj.wait.until(lambda o: obj.find_element(*self.locator))
        element.clear()
        if value is not None:
            element.send_keys(value)

    @property
    def text(self):
        return self.element.get_attribute("value")


class TextAreaField(Field):
    def __set__(self, obj, value):
        element = obj.wait.until(lambda obj: obj.find_element(*self.locator))
        element.clear()
        if value is not None:
            element.send_keys(value)


class CkeditorField(Field):
    """
        For Ckeditor, the field is included in an iframe,
        We need to go into the frame before send the value.
    """
    def __set__(self, obj, value):
        element = obj.find_element(*self.locator)
        obj.driver.switch_to.frame(element)
        body = obj.find_element(By.TAG_NAME, "body")
        body.clear()
        if value is not None:
            body.send_keys(value)

        obj.driver.switch_to.default_content()

    @property
    def text(self):
        self.element = self.current_page.find_element(*self.locator)
        self.current_page.driver.switch_to.frame(self.element)
        body = self.current_page.find_element(By.TAG_NAME, "body")

        self.current_page.driver.switch_to.default_content()

        return body.get_attribute('value')


class SelectField(Field):

    def __get__(self, instance, owner):
        obj = super().__get__(instance, owner)
        return Select(self.element)

    def __set__(self, obj, value):
        element = Select(obj.find_element(*self.locator))
        try:
            element.select_by_value(str(value))
        except NoSuchElementException:
            element.select_by_visible_text(value)

    def options(self):
        return Select(self.element).options()

    @property
    def text(self):
        return Select(self.element).first_selected_option.text


class Select2Field(Field):
    sub_input_locator = "select2-search__field"

    def __set__(self, obj, value):
        element = obj.find_element(*self.locator)
        element.click()

        sub_element = obj.find_element(By.CLASS_NAME, self.sub_input_locator)
        sub_element.clear()

        if value is not None:
            sub_element.send_keys(value)
        time.sleep(1)
        sub_element.send_keys(Keys.RETURN)


class ButtonField(Field):

    def __init__(self, by, selector, waiting_time=0):
        super().__init__(by, selector)
        self.waiting_time = waiting_time

    def click(self):
        self.element.click()
        time.sleep(self.waiting_time)


class SubmitField(ButtonField):
    pass


class CharField(Field):

    @property
    def text(self):
        return self.element.text


class Checkbox(Field):

    def __set__(self, obj, value: bool):
        element = obj.find_element(*self.locator)
        old_val = element.get_attribute('checked')
        if not old_val and value:
            element.click()
        elif old_val and not value:
            element.click()


class RadioField(Field):

    def __set__(self, obj, value):
        element = obj.find_element(*self.locator)

        choices = element.find_elements(By.XPATH, '//*[@id="id_mandatory"]/div/label')
        for choice in choices:
            if choice.text == value:
                choice.click()


class SelectEntityVersionField(SelectField):

    def __set__(self, obj, value):
        value = EntityVersion.objects.filter(acronym=value).order_by('start_date').last().pk
        return super().__set__(obj, value)
