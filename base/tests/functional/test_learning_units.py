##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################

from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.utils.translation import ugettext_lazy as _
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import WebDriverException
from base.tests.factories.academic_year import AcademicYearFakerFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFakerFactory
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

MAX_WAIT = 10


class LearningUnitsSearchTest(StaticLiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.PhantomJS()
        self.browser.set_window_size(1280, 720)

        User.objects.create_superuser(username='superdummy',
                                 email='superdummy@dummy.com',
                                password='superpassword')

    def error_displayed(self,error_msg):
        self.wait_for(lambda: self.browser.find_element_by_class_name('alert-danger').is_displayed())

    def go_to_learning_units_page(self):
        # She goes on the homepage to log in
        self.browser.get(self.live_server_url)
        self.wait_for(lambda: self.assertIn('Log-in',self.browser.find_element_by_tag_name('h1').text))

        # She is invited to log in
        self.the_user_logs_in()

        # She goes in the header menu and clicks on 'Formation Catalogue'
        # and then 'Learning Units' to go on the search page of learning units.
        self.browser.get(self.live_server_url+'/learning_units/')
        # She notices the title of the learning units search page
        self.wait_for(lambda: self.browser.find_element_by_tag_name('h2').is_displayed())

    def the_user_logs_in(self):
        inputbox_login_usr = self.browser.find_element_by_id('id_username')
        self.assertEqual(
            inputbox_login_usr.get_attribute('placeholder'),
            _('user')
        )
        inputbox_login_pwd = self.browser.find_element_by_id('id_password')
        self.assertEqual(
            inputbox_login_pwd.get_attribute('placeholder'),
            _('password')
        )
        inputbox_login_usr.send_keys('superdummy')
        inputbox_login_pwd.send_keys('superpassword')
        login_button = self.browser.find_element_by_id('post_login_btn')
        login_button.send_keys(Keys.ENTER)
        ## Wait for the home_page to load on screen
        self.wait_for(lambda:self.browser.find_element_by_id('lnk_home_dropdown_catalog').is_displayed())

    def wait_for_text_in_table(self, table_id, text_to_find, row_or_col):
        self.wait_for(lambda:self.assertIn(text_to_find, [element.text for element in self.browser.find_element_by_id(table_id).find_elements_by_tag_name(row_or_col)]))

    def wait_for(self, fct):
        start_time = time.time()
        while True:
            try:
                return fct()
            except (AssertionError, WebDriverException) as e:
                if time.time() - start_time > MAX_WAIT:
                    self.browser.save_screenshot('screenshot.png')
                    print('BROWSER_GET_LOG: '+str(self.browser.get_log('har')))
                    print('BROWSER_GET_HTML: '+str(self.browser.execute_script("return document.getElementsByTagName('html')[0].innerHTML")))
                    raise e
                time.sleep(0.5)

    def tearDown(self):
        self.browser.quit()

    def test_retrieve_learning_units_from_search_with_valid_acronym_only(self):
        ## First, lets plant some seeds..
        learning_unit_year_seed = LearningUnitYearFakerFactory()

        # Sarah needs to check out an existing learning_unit
        self.go_to_learning_units_page()

        # She enters a valid acronym only,
        # to see if a learning unit exists in a particular year.
        inputbox_acronym=self.browser.find_element_by_id('id_acronym')
        inputbox_acronym.send_keys(learning_unit_year_seed.acronym)

        # Then she start the search
        login_button= self.browser.find_element_by_id('bt_submit_learning_unit_search')
        login_button.send_keys(Keys.ENTER)

        #She now can see the response returned by the application
        self.wait_for_text_in_table('table_learning_units',learning_unit_year_seed.acronym,'td')

        # She sees that this acronym already exists and the corresponding class is still valid for a particular year
        # Satisfied, she logs out.

    def test_error_when_search_has_no_input_value_given_by_user(self):
        # Sarah needs to check out an existing learning_unit
        self.go_to_learning_units_page()

        # She starts a search by pressing ENTER by mistake,
        # without entering any input values
        login_button= self.browser.find_element_by_id('bt_submit_learning_unit_search')
        login_button.send_keys(Keys.ENTER)

        # She sees an error when the page refreshes
        self.error_displayed('LU_ERRORS_INVALID_SEARCH')

        # Unhappy of the situation, she closes the browser...

    def test_error_when_search_has_invalid_acronym_and_no_academic_year_given_by_user(self):
        # Sarah needs to check out an existing learning_unit
        self.go_to_learning_units_page()

        # She enters a non-valid acronym [< 3 CHAR] and doesnt specify an academic year,
        # to see if a learning unit exists in a particular year.
        inputbox_acronym=self.browser.find_element_by_id('id_acronym')
        inputbox_acronym.send_keys('AC')

        # She starts a search by pressing ENTER
        login_button= self.browser.find_element_by_id('bt_submit_learning_unit_search')
        login_button.send_keys(Keys.ENTER)

        # She sees an error when the page refreshes
        self.error_displayed('LU_ERRORS_INVALID_SEARCH')

        # Unhappy of the situation, she closes the browser...

    def test_error_when_search_has_no_acronym_and_no_academic_year_given_by_user(self):
        # Sarah needs to check out an existing learning_unit
        self.go_to_learning_units_page()

        # She enters a keyword only and doesnt specify an academic year,
        # to see if a learning unit exists in a particular year.
        inputbox_keyword=self.browser.find_element_by_id('id_keyword')
        inputbox_keyword.send_keys('KEYWORD')

        # She starts a search by pressing ENTER
        login_button= self.browser.find_element_by_id('bt_submit_learning_unit_search')
        login_button.send_keys(Keys.ENTER)

        # She sees an error when the page refreshes
        self.error_displayed('LU_ERRORS_ACADEMIC_YEAR_REQUIRED')

        # Unhappy of the situation, she closes the browser...

    def test_error_when_search_has_academic_year_but_no_other_input_value_given_by_user(self):
        ## First, lets plant some seeds..
        academic_year_seed = AcademicYearFakerFactory()

        # Sarah needs to check out an existing learning_unit
        self.go_to_learning_units_page()

        # She enters a keyword only and doesnt specify an academic year,
        # to see if a learning unit exists in a particular year.
        start_time = time.time()
        while True:
            try:
                academic_year = Select(self.browser.find_element_by_id('slt_academic_year'))
                academic_year.select_by_visible_text(academic_year_seed.name)
                return
            except (AssertionError, WebDriverException) as e:
                if time.time() - start_time > MAX_WAIT:
                    raise e
                time.sleep(0.5)

        # She starts a search by pressing ENTER
        login_button= self.browser.find_element_by_id('bt_submit_learning_unit_search')
        login_button.send_keys(Keys.ENTER)

        # She sees an error when the page refreshes
        self.error_displayed('LU_ERRORS_INVALID_SEARCH')

        # Unhappy of the situation, she closes the browser...
