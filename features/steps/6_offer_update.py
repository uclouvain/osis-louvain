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
from django.urls import reverse

from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_categories
from features.forms.education_groups import update_form
from features.pages.education_group.pages import EducationGroupPage, UpdateTrainingPage, QuickSearchPage, \
    AttachModalPage

use_step_matcher("parse")


@given("Aller sur la page de detail de la formation: {acronym} en {year}")
def step_impl(context: Context, acronym: str, year: str):
    egy = EducationGroupYear.objects.get(acronym=acronym, academic_year__year=int(year[:4]))
    url = reverse('education_group_read', args=[egy.pk, egy.pk])

    context.current_page = EducationGroupPage(driver=context.browser, base_url=context.get_url(url)).open()
    context.test.assertEqual(context.browser.current_url, context.get_url(url))


@given("Aller sur la page de detail d'une formation en année académique courante")
def step_impl(context: Context):
    egy = EducationGroupYear.objects.filter(
        academic_year=context.data.current_academic_year,
        education_group_type__category=education_group_categories.TRAINING
    ).order_by('?').first()
    url = reverse('education_group_read', args=[egy.pk, egy.pk])

    context.egy_modified = egy

    EducationGroupPage(driver=context.browser, base_url=context.get_url(url)).open()


@when("Offre cliquer sur le menu « Actions »")
def step_impl(context: Context):
    page = EducationGroupPage(driver=context.browser)
    page.actions.click()


@when("Offre Cliquer sur l'action recherche rapide")
def step_impl(context: Context):
    page = EducationGroupPage(driver=context.browser)
    page.quick_search.click()


@then("Vérifier que la dernière année d'organisation de la formation a été mis à jour")
def step_impl(context: Context):
    end_year_displayed = context.current_page.end_year.text
    context.test.assertEqual(context.form_data["end_year"], end_year_displayed)


@step("Encoder année de fin")
def step_impl(context: Context):
    page = UpdateTrainingPage(driver=context.browser)
    context.form_data = update_form.fill_end_year(page, context.data.current_academic_year)


@when("Cliquer sur « Modifier »")
def step_impl(context):
    page = EducationGroupPage(driver=context.browser)
    page.modify.click()


@step("Offre cliquer sur le bouton « Enregistrer »")
def step_impl(context: Context):
    page = UpdateTrainingPage(driver=context.browser)
    page.save_button.click()


@then("Vérifier que la formation {acronym} a bien été mise à jour de {start_year} à {end_year}")
def step_impl(context, acronym, start_year, end_year):
    for i in range(int(start_year), int(end_year) + 1):
        string_to_check = "{} ({}-".format(acronym, i)
        context.test.assertIn(string_to_check, context.current_page.success_messages.text)

    context.test.assertIn('mis à jour', context.current_page.success_messages.text)


@then("Vérifier que la formation {acronym} a bien été supprimée de {start_year} à {end_year}")
def step_impl(context, acronym, start_year, end_year):
    for i in range(int(start_year), int(end_year) + 1):
        string_to_check = "{} ({}-".format(acronym, i)
        context.test.assertIn(string_to_check, context.current_page.success_messages.text)

    context.test.assertIn('supprimé', context.current_page.success_messages.text)


@step("Vérifier qu'il n'y a que {count} résultats.")
def step_impl(context, count):
    context.test.assertEqual(count, context.current_page.count_result())


@step("Ouvrir {acronym} dans l’arbre")
def step_impl(context, acronym):
    context.current_page.open_node_tree_by_acronym(acronym)


@step("Cliquer sur la recherche rapide")
def step_impl(context):
    page = EducationGroupPage(driver=context.browser)
    page.quick_search.click()


@step("Selectionner le premier resultat (recherche rapide)")
def step_impl(context):
    page = QuickSearchPage(driver=context.browser)
    print(page.code.text)
    page.select_first = True


@step("Cliquer sur Ajouter (recherche rapide)")
def step_impl(context):
    page = QuickSearchPage(driver=context.browser)
    page.attach.click()


@step("Fermer la modal")
def step_impl(context):
    context.current_page = context.current_page.close.click()


@step("Selectionner l'onglet d'unité d'enseignement")
def step_impl(context):
    page = QuickSearchPage(driver=context.browser)
    page.lu_tab.click()


@step("Dans l'arbre, cliquer sur {action} sur {acronym}.")
def step_impl(context, action, acronym):
    if action.lower() == 'coller':
        context.current_page = context.current_page.attach_node_tree(acronym)
    elif action.lower() == 'copier':
        context.current_page.select_node_tree(acronym)
    else:
        raise Exception("Unknown action")


@step("Dans l'arbre et dans {parent}, cliquer sur {action} sur {acronym}.")
def step_impl(context, parent, action, acronym):
    if action.lower() == 'coller':
        context.current_page = context.current_page.attach_node_tree(acronym, parent)
    elif action.lower() == 'copier':
        context.current_page.select_node_tree(acronym, parent)
    elif action.lower() == 'retirer':
        context.current_page = context.current_page.detach_node_tree(acronym, parent)
    else:
        raise Exception("Unknown action")


@step("Cliquer sur « Enregistrer » dans la modal")
def step_impl(context):
    page = AttachModalPage(driver=context.browser)
    page.save_modal.click()


@step("Vérifier que l'UE se trouve bien dans l'arbre")
def step_impl(context):
    page = EducationGroupPage(driver=context.browser)
    nodes = page.panel_tree().nodes()
    context.test.assertIn(
        context.luy_to_attach,
        [node.text for node in nodes]
    )


@then("Vérifier que {acronym} a été mis à jour")
def step_impl(context, acronym):
    context.test.assertIn(acronym, context.current_page.success_messages.text)
    context.test.assertIn('mis à jour', context.current_page.success_messages.text)


@step("{child} se trouve bien dans l'arbre sous {parent}")
def step_impl(context, child, parent):
    context.current_page.find_node_tree_by_acronym(child, parent)


@step("{child} ne se trouve plus bien dans l'arbre sous {parent}")
def step_impl(context, child, parent):
    with context.test.assertRaises(Exception):
        context.current_page.find_node_tree_by_acronym(child, parent)


@step("Cliquer sur Copier dans la modal")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    context.current_page = context.current_page.copy_btn.click()
