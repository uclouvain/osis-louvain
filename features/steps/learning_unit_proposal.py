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
import random

from behave import *
from behave.runner import Context
from django.utils.translation import gettext_lazy as _

from features.forms.learning_units import search_proposal_form, update_proposal_form
from features.pages.learning_unit.pages import SearchProposalPage, EditLearningUnitProposalPage, LearningUnitPage

use_step_matcher("parse")


@step("Aller sur la page de recherche des propositions")
def step_impl(context: Context):
    url = 'learning_units_proposal'
    SearchProposalPage(driver=context.browser, base_url=context.get_url(url)).open()


@step("Rechercher propositions de création")
def step_impl(context: Context):
    page = SearchProposalPage(driver=context.browser)
    context.form_data = search_proposal_form.fill_search_creation_proposal(page)
    page.search.click()


@step("Rechercher propositions de suppression")
def step_impl(context: Context):
    page = SearchProposalPage(driver=context.browser)
    context.form_data = search_proposal_form.fill_search_suppression_proposal(page)
    page.search.click()


@step("Rechercher propositions de modification")
def step_impl(context: Context):
    page = SearchProposalPage(driver=context.browser)
    context.form_data = search_proposal_form.fill_search_modification_proposal(page)
    page.search.click()


@step("Sélectionner une proposition")
def step_impl(context: Context):
    page = SearchProposalPage(driver=context.browser)
    random_proposal = random.choice(page.proposal_results)
    random_proposal.acronym.click()


@step("Proposition encoder l'état Accepté")
def step_impl(context: Context):
    page = EditLearningUnitProposalPage(driver=context.browser)
    context.form_data = update_proposal_form.accept_proposal(page)


@step("Proposition Cliquer sur le bouton « Enregistrer »")
def step_impl(context: Context):
    page = EditLearningUnitProposalPage(driver=context.browser)
    page.save_button.click()


@step("Vérifier que la proposition est en état Accepté")
def step_impl(context: Context):
    page = LearningUnitPage(driver=context.browser)
    context.test.assertEqual(
        page.proposal_state.text,
        context.form_data["proposal_state"]
    )


@step("Cliquer sur « Consolider »")
def step_impl(context: Context):
    page = LearningUnitPage(driver=context.browser)
    page.consolidate_proposal.click()


@step("Cliquer sur « Oui » pour consolider")
def step_impl(context: Context):
    page = LearningUnitPage(driver=context.browser)
    page.confirm_consolidate.click()


@step("Vérifier que la proposition a été consolidée avec succès")
def step_impl(context: Context):
    page = LearningUnitPage(driver=context.browser)
    context.test.assertIn(str(_('successfully consolidated')), page.success_messages.text)

