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

from behave import *
from behave.runner import Context
from django.urls import reverse
from selenium.webdriver.common.by import By

from base.models.entity import Entity
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from features.pages.learning_unit.pages import LearningUnitPage, SearchLearningUnitPage

use_step_matcher("parse")


@step("Les propositions {proposals} doivent être attachées à {entity} en {year}")
def step_impl(context, proposals, entity, year):
    """
    :type context: behave.runner.Context
    """
    entity = Entity.objects.filter(entityversion__acronym=entity).last()
    for acronym in proposals.split(','):
        luy = LearningUnitYearFactory(acronym=acronym, academic_year__year=int(year[:4]))
        ProposalLearningUnitFactory(learning_unit_year=luy,
                                    entity=entity,
                                    folder_id=12)


@given("Aller sur la page de detail de l'ue: {acronym} en {year}")
def step_impl(context: Context, acronym: str, year: str):
    luy = LearningUnitYear.objects.get(acronym=acronym, academic_year__year=int(year[:4]))
    url = reverse('learning_unit', args=[luy.pk])

    LearningUnitPage(driver=context.browser, base_url=context.get_url(url)).open()


@given("Aller sur la page de detail de l'ue: {acronym}")
def step_impl(context: Context, acronym: str):
    luy = LearningUnitYear.objects.get(acronym=acronym)
    url = reverse('learning_unit', args=[luy.pk])

    context.current_page = LearningUnitPage(driver=context.browser, base_url=context.get_url(url)).open()
    context.test.assertEqual(context.browser.current_url, context.get_url(url))


@step("Cliquer sur le menu « Mettre en proposition de fin d’enseignement »")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    page = LearningUnitPage(driver=context.browser)
    page.proposal_suppression.click()


@step("Cliquer sur « Modifier la proposition »")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    page = LearningUnitPage(driver=context.browser)
    page.edit_proposal_button.click()


@when("Sélectionner le premier résultat")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    page = SearchLearningUnitPage(driver=context.browser)
    page.find_element(
        By.CSS_SELECTOR,
        '#table_learning_units > tbody > tr:nth-child(1) > td:nth-child(1) > input'
    ).click()
    time.sleep(1)


@step("Cliquer sur « Retour à l’état initial »")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    page = SearchLearningUnitPage(driver=context.browser)
    page.find_element(By.ID, 'btn_modal_get_back_to_initial').click()


@step("Cliquer sur « Oui » pour retourner à l'état initial")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    page = SearchLearningUnitPage(driver=context.browser)
    page.back_to_initial_yes.click()


@then("Vérifier que la proposition {acronym} a été {msg}.")
def step_impl(context, acronym, msg):
    """
    :type context: behave.runner.Context
    """
    page = LearningUnitPage(driver=context.browser)
    context.test.assertIn(acronym, page.success_messages.text)
    context.test.assertIn(msg, page.success_messages.text)


@step("Cliquer sur le menu « Mettre en proposition de modification »")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    page = LearningUnitPage(driver=context.browser)
    page.proposal_edit.click()


@step("Cliquer sur le menu Proposition de création")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    page = SearchLearningUnitPage(driver=context.browser)
    page.create_proposal_url.click()
