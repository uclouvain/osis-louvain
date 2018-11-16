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
from unittest import mock
from unittest.mock import Mock

from django.db import Error
from django.test import TestCase

from base.business.education_groups.automatic_postponement import EducationGroupAutomaticPostponement
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_categories import MINI_TRAINING
from base.models.enums.education_group_types import OPTION
from base.tests.factories.academic_year import AcademicYearFactory, get_current_year
from base.tests.factories.education_group import EducationGroupFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory


class TestFetchEducationGroupToPostpone(TestCase):
    def setUp(self):
        current_year = get_current_year()
        self.academic_years = [AcademicYearFactory(year=i) for i in range(current_year, current_year + 7)]
        self.education_group = EducationGroupFactory(end_year=None)

    def test_fetch_education_group_to_postpone_to_N6(self):
        EducationGroupYearFactory(
            education_group=self.education_group,
            academic_year=self.academic_years[-2],
        )

        self.assertEqual(EducationGroupYear.objects.count(), 1)
        result, errors = EducationGroupAutomaticPostponement().postpone()
        self.assertEqual(len(result), 1)
        self.assertFalse(errors)

    def test_egy_to_not_duplicated(self):
        # The learning unit is over
        self.education_group.end_year = self.academic_years[-2].year
        self.education_group.save()

        EducationGroupYearFactory(
            education_group=self.education_group,
            academic_year=self.academic_years[-2],
        )
        self.assertEqual(EducationGroupYear.objects.count(), 1)
        result, errors = EducationGroupAutomaticPostponement().postpone()
        self.assertEqual(len(result), 0)
        self.assertFalse(errors)

    def test_egy_already_duplicated(self):
        EducationGroupYearFactory(
            education_group=self.education_group,
            academic_year=self.academic_years[-2],
        )
        EducationGroupYearFactory(
            education_group=self.education_group,
            academic_year=self.academic_years[-1],
        )
        self.assertEqual(EducationGroupYear.objects.count(), 2)
        result, errors = EducationGroupAutomaticPostponement().postpone()
        self.assertEqual(len(result), 0)
        self.assertFalse(errors)

    @mock.patch('base.business.education_groups.automatic_postponement.EducationGroupAutomaticPostponement.extend_obj')
    def test_egy_to_duplicate_with_error(self, mock_method):
        mock_method.side_effect = Mock(side_effect=Error("test error"))

        egy_with_error = EducationGroupYearFactory(
            education_group=self.education_group,
            academic_year=self.academic_years[-2],
        )
        self.assertEqual(EducationGroupYear.objects.count(), 1)

        result, errors = EducationGroupAutomaticPostponement().postpone()
        self.assertTrue(mock_method.called)
        self.assertEqual(errors, [egy_with_error])
        self.assertEqual(len(result), 0)

    def test_education_group_wrong_mini_training(self):
        egt = EducationGroupTypeFactory(name=OPTION, category=MINI_TRAINING)
        EducationGroupYearFactory(
            education_group=self.education_group,
            academic_year=self.academic_years[-2],
            education_group_type=egt
        )
        queryset = EducationGroupAutomaticPostponement().get_queryset()

        self.assertQuerysetEqual(queryset, [])


class TestSerializePostponement(TestCase):
    @classmethod
    def setUpTestData(cls):
        current_year = get_current_year()
        cls.academic_years = [AcademicYearFactory(year=i) for i in range(current_year, current_year + 7)]
        cls.egys = [EducationGroupYearFactory() for _ in range(10)]

    def test_empty_results_and_errors(self):
        result_dict = EducationGroupAutomaticPostponement().serialize_postponement_results()
        self.assertDictEqual(result_dict, {
            "msg": EducationGroupAutomaticPostponement.msg_result % {
                "number_extended": 0,
                "number_error": 0
            },
            "errors": []
        })

    def test_empty_errors(self):
        postponement = EducationGroupAutomaticPostponement()

        postponement.result = self.egys

        result_dict = postponement.serialize_postponement_results()
        self.assertDictEqual(result_dict, {
            "msg": postponement.msg_result % {
                "number_extended": len(self.egys),
                "number_error": 0
            },
            "errors": []
        })

    def test_with_errors_and_results(self):
        postponement = EducationGroupAutomaticPostponement()
        postponement.result = self.egys[:5]
        postponement.errors = [str(egy) for egy in self.egys[5:]]
        result_dict = postponement.serialize_postponement_results()
        self.assertDictEqual(result_dict, {
            "msg": postponement.msg_result % {
                "number_extended": len(self.egys[:5]),
                "number_error": len(self.egys[5:])
            },
            "errors": [str(egy) for egy in self.egys[5:]]
        })
