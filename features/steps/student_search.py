#############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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

from behave import *
from behave.runner import Context

from features.steps.utils.pages import SearchStudentPage

use_step_matcher("re")


@step("Aller sur la page de recherche d'étudiants")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    url = '/students/'
    context.current_page = SearchStudentPage(driver=context.browser, base_url=context.get_url(url)).open()
    context.test.assertEqual(context.browser.current_url, context.get_url(url))


@step("Cliquer sur le bouton Rechercher étudiant \(Loupe\)")
def step_impl(context: Context):
    context.current_page.search.click()
    context.current_page.wait_for_page_to_load()


@step("Dans la liste des étudiants, le\(s\) premier\(s\) « Sigle » est\(sont\) bien (?P<results>.+)\.")
def step_impl(context, results):
    """
    :type context behave.runner.Context
    :type results str
    """
    acronyms = results.split(',')
    for row, acronym in enumerate(acronyms):
        context.test.assertEqual(context.current_page.find_acronym_in_table(row + 1), acronym)


@step("Dans la liste des étudiants, le\(s\) premier\(s\) « Noma » est\(sont\) bien (?P<results>.+)\.")
def step_impl(context, results):
    """
    :type context behave.runner.Context
    :type results str
    """
    registrations_ids = results.split(',')
    for row, registration_id in enumerate(registrations_ids):
        context.test.assertEqual(context.current_page.find_registration_id_in_table(row + 1), registration_id)


@then("Dans la liste, le « Nom » (?P<search_value>.+) est bien présent partout dans la colonne des noms\.")
def step_impl(context, search_value):
    """
    :type context behave.runner.Context
    :type search_value str
    """
    names = context.current_page.find_name_in_table()
    for value in names:
        context.test.assertIn(search_value.upper(), value.upper())
