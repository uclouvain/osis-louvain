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

from django.contrib.auth.models import Permission
from django.test import TestCase

from base.business.education_groups.perms import is_academic_calendar_opened, check_permission, \
    check_authorized_type, is_eligible_to_edit_general_information
from base.models.enums import academic_calendar_type
from base.models.enums.education_group_categories import TRAINING
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.person import PersonFactory, PersonWithPermissionsFactory, CentralManagerFactory


class TestPerms(TestCase):
    def test_has_person_the_right_to_add_education_group(self):
        person_without_right = PersonFactory()
        self.assertFalse(check_permission(person_without_right, "base.add_educationgroup"))

        person_with_right = PersonWithPermissionsFactory("add_educationgroup")
        self.assertTrue(check_permission(person_with_right, "base.add_educationgroup"))

    def test_is_education_group_creation_period_opened(self):
        person = PersonFactory()
        education_group = EducationGroupYearFactory()
        today = datetime.date.today()

        current_ac = create_current_academic_year()

        closed_period = AcademicCalendarFactory(start_date=today + datetime.timedelta(days=1),
                                                end_date=today + datetime.timedelta(days=3),
                                                academic_year=current_ac,
                                                reference=academic_calendar_type.EDUCATION_GROUP_EDITION)

        next_ac = AcademicYearFactory(year=current_ac.year + 1)

        # The period is closed
        self.assertFalse(
            is_academic_calendar_opened(
                education_group,
                academic_calendar_type.EDUCATION_GROUP_EDITION
            )
        )

        opened_period = closed_period
        opened_period.start_date = today
        opened_period.save()

        # It is open the academic_year does not match
        self.assertFalse(
            is_academic_calendar_opened(
                education_group,
                academic_calendar_type.EDUCATION_GROUP_EDITION
            )
        )

        # It is open and the education_group is in N+1 academic_year
        education_group.academic_year = next_ac
        education_group.save()
        self.assertTrue(
            is_academic_calendar_opened(
                education_group,
                academic_calendar_type.EDUCATION_GROUP_EDITION,
                raise_exception=True
            )
        )

    def is_person_central_manager(self):
        person = PersonFactory()
        self.assertFalse(person.is_central_manager())

        central_manager = CentralManagerFactory()
        self.assertTrue(central_manager.is_central_manager())

    def test_check_unauthorized_type(self):
        education_group = EducationGroupYearFactory()
        result = check_authorized_type(education_group, TRAINING)
        self.assertFalse(result)

    def test_check_authorized_type(self):
        education_group = EducationGroupYearFactory()
        AuthorizedRelationshipFactory(parent_type=education_group.education_group_type)
        result = check_authorized_type(education_group, TRAINING)
        self.assertTrue(result)

    def test_check_authorized_type_without_parent(self):
        result = check_authorized_type(None, TRAINING)
        self.assertTrue(result)

    def test_is_education_group_general_information_edit_period_opened(self):
        person = PersonFactory()
        education_group = EducationGroupYearFactory()
        today = datetime.date.today()

        current_ac = create_current_academic_year()

        closed_period = AcademicCalendarFactory(
            start_date=today + datetime.timedelta(days=1),
            end_date=today + datetime.timedelta(days=3),
            academic_year=current_ac,
            reference=academic_calendar_type.EDUCATION_GROUP_EDITION,
        )

        next_ac = AcademicYearFactory(year=current_ac.year + 1)

        # The period is closed
        self.assertFalse(
            is_academic_calendar_opened(
                education_group,
                academic_calendar_type.EDUCATION_GROUP_EDITION
            )
        )

        opened_period = closed_period
        opened_period.start_date = today
        opened_period.save()

        # It is open the academic_year does not match
        self.assertFalse(
            is_academic_calendar_opened(
                education_group,
                academic_calendar_type.EDUCATION_GROUP_EDITION
            )
        )

        # It is open and the education_group is in N+1 academic_year
        education_group.academic_year = next_ac
        education_group.save()
        self.assertTrue(
            is_academic_calendar_opened(
                education_group,
                academic_calendar_type.EDUCATION_GROUP_EDITION,
                raise_exception=True
            )
        )

    def test_is_eligible_to_edit_common_offer_as_central_manager(self):
        person = CentralManagerFactory()
        person.user.user_permissions.add(Permission.objects.get(codename="can_edit_educationgroup_pedagogy"))
        education_group = EducationGroupYearFactory(acronym="common-1ba")
        self.assertTrue(is_eligible_to_edit_general_information(person, education_group))
