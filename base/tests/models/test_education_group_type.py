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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.test import TestCase

from base.models.education_group_type import find_authorized_types
from base.models.enums import education_group_categories
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from django.test.utils import override_settings


class TestAuthorizedTypes(TestCase):
    """Unit tests on find_authorized_types()"""
    def setUp(self):
        self.category = education_group_categories.GROUP

        self.access_contest = EducationGroupTypeFactory(name='ACCESS_CONTEST', category=self.category)
        self.bachelor = EducationGroupTypeFactory(name='BACHELOR', category=self.category)
        self.master_60 = EducationGroupTypeFactory(name='MASTER_60', category=self.category)

    @override_settings(LANGUAGES=[('fr-be', 'French'), ('en', 'English'), ], LANGUAGE_CODE='fr-be')
    def test_ordered_by_name_fr(self):
        # Considering that translations stay similar to
        #
        # ACCESS_CONTEST = Concours d’accès
        # BACHELOR = Bachelier
        # MASTER_60 = Master 60

        EducationGroupTypeFactory(category=education_group_categories.TRAINING)
        expected_result = [self.bachelor, self.access_contest, self.master_60]
        self.assertEqual(expected_result, list(find_authorized_types(category=self.category)))

    @override_settings(LANGUAGES=[('fr-be', 'French'), ('en', 'English'), ], LANGUAGE_CODE='en')
    def test_ordered_by_name_en(self):
        # Considering that translations stay similar to
        #
        # ACCESS_CONTEST = Access contest
        # BACHELOR = Bachelor
        # MASTER_60 = Master 60
        EducationGroupTypeFactory(category=education_group_categories.TRAINING)
        expected_result = [self.access_contest, self.bachelor, self.master_60]
        self.assertEqual(expected_result, list(find_authorized_types(category=self.category)))

    def test_filter_on_authorized_types(self):
        doctorate = EducationGroupTypeFactory(name='PhD', category=education_group_categories.TRAINING)
        AuthorizedRelationshipFactory(parent_type=doctorate, child_type=self.master_60)
        educ_group_year = EducationGroupYearFactory(education_group_type=doctorate)
        result = find_authorized_types(parents=[educ_group_year])
        self.assertEqual(len(result), 1)
        self.assertIn(self.master_60, result)
        self.assertNotIn(self.access_contest, result)
        self.assertNotIn(self.bachelor, result)

    def test_when_no_authorized_type_matches(self):
        AuthorizedRelationshipFactory(parent_type=self.bachelor, child_type=self.master_60)
        AuthorizedRelationshipFactory(parent_type=self.master_60, child_type=self.access_contest)
        educ_group_year = EducationGroupYearFactory(education_group_type=self.access_contest)
        result = find_authorized_types(parents=[educ_group_year])
        self.assertEqual(result.count(), 0)
