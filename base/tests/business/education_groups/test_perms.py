##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
##############################################################################
import datetime

from django.test import TestCase

from base.business.education_groups.perms import has_person_the_right_to_add_education_group, \
    is_education_group_creation_period_opened, is_central_manager
from base.models.enums import academic_calendar_type
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.person import PersonFactory, PersonWithPermissionsFactory, PersonWithGroupsFactory, \
    CentralManagerFactory


class TestPerms(TestCase):
    def test_has_person_the_right_to_add_education_group(self):
        person_without_right = PersonFactory()
        self.assertFalse(has_person_the_right_to_add_education_group(person_without_right))

        person_with_right = PersonWithPermissionsFactory("add_educationgroup")
        self.assertTrue(has_person_the_right_to_add_education_group(person_with_right))

    def test_is_education_group_creation_period_opened(self):
        person = PersonFactory()
        today = datetime.date.today()

        closed_period = AcademicCalendarFactory(start_date=today + datetime.timedelta(days=1),
                                                end_date=today + datetime.timedelta(days=3),
                                                reference=academic_calendar_type.EDUCATION_GROUP_EDITION)

        self.assertFalse(is_education_group_creation_period_opened(person))

        opened_period = closed_period
        opened_period.start_date = today
        opened_period.save()
        self.assertTrue(is_education_group_creation_period_opened(person))

    def is_person_central_manager(self):
        person = PersonFactory()
        self.assertFalse(is_central_manager(person))

        central_manager = CentralManagerFactory()
        self.assertTrue(is_central_manager(central_manager))
