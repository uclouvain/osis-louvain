##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import os
from datetime import date

from django.apps import apps
from django.core.serializers import serialize
from selenium.common.exceptions import NoSuchElementException
from backoffice.settings import SCREEN_SHOT_FOLDER, BASE_DIR
from base.tests.selenium.non_db_data import users


def take_screen_shot(test_class, name):
    today = date.today().strftime("%d_%m_%H_%M")
    screenshot_name = ''.join([name, '_', today, '.png'])
    test_class.selenium.save_screenshot(os.path.join(SCREEN_SHOT_FOLDER, screenshot_name))


def get_url(test_class, url):
    test_class.selenium.get('%s%s' % (test_class.live_server_url, url))


def assert_is_element_present(test_class, assertion, element_id):
    """
    Asert that an element defined by his id is present or not on the page.
    If the assertion is wrong , a screenshot is taken and an assertionError is raised
    """
    is_present = True
    try:
        test_class.selenium.find_element_by_id(element_id)
    except NoSuchElementException:
        is_present = False
    try:
        test_class.assertEqual(assertion, is_present,
                               "Element {} is {} present".format(
                                    element_id,
                                    'not' if assertion else ''
                                ))
    except AssertionError as ae:
        take_screen_shot(test_class, element_id)
        raise ae


def get_element_by_id(test_class, element_id):
    """
    Return the element deisgned by the id.
    If the element is not present , take a screenshot and raise an exception
    :param element_id: The id of the element we are looking for
    :param test_class
    :return: The element if found
    """
    try:
        return test_class.selenium.find_element_by_id(element_id)
    except NoSuchElementException as nsee:
        take_screen_shot(test_class, element_id)
        raise nsee


def assert_is_enabled(test_class, assertion, element_id):
    """
    Assert that an element is enabled or not on the page.
    Raise an assetionError if the assertion is false
    :param test_class: The test class used to test
    :param assertion: True or False
    :param element_id: The element we want to test
    """
    try:
        is_enabled = test_class.selenium.find_element_by_id(element_id).is_enabled()
    except NoSuchElementException:
        is_enabled = False
    try:
        return test_class.assertEqual(assertion, is_enabled,
                                      "Element {} is {} enabled".format(
                                          element_id,
                                          'not' if assertion else ''
                                      ))
    except AssertionError as ae:
        take_screen_shot(test_class, element_id)
        raise ae


def login_as(test_class, user):
    """
    Log into the application as a user
    :param test_class: The test class
    :param user: The user
    """
    get_url(test_class, "/")
    user_username = users.get(user).get('username')
    user_passwd = users.get(user).get('password')
    get_element_by_id(test_class, 'lnk_login').click()
    get_element_by_id(test_class, 'id_username').send_keys(user_username)
    get_element_by_id(test_class, 'id_password').send_keys(user_passwd)
    get_element_by_id(test_class, 'post_login_btn').click()


def log_out(test_class):
    """
    Log out from the application
    :param test_class: The test class
    """
    get_element_by_id(test_class, 'bt_user').click()
    get_element_by_id(test_class, 'lnk_logout').click()


def assert_txt_contain(test_class, assertion, element_id, text):
    """
    Assert that a text element contain a text or not
    Raise an assetionError if the assertion is false
    This method is not suited to be used with input.
    Input texts store their text value in element.getAttribute("value")
    :param test_class: The test class
    :param assertion: True or False
    :param element_id: The id of the element we want to test the text
    :param text: The text we assert is or isn't in the text element
    """
    try:
        element_txt = test_class.selenium.find_element_by_id(element_id).getText()
    except NoSuchElementException:
        element_txt = None
    try:
        test_class.assertEqual(
            assertion,
            text in element_txt,
            "Element {} text should {} contains {}".format(
                element_id,
                'not' if not assertion else '',
                text
            ))
    except AssertionError as ae:
        take_screen_shot(test_class, element_id)
        raise ae


def dump_data_after_tests(apps_name_list, fixture_name):
    apps_models = [model for app_name in apps_name_list for model in apps.get_app_config(app_name).get_models()]
    query_sets = [list(model.objects.all()) for model in apps_models]
    fixture = serialize('json', query_sets)
    file_path = os.path.join(BASE_DIR,
                             "base/tests/selenium/data_after_tests/{}_{}.json"
                             .format(fixture_name, date.today()
                                     .strftime("%d_%m_%H_%M")))
    file = open(file_path, 'w')
    file.write(fixture)
    file.close()