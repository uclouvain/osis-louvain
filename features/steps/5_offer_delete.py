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
from selenium.webdriver.common.by import By

from base.business.education_groups.create import create_initial_group_element_year_structure
from base.models.campus import Campus
from base.models.education_group_type import EducationGroupType
from base.models.entity import Entity
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.education_group_year import TrainingFactory
from features.pages.education_group.pages import SearchEducationGroupPage, EducationGroupPage

use_step_matcher("parse")


@step("La formation {acronym} doit exister en {year}")
def step_impl(context, acronym, year):
    """
    :type context: behave.runner.Context
    """
    entity = Entity.objects.filter(entityversion__acronym='DRT').first()
    campus = Campus.objects.filter(organization__type='MAIN').first()

    training = TrainingFactory(
        acronym=acronym,
        partial_acronym='LDROI200S',
        education_group_type=EducationGroupType.objects.get(name=TrainingType.MASTER_MS_120.name),
        academic_year__year=int(year),
        management_entity=entity,
        administration_entity=entity,
        enrollment_campus=campus,
        main_teaching_campus=campus,
        title='Master [120] en , à finalité spécialisée'

    )
    create_initial_group_element_year_structure([training])


@step("Cliquer sur le premier sigle dans la liste de résultats")
def step_impl(context: Context):
    page = SearchEducationGroupPage(driver=context.browser)
    context.offer_to_delete = page.first_row.text
    page.first_row.click()


@step("Cliquer sur « Supprimer »")
def step_impl(context: Context):
    page = EducationGroupPage(driver=context.browser)
    page.delete.click()


@then("Vérifier que l'offre n'apparaît plus dans la liste")
def step_impl(context: Context):
    page = SearchEducationGroupPage(driver=context.browser)
    context.test.assertNotEqual(page.first_row.text, context.offer_to_delete)
