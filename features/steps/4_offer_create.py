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
from behave import *
from behave.runner import Context
from django.utils.text import slugify
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from waffle.models import Flag

from features.forms.education_groups import create_form
from features.pages.education_group.pages import SearchEducationGroupPage, UpdateTrainingPage, EducationGroupPage, \
    NewTrainingPage, QuickSearchPage
from features.steps.utils import query

use_step_matcher("parse")


@step("les flags d'éditions des offres sont désactivés.")
def step_impl(context: Context):
    Flag.objects.update_or_create(name='education_group_create', defaults={"authenticated": True})
    Flag.objects.update_or_create(name='education_group_delete', defaults={"authenticated": True})
    Flag.objects.update_or_create(name='education_group_update', defaults={"authenticated": True})


@given("Aller sur la page Catalogue de formations / Formation")
def step_impl(context: Context):
    url = '/educationgroups/'
    SearchEducationGroupPage(driver=context.browser, base_url=context.get_url(url)).open()


@when("Recherche offre Cliquer sur le menu « Actions »")
def step_impl(context: Context):
    page = SearchEducationGroupPage(driver=context.browser)
    page.actions.click()


@step("Offre réinitialiser les critères de recherche")
def step_impl(context: Context):
    page = SearchEducationGroupPage(driver=context.browser)
    page.clear_button.click()


@step("Offre Cliquer sur le bouton Rechercher (Loupe)")
def step_impl(context: Context):
    page = SearchEducationGroupPage(driver=context.browser)
    page.search.click()


@step("Cliquer sur « Nouvelle Formation »")
def step_impl(context):
    page = SearchEducationGroupPage(driver=context.browser)
    page.new_training.click()


@step("Sélectionner le type de formation à {value}")
def step_impl(context: Context, value: str):
    page = SearchEducationGroupPage(driver=context.browser)
    page.type_de_formation = value


@step("Encoder {value} comme {field}")
def step_impl(context: Context, value: str, field: str):
    page = NewTrainingPage(driver=context.browser)
    slug_field = slugify(field).replace('-', '_')
    if hasattr(page, slug_field):
        setattr(page, slug_field, value)
    else:
        raise AttributeError(page.__class__.__name__ + " has no " + slug_field)


@step("Offre Encoder le code d'une UE")
def step_impl(context: Context):
    page = QuickSearchPage(driver=context.browser)
    code = query.get_random_learning_unit().acronym
    page.code = code
    context.luy_to_attach = code


@step("Cliquer sur le bouton Rechercher (recherche rapide)")
def step_impl(context: Context):
    page = QuickSearchPage(driver=context.browser)
    page.search.click()


@step("Offre création Cliquer sur le bouton « Enregistrer »")
def step_impl(context: Context):
    page = NewTrainingPage(driver=context.browser)
    page.save_button.click()


@step("Cliquer sur « Oui, je confirme »")
def step_impl(context: Context):
    page = EducationGroupPage(driver=context.browser)
    page.confirm_modal.click()


@step("Cliquer sur l'onglet Diplômes/Certificats")
def step_impl(context):
    page = NewTrainingPage(driver=context.browser)
    page.tab_diploma.click()


@step("Si une modal d'avertissement s'affiche, cliquer sur « oui »")
def step_impl(context: Context):
    try:
        page = UpdateTrainingPage(driver=context.browser)
        page.find_element(
            By.CSS_SELECTOR,
            '#confirm-modal > div > div > div.modal-footer > button.btn.btn-warning'
        ).click()
    except NoSuchElementException:
        pass


@then("Vérifier que la formation {acronym} à bien été créée de {start_year} à {end_year}")
def step_impl(context, acronym, start_year, end_year):
    """
    :type context: behave.runner.Context
    """
    for i in range(int(start_year), int(end_year) + 1):
        string_to_check = "{} ({}-".format(acronym, i)
        context.test.assertIn(string_to_check, context.current_page.success_messages.text)


@then("Vérifier que la formation {acronym} à bien été créée")
def step_impl(context, acronym):
    page = EducationGroupPage(driver=context.browser)
    string_to_check = "créée avec succès"
    context.test.assertIn(string_to_check, page.success_messages.text)


@then("Vérifier que le champ {field} est bien {value}")
def step_impl(context, field, value):
    page = EducationGroupPage(driver=context.browser)
    slug_field = slugify(field).replace('-', '_')
    context.test.assertIn(value, getattr(page, slug_field).text)


@step("Cliquer sur « Nouvelle Mini-Formation »")
def step_impl(context: Context):
    page = SearchEducationGroupPage(driver=context.browser)
    page.new_mini_training.click()


@when("Ouvrir l'arbre")
def step_impl(context: Context):
    page = EducationGroupPage(driver=context.browser)
    page.toggle_tree.click()


@when("Ouvrir l'entiereté de l'arbre")
def step_impl(context: Context):
    page = EducationGroupPage(driver=context.browser)
    page.open_all()


@when("Sélectionner un tronc commun dans l'arbre")
def step_impl(context: Context):
    page = EducationGroupPage(driver=context.browser)
    root_element_id = page.panel_tree().root_node.element.get_attribute("element_id")
    acronym = query.get_random_element_from_tree(int(root_element_id))
    element = next(
        node for node in page.panel_tree().nodes() if acronym in node.text
    )
    element.click()


@then("Vérifier que le(s) enfant(s) de {code} sont bien {children}")
def step_impl(context, code, children):
    """
    :type context: behave.runner.Context
    :type code: str
    :type children: str
    """
    context.current_page.open_first_node_tree.click()

    expected_children = children.split(',')
    children_in_tree = context.current_page.get_name_first_children()
    for i, child in enumerate(expected_children):
        context.test.assertIn(child, children_in_tree[i])


@step("Remplir formulaire de création de formation")
def step_impl(context: Context):
    page = NewTrainingPage(driver=context.browser)
    context.form_data = create_form.fill_training_form(page, context.user.person)


@step("Remplir formulaire de création de mini-formation")
def step_impl(context: Context):
    page = NewTrainingPage(driver=context.browser)
    context.form_data = create_form.fill_mini_training_form(page, context.user.person)
