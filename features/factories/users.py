############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
############################################################################
from django.conf import settings
from django.contrib.auth.models import Permission

from base.models.entity import Entity
from base.models.enums import entity_type
from base.tests.factories.person import FacultyManagerForUEFactory, CentralManagerForUEFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.student import StudentFactory
from base.tests.factories.tutor import TutorFactory
from base.tests.factories.user import SuperUserFactory


class UsersGenerator:
    def __init__(self):
        self.superuser = SuperUserFactory()
        self.faculty_manager = BusinessFacultyManagerFactory()
        self.central_manager = BusinessCentralManagerFactory()
        self.tutors = TutorFactory.create_batch(60)
        self.students = StudentFactory.create_batch(100)
        self.program_managers = ProgramManagerFactory.create_batch(
            5,
            offer_year__academic_year__current=True,
            person__language=settings.LANGUAGE_CODE_FR
        )

        perm = Permission.objects.filter(codename="can_access_scoreencoding").first()
        for manager in self.program_managers:
            manager.person.user.user_permissions.add(perm)


PERMISSIONS = (
    'can_access_learningunit',
    'can_edit_learningunit_date',
    'can_edit_learningunit',
    'can_create_learningunit',
    'can_edit_learning_unit_proposal',
    'can_propose_learningunit',
    'can_consolidate_learningunit_proposal',
    'add_educationgroup',
    'change_educationgroup',
    'view_educationgroup'
)


class BusinessFacultyManagerFactory(FacultyManagerForUEFactory):
    def __init__(self, *args, **kwargs):
        permissions = PERMISSIONS
        factory_parameters = {
            "user__username": "faculty_manager",
            "user__first_name": "Faculty",
            "user__last_name": "Manager",
            "user__password": "Faculty_Manager",
            "language": settings.LANGUAGE_CODE_FR
        }

        super().__init__(*permissions, *args, **factory_parameters, **kwargs)
        entity = Entity.objects.filter(entityversion__entity_type=entity_type.SECTOR).order_by("?").first()
        PersonEntityFactory(
            person=self.person,
            entity=entity,
            with_child=True
        )


class BusinessCentralManagerFactory(CentralManagerForUEFactory):
    def __init__(self, *args, **kwargs):
        permissions = PERMISSIONS
        factory_parameters = {
            "user__username": "central_manager",
            "user__first_name": "Central",
            "user__last_name": "Manager",
            "user__password": "Central_Manager",
            "language": settings.LANGUAGE_CODE_FR
        }

        super().__init__(*permissions, *args, **factory_parameters, **kwargs)
        entity = Entity.objects.filter(entityversion__entity_type="").order_by("?").first()
        PersonEntityFactory(
            person=self.person,
            entity=entity,
            with_child=True
        )
