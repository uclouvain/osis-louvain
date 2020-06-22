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
from datetime import timedelta, datetime

from behave import *
from behave.runner import Context
from django.contrib.auth.models import Group

from base.models.academic_year import current_academic_year
from base.models.entity import Entity
from base.models.enums.academic_calendar_type import EDUCATION_GROUP_EDITION, LEARNING_UNIT_EDITION_FACULTY_MANAGERS, \
    LEARNING_UNIT_EDITION_CENTRAL_MANAGERS
from base.models.enums.groups import FACULTY_MANAGER_GROUP, CENTRAL_MANAGER_GROUP
from base.models.learning_unit import LearningUnit
from base.models.person_entity import PersonEntity
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.person import FacultyManagerForUEFactory, CentralManagerForUEFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person import PersonWithPermissionsFactory
from features.pages.common import LoginPage

use_step_matcher("parse")


@given("La base de données est dans son état initial.")
def step_impl(context: Context):
    # TODO: Should be done in the real env.
    pass


@step("L'utilisateur est loggé en tant que gestionnaire facultaire")
def step_impl(context: Context):
    context.user = context.data.faculty_manager.user

    page = LoginPage(driver=context.browser, base_url=context.get_url('/login/')).open()
    page.login("faculty_manager", 'Faculty_Manager')

    context.test.assertEqual(context.browser.current_url, context.get_url('/'))


@step("L'utilisateur est loggé en tant que gestionnaire central")
def step_impl(context: Context):
    context.user = context.data.central_manager.user

    page = LoginPage(driver=context.browser, base_url=context.get_url('/login/')).open()
    page.login("central_manager", 'Central_Manager')

    context.test.assertEqual(context.browser.current_url, context.get_url('/'))


@step("L'utilisateur est loggé en tant que gestionnaire")
def step_impl(context: Context):
    manager_factory = random.choice([FacultyManagerForUEFactory, CentralManagerForUEFactory])
    context.user = manager_factory(
        'can_access_learningunit',
        'can_edit_learningunit_date',
        'can_edit_learningunit',
        'can_create_learningunit',
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


@step("La période de modification des programmes est en cours")
def step_impl(context: Context):
    calendar = AcademicCalendarFactory(academic_year=current_academic_year(), reference=EDUCATION_GROUP_EDITION)
    calendar.end_date = (datetime.now() + timedelta(days=1)).date()
    calendar.save()


@step("La période de modification des unités d'enseignement est en cours")
def step_impl(context: Context):
    calendar = AcademicCalendarFactory(
        academic_year=current_academic_year(),
        data_year=current_academic_year(),
        reference=LEARNING_UNIT_EDITION_FACULTY_MANAGERS)
    calendar.end_date = (datetime.now() + timedelta(days=1)).date()

    calendar.save()
    calendar = AcademicCalendarFactory(
        academic_year=current_academic_year(),
        data_year=current_academic_year(),
        reference=LEARNING_UNIT_EDITION_CENTRAL_MANAGERS)
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
        person.user.groups.add(Group.objects.get_or_create(name=FACULTY_MANAGER_GROUP)[0])
    elif group.lower() in ('gestionnaire central', 'central manager'):
        person.user.groups.add(Group.objects.get_or_create(name=CENTRAL_MANAGER_GROUP)[0])

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
