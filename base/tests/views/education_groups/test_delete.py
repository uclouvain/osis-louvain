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
from datetime import timedelta

from django.contrib.auth.models import Permission
from django.utils.translation import ugettext_lazy as _
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ngettext_lazy
from waffle.testutils import override_flag

from base.models.education_group import EducationGroup
from base.models.education_group_year import EducationGroupYear
from base.models.enums.academic_calendar_type import EDUCATION_GROUP_EDITION
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.education_group import EducationGroupFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.offer_enrollment import OfferEnrollmentFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory


@override_flag('education_group_delete', active=True)
class TestDeleteGroupEducationView(TestCase):

    def setUp(self):
        current_ac = create_current_academic_year()
        next_ac = AcademicYearFactory(year=current_ac.year + 1)

        self.education_group = EducationGroupFactory()
        self.education_group_year = EducationGroupYearFactory(education_group=self.education_group,
                                                              academic_year=next_ac)
        self.education_group_year2 = EducationGroupYearFactory(education_group=self.education_group,
                                                               academic_year=next_ac)
        self.person = PersonFactory()
        PersonEntityFactory(person=self.person, entity=self.education_group_year.management_entity)
        PersonEntityFactory(person=self.person, entity=self.education_group_year2.management_entity)

        self.url = reverse('delete_education_group', args=[self.education_group_year.id,
                                                           self.education_group_year.education_group.id])

        self.person.user.user_permissions.add(Permission.objects.get(codename="delete_educationgroup"))
        self.client.force_login(user=self.person.user)

        self.academic_calendar = AcademicCalendarFactory(
            reference=EDUCATION_GROUP_EDITION,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(weeks=+1),
            academic_year=current_ac,
        )

    def test_delete_get_permission_denied(self):
        self.person.user.user_permissions.remove(Permission.objects.get(codename="delete_educationgroup"))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_delete_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["protected_messages"], [])
        self.assertTemplateUsed(response, "education_group/delete.html")

    def test_delete_post(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(EducationGroupYear.objects.filter(pk=self.education_group_year.pk).exists())
        self.assertFalse(EducationGroupYear.objects.filter(pk=self.education_group_year2.pk).exists())
        self.assertFalse(EducationGroup.objects.filter(pk=self.education_group.pk).exists())

    def test_delete_get_with_protected_objects(self):
        # Create protected data
        OfferEnrollmentFactory(education_group_year=self.education_group_year)
        GroupElementYearFactory(parent=self.education_group_year)
        GroupElementYearFactory(parent=self.education_group_year)

        count_enrollment = 1
        msg_offer_enrollment = ngettext_lazy(
            "%(count_enrollment)d student is enrolled in the offer.",
            "%(count_enrollment)d students are enrolled in the offer.",
            count_enrollment
        ) % {"count_enrollment": count_enrollment}
        msg_pgrm_content = _("The content of the education group is not empty.")

        protected_messages = [
            {
                'education_group_year': self.education_group_year,
                'messages': [
                    msg_offer_enrollment,
                    msg_pgrm_content
                ]
            }
        ]
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["protected_messages"], protected_messages)
        self.assertTemplateUsed(response, "education_group/protect_delete.html")
