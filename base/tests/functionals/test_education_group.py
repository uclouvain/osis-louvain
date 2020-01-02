import unittest

import pypom
from django.conf import settings
from django.contrib.auth.models import Permission
from django.test import tag
from django.test.selenium import SeleniumTestCase
from django.urls import reverse
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from base.models.enums import education_group_categories
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from cms.enums import entity_name
from cms.tests.factories.text_label import TextLabelFactory
from cms.tests.factories.translated_text import TranslatedTextRandomFactory, EnglishTranslatedTextRandomFactory
from cms.tests.factories.translated_text_label import TranslatedTextLabelFactory

try:
    import pyvirtualdisplay

    HAS_VIRTUAL_DISPLAY = True
except ImportError:
    HAS_VIRTUAL_DISPLAY = False


class Field:
    def __init__(self, *locator):
        self.locator = locator


class InputField(Field):
    def __set__(self, obj, value):
        element = obj.find_element(*self.locator)
        element.clear()
        if value is not None:
            element.send_keys(value)

    def __get__(self, obj, owner):
        element = obj.find_element(*self.locator)
        return element.get_attribute('value')


class SubmitField(Field):
    def __get__(self, obj, owner):
        return obj.find_element(*self.locator)


class CharField(Field):
    def __get__(self, obj, owner):
        return obj.find_element(*self.locator).text


class LoginPage(pypom.Page):
    URL_TEMPLATE = '/login/'

    username = InputField(By.ID, 'id_username')
    password = InputField(By.ID, 'id_password')
    submit = SubmitField(By.ID, 'post_login_btn')

    def login(self, username, password='password123'):
        self.username = username
        self.password = password
        self.submit.click()


class TermRegion(pypom.Region):
    _BUTTON_EDIT_SELECTOR = (By.CSS_SELECTOR, "a[class~='pedagogy-edit-btn']")
    title = CharField(By.CSS_SELECTOR, "label[id^='label_']")
    french = CharField(By.CSS_SELECTOR, "div[id^='content_fr_']")
    english = CharField(By.CSS_SELECTOR, "div[id^='content_en_']")
    edit_button = SubmitField(*_BUTTON_EDIT_SELECTOR)

    def has_edit_button(self):
        try:
            WebDriverWait(self.driver, 1).until(
                expected_conditions.presence_of_element_located(self._BUTTON_EDIT_SELECTOR)
            )

            return True
        except (NoSuchElementException, TimeoutException):
            return False


class EducationGroupPage(pypom.Page):
    def terms(self):
        elements = self.find_elements(By.CSS_SELECTOR, "#panel-data > div[class~='section_label']")
        for el in elements:
            yield TermRegion(self, el)


def skipUnlessSelenium(func):
    use_selenium = getattr(settings, 'USE_SELENIUM_FOR_FUNCTIONAL_TESTS', False)
    return unittest.skipUnless(use_selenium, 'Skip Selenium')(func)


@tag('selenium')
@skipUnlessSelenium
class TestEducationGroupYear(SeleniumTestCase):
    browser = 'chrome'

    @classmethod
    def setUpClass(cls):
        if HAS_VIRTUAL_DISPLAY:
            cls.virtual_display = pyvirtualdisplay.Display(size=(1920, 1080))
            cls.virtual_display.start()

        super().setUpClass()
        cls.selenium.set_window_size(1920, 1080)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'virtual_display'):
            cls.virtual_display.stop()

        super().tearDownClass()

    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.person = PersonFactory(user=self.user)

        # the user can access to the education group
        self.user.user_permissions.add(Permission.objects.get(codename='can_access_education_group'))

        academic_year = AcademicYearFactory()

        type_training = EducationGroupTypeFactory(category=education_group_categories.TRAINING)

        self.education_group_parent = EducationGroupYearFactory(acronym="Parent",
                                                                academic_year=academic_year,
                                                                education_group_type=type_training)

        self.education_group_year = EducationGroupYearFactory(acronym="Child_1",
                                                              academic_year=academic_year,
                                                              education_group_type=type_training)

        GroupElementYearFactory(parent=self.education_group_parent, child_branch=self.education_group_year)

        self.text_label = TextLabelFactory(label='welcome_introduction',
                                           entity=entity_name.OFFER_YEAR)

        TranslatedTextLabelFactory(text_label=self.text_label,
                                   language="fr-be",
                                   label='Introduction')

        TranslatedTextLabelFactory(text_label=self.text_label,
                                   language="en",
                                   label='Introduction')
        # fr-be
        TranslatedTextRandomFactory(text_label=self.text_label,
                                    entity=self.text_label.entity,
                                    reference=str(self.education_group_year.id))

        # en
        EnglishTranslatedTextRandomFactory(text_label=self.text_label,
                                           entity=self.text_label.entity,
                                           reference=str(self.education_group_year.id))
        page = LoginPage(
            driver=self.selenium,
            base_url=self.live_server_url + '/login/'
        ).open()

        page.login(username=self.user.username)

        self.url = reverse('education_group_general_informations',
                           args=[self.education_group_parent.id, self.education_group_year.id])

    def test_can_not_edit_education_group(self):
        page = EducationGroupPage(driver=self.selenium, base_url=self.live_server_url + self.url).open()

        term = next(page.terms())

        self.assertFalse(term.has_edit_button())

    def test_can_edit_education_group(self):
        self.user.user_permissions.add(Permission.objects.get(codename='change_pedagogyinformation'))
        page = EducationGroupPage(driver=self.selenium, base_url=self.live_server_url + self.url).open()

        term = next(page.terms())

        self.assertTrue(term.has_edit_button())

    def test_edit_education_group_french(self):
        self.user.user_permissions.add(Permission.objects.get(codename='change_pedagogyinformation'))

        page = EducationGroupPage(driver=self.selenium, base_url=self.live_server_url + self.url).open()

        term = next(page.terms())

        self.assertEqual(term.title, 'Introduction')

        self.assertTrue(term.has_edit_button())
        term.edit_button.click()

        WebDriverWait(self.selenium, 10).until(
            expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, 'div.modal-footer'))
        )

        self.selenium.switch_to.frame(self.selenium.find_element_by_tag_name("iframe"))
        element = self.selenium.find_element_by_tag_name('body')

        element.clear()
        element.send_keys('ceci est un test')

        self.selenium.switch_to.default_content()

        element = self.selenium.find_element(By.CSS_SELECTOR, 'div.modal-footer > button.btn-primary[type="submit"]')
        element.click()

        term = next(page.terms())

        self.assertEqual(term.title, 'Introduction')
        self.assertEqual(term.french, 'ceci est un test')

    def test_edit_education_group_english(self):
        self.user.user_permissions.add(Permission.objects.get(codename='change_pedagogyinformation'))
        page = EducationGroupPage(driver=self.selenium, base_url=self.live_server_url + self.url).open()

        term = next(page.terms())

        self.assertEqual(term.title, 'Introduction')

        self.assertTrue(term.has_edit_button())
        term.edit_button.click()

        WebDriverWait(self.selenium, 10).until(
            expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, 'div.modal-footer'))
        )

        self.selenium.find_element_by_css_selector("a[href='#modification_en']").click()

        self.selenium.switch_to.frame(self.selenium.find_element_by_css_selector("iframe[title~='id_text_english']"))
        element = self.selenium.find_element_by_tag_name('body')

        element.clear()
        element.send_keys('this is a test')

        self.selenium.switch_to.default_content()

        element = self.selenium.find_element(By.CSS_SELECTOR, 'div.modal-footer > button.btn-primary[type="submit"]')
        element.click()

        term = next(page.terms())

        self.assertEqual(term.title, 'Introduction')
        self.assertEqual(term.english, 'this is a test')
