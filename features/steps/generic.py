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
from datetime import timedelta, datetime

from behave import *
from behave.runner import Context
from django.contrib.auth.models import Group

from base.business.learning_unit_proposal import copy_learning_unit_data
from base.models.academic_calendar import AcademicCalendar
from base.models.academic_year import AcademicYear, current_academic_year
from base.models.campus import Campus
from base.models.entity import Entity
from base.models.enums.academic_calendar_type import EDUCATION_GROUP_EDITION
from base.models.enums.groups import FACULTY_MANAGER_GROUP, CENTRAL_MANAGER_GROUP
from base.models.enums.proposal_state import ProposalState
from base.models.enums.proposal_type import ProposalType
from base.models.learning_unit import LearningUnit
from base.models.learning_unit_year import LearningUnitYear
from base.models.person_entity import PersonEntity
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory, LearningUnitYearFullFactory
from base.tests.factories.person import FacultyManagerForUEFactory, PersonFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from base.tests.functionals.test_education_group import LoginPage
from base.tests.factories.person import PersonWithPermissionsFactory

use_step_matcher("parse")


@given("La base de données est dans son état initial.")
def step_impl(context: Context):
    # TODO: Should be done in the real env.
    pass


@step("L'utilisateur est loggé en tant que gestionnaire facultaire ou central")
def step_impl(context: Context):
    context.user = FacultyManagerForUEFactory(
        user__username="usual_suspect",
        user__first_name="Keyser",
        user__last_name="Söze",
        user__password="Roger_Verbal_Kint").user

    page = LoginPage(driver=context.browser, base_url=context.get_url('/login/')).open()
    page.login("usual_suspect", 'Roger_Verbal_Kint')

    context.test.assertEqual(context.browser.current_url, context.get_url('/'))


@step("L'utilisateur est loggé en tant que {group}.")
def step_impl(context: Context, group):
    user = PersonFactory(
        user__username="usual_suspect",
        user__first_name="Keyser",
        user__last_name="Söze",
        user__password="Roger_Verbal_Kint").user

    user.groups.clear()

    if group.lower() == 'gestionnaire factulaire':
        user.groups.add(Group.objects.get(name=FACULTY_MANAGER_GROUP))
    elif group.lower() in ('gestionnaire central', 'central manager'):
        user.groups.add(Group.objects.get(name=CENTRAL_MANAGER_GROUP))
    elif group.lower() == "gestionnaire d'institution":
        user.groups.add(Group.objects.get(name="institution_administration"))

    user.save()

    context.user = user

    page = LoginPage(driver=context.browser, base_url=context.get_url('/login/')).open()
    page.login("usual_suspect", 'Roger_Verbal_Kint')

    context.test.assertEqual(context.browser.current_url, context.get_url('/'))


@step("{acronym} est en proposition en {year} lié à {entity}")
def step_impl(context, acronym, year, entity):
    ac = AcademicYear.objects.get(year=year[:4])
    luy = LearningUnitYearFactory(acronym=acronym, academic_year=ac)
    entity = Entity.objects.filter(entityversion__acronym=entity).last()
    ProposalLearningUnitFactory(learning_unit_year=luy,
                                entity=entity,
                                folder_id=12)


@step("La période de modification des programmes est en cours")
def step_impl(context: Context):
    calendar = AcademicCalendarFactory(academic_year=current_academic_year(), reference=EDUCATION_GROUP_EDITION)
    calendar.end_date = (datetime.now() + timedelta(days=1)).date()
    calendar.save()


@step("L’utilisateur est dans le groupe {group}")
def step_impl(context: Context, group):
    person = PersonFactory(
        user__username="usual_suspect",
        user__first_name="Keyser",
        user__last_name="Söze",
        user__password="Roger_Verbal_Kint",
    )

    person.user.groups.clear()

    if group.lower() in ('gestionnaire factulaire', 'faculty manager'):
        person.user.groups.add(Group.objects.get(name=FACULTY_MANAGER_GROUP))
    elif group.lower() in ('gestionnaire central', 'central manager'):
        person.user.groups.add(Group.objects.get(name=CENTRAL_MANAGER_GROUP))

    person.user.save()

    context.user = person.user

    page = LoginPage(driver=context.browser, base_url=context.get_url('/login/')).open()
    page.login("usual_suspect", 'Roger_Verbal_Kint')

    context.test.assertEqual(context.browser.current_url, context.get_url('/'))


@step("L’utilisateur est attaché à l’entité {value}")
def step_impl(context: Context, value: str):
    entity = Entity.objects.filter(entityversion__acronym=value).first()
    PersonEntity.objects.get_or_create(person=context.user.person, entity=entity, defaults={'with_child': True})


@given("S’assurer que la date de fin de {acronym} est {year}.")
def step_impl(context, acronym, year):
    lu = LearningUnit.objects.filter(learningunityear__acronym=acronym).first()
    lu.end_year = int(year[:4])
    lu.save()


@given("L'ue {acronym} en {year} et liée à {entity} est en proposition de création")
def step_impl(context, acronym, year, entity):
    campus = Campus.objects.filter(organization__type='MAIN').first()

    e = Entity.objects.filter(entityversion__acronym=entity).first()
    luy = LearningUnitYearFullFactory(
        acronym=acronym,
        campus=campus,
        academic_year=AcademicYear.objects.get(year=year[:4]),
        internship_subtype=None,
        learning_container_year__requirement_entity=e,
        learning_container_year__allocation_entity=e,
    )

    ProposalLearningUnitFactory(
        learning_unit_year=luy,
        type=ProposalType.CREATION.name,
        state=ProposalState.FACULTY.name,
        entity=e,
    )


@given("L'ue {acronym} en {year} et liée à {entity} est en proposition de modification")
def step_impl(context, acronym, year, entity):
    luy = LearningUnitYear.objects.get(acronym=acronym, academic_year__year=year[:4])
    e = Entity.objects.filter(entityversion__acronym=entity).first()

    ProposalLearningUnitFactory(
        learning_unit_year=luy,
        type=ProposalType.MODIFICATION.name,
        state=ProposalState.FACULTY.name,
        entity=e,
        initial_data=copy_learning_unit_data(luy)
    )


@given("L'ue {acronym} en {year} et liée à {entity} est en proposition de suppression")
def step_impl(context, acronym, year, entity):
    luy = LearningUnitYear.objects.get(acronym=acronym, academic_year__year=year[:4])
    e = Entity.objects.filter(entityversion__acronym=entity).first()

    ProposalLearningUnitFactory(
        learning_unit_year=luy,
        type=ProposalType.SUPPRESSION.name,
        state=ProposalState.FACULTY.name,
        entity=e,
        initial_data=copy_learning_unit_data(luy)
    )


@step("Encoder la valeur {search_value} dans la zone de saisie {search_field}")
def step_impl(context: Context, search_value: str, search_field: str):
    setattr(context.current_page, search_field, search_value)


@step("L'utilisateur a la permission {permission}.")
def step_impl(context: Context, permission: str):
    """
    :type context behave.runner.Context
    """
    user = PersonWithPermissionsFactory(
        permission,
        user__username="usual_suspect",
        user__first_name="Keyser",
        user__last_name="Söze",
        user__password="Roger_Verbal_Kint",
    ).user
    user.groups.clear()

    user.save()
    context.user = user

    page = LoginPage(driver=context.browser, base_url=context.get_url('/login/')).open()
    page.login("usual_suspect", 'Roger_Verbal_Kint')

    context.test.assertEqual(context.browser.current_url, context.get_url('/'))
