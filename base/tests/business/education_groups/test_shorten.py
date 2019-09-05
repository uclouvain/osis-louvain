##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.safestring import mark_safe
from django.utils.translation import ngettext_lazy, ugettext_lazy as _

from base.business.education_groups import shorten
from base.business.education_groups.shorten import _get_formated_error_msg, check_education_group_end_date
from base.models.education_group_year import EducationGroupYear
from base.models.enums import entity_type
from base.models.enums import organization_type
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.business.learning_units import GenerateAcademicYear
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.offer_enrollment import OfferEnrollmentFactory


class EducationGroupShortenContext(TestCase):
    """This class is used in this test file in order to setup an environment for testing EGY SHORTEN"""
    def setUp(self):
        # Create several academic year
        self.current_academic_year = create_current_academic_year()
        self.generated_ac_years = GenerateAcademicYear(self.current_academic_year.year + 1,
                                                       self.current_academic_year.year + 10)
        # Create small entities
        self.entity = EntityFactory(organization__type=organization_type.MAIN)
        self.entity_version = EntityVersionFactory(
            entity=self.entity,
            entity_type=entity_type.SECTOR
        )

        self.education_group_year = EducationGroupYearFactory(
            management_entity=self.entity,
            administration_entity=self.entity,
            academic_year=self.current_academic_year
        )


class TestStartShortenEducationGroupYear(EducationGroupShortenContext):
    def test_start_shorten_case_no_deletion(self):
        # Remove all in the future
        EducationGroupYear.objects.filter(
            education_group=self.education_group_year.education_group,
            academic_year__year__gt=self.current_academic_year.year
        ).delete()

        result = shorten.start(self.education_group_year.education_group, self.current_academic_year)
        self.assertIsInstance(result, list)
        self.assertFalse(result)

    def test_start_shorten_case_multiple_deletion(self):
        # Insert multiple in future
        for ac_year in self.generated_ac_years.academic_years:
            EducationGroupYearFactory(
                education_group=self.education_group_year.education_group,
                management_entity=self.entity,
                administration_entity=self.entity,
                academic_year=ac_year,
            )

        result = shorten.start(self.education_group_year.education_group, self.current_academic_year)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 10)
        # Ensure that the order is by academic_year.year
        for idx, ac_year in enumerate(self.generated_ac_years.academic_years):
            self.assertEqual(result[idx].academic_year, ac_year)

        # Ensure that data doesn't exist anymore
        self.assertFalse(EducationGroupYear.objects.filter(
            education_group=self.education_group_year.education_group,
            academic_year__year__gt=self.current_academic_year.year
        ).count())


class TestGetProtectedMessageEducationGroupYear(EducationGroupShortenContext):
    def test_get_protected_messages_without_any_protected_datas(self):
        edy = EducationGroupYearFactory(
            education_group=self.education_group_year.education_group,
            management_entity=self.entity,
            administration_entity=self.entity,
            academic_year=self.generated_ac_years.academic_years[0],
        )
        protected_messages = shorten._get_protected_messages([edy])
        self.assertFalse(protected_messages)

    def test_get_protected_messages_with_protected_datas(self):
        # Insert multiple in future with protected datas
        all_edy = []
        for ac_year in self.generated_ac_years.academic_years:
            edy = EducationGroupYearFactory(
                education_group=self.education_group_year.education_group,
                management_entity=self.entity,
                administration_entity=self.entity,
                academic_year=ac_year,
            )
            # Protected data [Offer enrollment]
            OfferEnrollmentFactory(education_group_year=edy)
            all_edy.append(edy)

        protected_messages = shorten._get_protected_messages(all_edy)
        self.assertIsInstance(protected_messages, list)
        self.assertEqual(len(protected_messages), 10)

        # Ensure that the order of protected messages is by academic_year.year + Message expected
        count_enrollment = 1
        msg_expected = [
            ngettext_lazy(
                "%(count_enrollment)d student is enrolled in the offer.",
                "%(count_enrollment)d students are enrolled in the offer.",
                count_enrollment
            ) % {"count_enrollment": count_enrollment}
        ]
        for idx, ac_year in enumerate(self.generated_ac_years.academic_years):
            protected_message = protected_messages
            self.assertEqual(protected_message[idx]['education_group_year'].academic_year, ac_year)
            self.assertEqual(protected_message[idx]['messages'], msg_expected)

    def test_get_protected_messages_linked_with_epc(self):
        edy = EducationGroupYearFactory(
            education_group=self.education_group_year.education_group,
            management_entity=self.entity,
            administration_entity=self.entity,
            academic_year=self.generated_ac_years.academic_years[0],
            linked_with_epc=True
        )
        protected_messages = shorten._get_protected_messages([edy])
        self.assertEqual(protected_messages[0]['messages'][0], _('Linked with EPC'))


class TestGetFormatedErrorMessage(EducationGroupShortenContext):
    def test_get_formated_error_msg(self):
        protected_messages = [
            {
                'education_group_year': self.education_group_year,
                'messages': ['message 1', 'message 2', 'message 3']
            }
        ]
        end_year = 2015
        expected_msg = _("Cannot set end year to %(end_year)s :") % {'end_year': end_year}
        expected_msg += "<ul><li> {education_group_year} : {msg_str} </li></ul>".format(
            education_group_year=self.education_group_year,
            msg_str=", ".join(protected_messages[0]['messages'])
        )

        error_msg = _get_formated_error_msg(end_year, protected_messages)
        self.assertEqual(error_msg, mark_safe(expected_msg))


class TestCheckEducationGroupEndDate(EducationGroupShortenContext):
    def setUp(self):
        super().setUp()
        self.ac_year_in_future = self.generated_ac_years.academic_years[0]

    def test_check_education_group_end_date_valid_case(self):
        self.assertTrue(check_education_group_end_date(
            education_group=self.education_group_year.education_group,
            end_year=self.ac_year_in_future
        ))

    def test_check_education_group_end_date_with_protected_data(self):
        edy = EducationGroupYearFactory(
            education_group=self.education_group_year.education_group,
            management_entity=self.entity,
            administration_entity=self.entity,
            academic_year=self.ac_year_in_future,
        )
        # Protected data [Offer enrollment]
        OfferEnrollmentFactory(education_group_year=edy)
        previous_academic_year = AcademicYearFactory(year=self.ac_year_in_future.year-1)

        with self.assertRaises(ValidationError):
            check_education_group_end_date(
                education_group=self.education_group_year.education_group,
                end_year=previous_academic_year
            )
