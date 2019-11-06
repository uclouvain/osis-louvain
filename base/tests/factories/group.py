##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import factory

from base.models.enums.groups import FACULTY_MANAGER_GROUP, CENTRAL_MANAGER_GROUP, UE_FACULTY_MANAGER_GROUP, \
    ADMINISTRATIVE_MANAGER_GROUP, ENTITY_MANAGER_GROUP, PROGRAM_MANAGER_GROUP, TUTOR


class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'auth.Group'
        django_get_or_create = ('name',)

    name = ""


class FacultyManagerGroupFactory(GroupFactory):
    name = FACULTY_MANAGER_GROUP


class UEFacultyManagerGroupFactory(GroupFactory):
    name = UE_FACULTY_MANAGER_GROUP


class CentralManagerGroupFactory(GroupFactory):
    name = CENTRAL_MANAGER_GROUP


class TutorGroupFactory(GroupFactory):
    name = TUTOR


class ProgramManagerGroupFactory(GroupFactory):
    name = PROGRAM_MANAGER_GROUP


class EntityManagerGroupFactory(GroupFactory):
    name = ENTITY_MANAGER_GROUP


class AdministrativeManagerGroupFactory(GroupFactory):
    name = ADMINISTRATIVE_MANAGER_GROUP
