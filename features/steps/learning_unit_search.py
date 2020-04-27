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
import os

from behave import *
from behave.runner import Context
from django.utils.translation import gettext_lazy as _

from features.forms.learning_units import search_form
from features.pages.learning_unit.pages import SearchLearningUnitPage

use_step_matcher("re")


@step("Aller sur la page de recherche d'UE")
def step_impl(context: Context):
    url = 'learning_units'
    SearchLearningUnitPage(driver=context.browser, base_url=context.get_url(url)).open()


@step("Réinitialiser les critères de recherche")
def step_impl(context: Context):
    page = SearchLearningUnitPage(driver=context.browser)
    page.clear_button.click()


@step("Cliquer sur le bouton Rechercher \(Loupe\)")
def step_impl(context: Context):
    page = SearchLearningUnitPage(driver=context.browser)
    page.search.click()


@then("Le nombre total de résultat est (?P<result_count>.+)")
def step_impl(context: Context, result_count: str):
    page = SearchLearningUnitPage(driver=context.browser)
    context.test.assertEqual(page.count_result(), result_count)


@when("Ouvrir le menu « Exporter »")
def step_impl(context: Context):
    page = SearchLearningUnitPage(driver=context.browser)
    page.export.click()


@step("Sélection « Liste personnalisée des unités d’enseignement »")
def step_impl(context: Context):
    page = SearchLearningUnitPage(driver=context.browser)
    page.list_learning_units.click()


@step("Cocher les cases « Programmes/regroupements » et « Enseignant\(e\)s »")
def step_impl(context: Context):
    page = SearchLearningUnitPage(driver=context.browser)
    page.with_program.click()
    page.with_tutor.click()


@step("Cliquer sur « Produire Excel »")
def step_impl(context: Context):
    page = SearchLearningUnitPage(driver=context.browser)
    page.generate_xls.click()


@step("Sélectionner l’onglet « Propositions »")
def step_impl(context: Context):
    page = SearchLearningUnitPage(driver=context.browser)
    page.proposal_search.click()


@step("Encoder le code d'une UE")
def step_impl(context: Context):
    page = SearchLearningUnitPage(driver=context.browser)
    context.search_form_values = search_form.fill_code(page)


@step("Encoder le type d'UE")
def step_impl(context: Context):
    page = SearchLearningUnitPage(driver=context.browser)
    context.search_form_values = search_form.fill_container_type(page)


@step("Encoder l'entité d'UE")
def step_impl(context: Context):
    page = SearchLearningUnitPage(driver=context.browser)
    context.search_form_values = search_form.fill_entity(page)


@step("Encoder l'enseignant d'UE")
def step_impl(context: Context):
    page = SearchLearningUnitPage(driver=context.browser)
    context.search_form_values = search_form.fill_tutor(page)


@step("La liste de résultat doit correspondre aux crières de recherche")
def step_impl(context: Context):
    page = SearchLearningUnitPage(driver=context.browser)
    search_criterias = context.search_form_values
    context.test.assertLearningUnitResultsMatchCriteria(page.results, search_criterias)


@then("Le fichier excel devrait être présent")
def step_impl(context: Context):
    filename = "{}.xlsx".format(_('LearningUnitsList'))
    full_path = os.path.join(context.download_directory, filename)
    context.test.assertTrue(os.path.exists(full_path), full_path)
