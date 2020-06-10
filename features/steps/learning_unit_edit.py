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
from datetime import datetime, timedelta

from behave import *
from behave.runner import Context
from django.urls import reverse
from django.utils.text import slugify
from waffle.models import Flag

from base.models.academic_calendar import AcademicCalendar
from base.models.academic_year import current_academic_year, AcademicYear
from base.models.entity_version import EntityVersion
from base.models.enums.academic_calendar_type import EDUCATION_GROUP_EDITION
from base.models.learning_unit_year import LearningUnitYear
from features.forms.learning_units import update_form, create_form
from features.pages.learning_unit.pages import LearningUnitPage, LearningUnitEditPage, SearchLearningUnitPage, \
    NewPartimPage, NewLearningUnitPage
from features.steps.utils.query import get_random_learning_unit_outside_of_person_entities, \
    get_random_learning_unit_inside_of_person_entities

use_step_matcher("parse")


@when("Cliquer sur le menu « Actions »")
def step_impl(context: Context):
    page = LearningUnitPage(driver=context.browser)
    page.actions.click()


@when("Cliquer sur le menu « Actions » depuis la recherche")
def step_impl(context: Context):
    page = SearchLearningUnitPage(driver=context.browser)
    page.actions.click()


@then("L’action « Modifier » est désactivée.")
def step_impl(context: Context):
    page = LearningUnitPage(driver=context.browser)
    context.test.assertTrue(page.is_li_edit_link_disabled())


@given("Aller sur la page de detail d'une UE ne faisant pas partie de la faculté")
def step_impl(context: Context):
    luy = get_random_learning_unit_outside_of_person_entities(context.user.person)
    url = reverse('learning_unit', args=[luy.pk])

    LearningUnitPage(driver=context.browser, base_url=context.get_url(url)).open()


@given("Aller sur la page de detail d'une UE faisant partie de la faculté")
def step_impl(context: Context):
    luy = get_random_learning_unit_inside_of_person_entities(context.user.person)
    context.learning_unit_year = luy
    url = reverse('learning_unit', args=[luy.pk])

    LearningUnitPage(driver=context.browser, base_url=context.get_url(url)).open()


@given("Aller sur la page de detail d'une UE faisant partie de la faculté l'année suivante")
def step_impl(context: Context):
    entities_version = EntityVersion.objects.get(entity__personentity__person=context.user.person).descendants
    entities = [ev.entity for ev in entities_version]
    luy = LearningUnitYear.objects.filter(
        learning_container_year__requirement_entity__in=entities,
        academic_year__year=current_academic_year().year + 1
    ).order_by("?")[0]
    context.learning_unit_year = luy
    url = reverse('learning_unit', args=[luy.pk])

    LearningUnitPage(driver=context.browser, base_url=context.get_url(url)).open()


@then("L’action « Modifier » est activée.")
def step_impl(context: Context):
    page = LearningUnitPage(driver=context.browser)
    context.test.assertFalse(page.is_li_edit_link_disabled())


@step("Cliquer sur le menu « Modifier »")
def step_impl(context):
    page = LearningUnitPage(driver=context.browser)
    page.edit_button.click()


@step("Le gestionnaire faculatire remplit le formulaire d'édition des UE")
def step_impl(context: Context):
    page = LearningUnitEditPage(driver=context.browser)
    context.form_data = update_form.fill_form_for_faculty(page)


@step("Le gestionnaire faculatire remplit le formulaire de création de partim")
def step_impl(context: Context):
    page = NewPartimPage(driver=context.browser)
    context.form_data = create_form.fill_partim_form_for_faculty_manager(page)


@step("Le gestionnaire central remplit le formulaire de création d'autre collectif")
def step_impl(context: Context):
    page = NewLearningUnitPage(driver=context.browser)
    context.form_data = create_form.fill_other_collective_form_for_central_manager(page, context.user.person)


@step("Le gestionnaire central remplit le formulaire d'édition des UE")
def step_impl(context: Context):
    page = LearningUnitEditPage(driver=context.browser)
    context.form_data = update_form.fill_form_for_central(page)


@step("Vérifier UE a été mis à jour")
def step_impl(context: Context):
    page = LearningUnitPage(driver=context.browser)
    context.test.assertLearningUnitHasBeenUpdated(page, context.form_data)


@step("Encoder année suivante")
def step_impl(context: Context):
    page = LearningUnitEditPage(driver=context.browser)
    year = current_academic_year().year + 1
    page.anac = str(AcademicYear.objects.get(year=year))


@step("Cliquer sur le bouton « Enregistrer »")
def step_impl(context: Context):
    page = LearningUnitEditPage(driver=context.browser)
    page.save_button.click()


@step("Cliquer sur le bouton « Enregistrer » de la création")
def step_impl(context: Context):
    page = NewLearningUnitPage(driver=context.browser)
    page.save_button.click()


@step("Cliquer sur le bouton « Enregistrer » pour partim")
def step_impl(context: Context):
    page = NewPartimPage(driver=context.browser)
    page.save_button.click()


@step("A la question, « voulez-vous reporter » répondez « non »")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    page = LearningUnitEditPage(driver=context.browser)
    page.no_postponement.click()


@given("La période de modification des programmes n’est pas en cours")
def step_impl(context: Context):
    calendar = AcademicCalendar.objects.filter(academic_year=current_academic_year(),
                                               reference=EDUCATION_GROUP_EDITION).first()
    if calendar:
        calendar.end_date = (datetime.now() - timedelta(days=1)).date()
        calendar.save()


@step("A la question, « voulez-vous reporter » répondez « oui »")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    page = LearningUnitEditPage(driver=context.browser)
    context.current_page = page.with_postponement.click()


@step("Rechercher la même UE dans une année supérieure")
def step_impl(context: Context):
    luy = LearningUnitYear.objects.filter(
        learning_unit=context.learning_unit_year.learning_unit,
        academic_year__year__gt=context.learning_unit_year.academic_year.year
    ).first()
    url = reverse('learning_unit', args=[luy.pk])

    LearningUnitPage(driver=context.browser, base_url=context.get_url(url)).open()


@step("Cliquer sur le menu « Nouveau partim »")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    page = LearningUnitPage(driver=context.browser)
    context.current_page = page.new_partim.click()


@then("Vérifier que l'UE a bien été créé")
def step_impl(context):
    page = LearningUnitPage(context.browser, context.browser.current_url)
    context.test.assertEqual(page.code.text, context.form_data["code"])


@then("Vérifier que le partim a bien été créé")
def step_impl(context):
    page = LearningUnitPage(context.browser, context.browser.current_url)
    context.test.assertEqual(page.code.text[-1], context.form_data["partim_code"])


@when("Cliquer sur le lien {acronym}")
def step_impl(context: Context, acronym: str):
    page = LearningUnitPage(driver=context.browser)
    page.go_to_full.click()

    page = LearningUnitPage(context.browser, context.browser.current_url)
    page.wait_for_page_to_load()


@step("Cliquer sur le menu « Nouvelle UE »")
def step_impl(context: Context):
    page = SearchLearningUnitPage(driver=context.browser)
    page.new_luy.click()


@step("les flags d'éditions des UEs sont désactivés.")
def step_impl(context: Context):
    Flag.objects.update_or_create(name='learning_achievement_update', defaults={"authenticated": True})
    Flag.objects.update_or_create(name='learning_unit_create', defaults={"authenticated": True})
    Flag.objects.update_or_create(name='learning_unit_proposal_create', defaults={"authenticated": True})
