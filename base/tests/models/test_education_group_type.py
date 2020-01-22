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
import json

from django.core import serializers
from django.test import TestCase

from base.models.education_group_type import find_authorized_types
from base.models.enums import education_group_categories
from base.models.enums import education_group_types
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory


class TestAuthorizedTypes(TestCase):
    """Unit tests on find_authorized_types()"""
    @classmethod
    def setUpTestData(cls):
        cls.category = education_group_categories.GROUP

        cls.subgroup = EducationGroupTypeFactory(name='Subgroup', category=cls.category)
        cls.complementary_module = EducationGroupTypeFactory(name='Complementary module', category=cls.category)
        cls.options_list = EducationGroupTypeFactory(name='Options list', category=cls.category)

    def test_ordered_by_name(self):
        EducationGroupTypeFactory(category=education_group_categories.TRAINING)
        expected_result = [self.complementary_module, self.options_list, self.subgroup]
        self.assertEqual(expected_result, list(find_authorized_types(category=self.category)))

    def test_filter_on_authorized_types(self):
        doctorate = EducationGroupTypeFactory(name='PhD', category=education_group_categories.TRAINING)
        AuthorizedRelationshipFactory(parent_type=doctorate, child_type=self.options_list)
        educ_group_year = EducationGroupYearFactory(education_group_type=doctorate)
        result = find_authorized_types(parents=[educ_group_year])
        self.assertEqual(len(result), 1)
        self.assertIn(self.options_list, result)
        self.assertNotIn(self.subgroup, result)
        self.assertNotIn(self.complementary_module, result)

    def test_when_no_authorized_type_matches(self):
        AuthorizedRelationshipFactory(parent_type=self.complementary_module, child_type=self.options_list)
        AuthorizedRelationshipFactory(parent_type=self.options_list, child_type=self.subgroup)
        educ_group_year = EducationGroupYearFactory(education_group_type=self.subgroup)
        result = find_authorized_types(parents=[educ_group_year])
        self.assertEqual(result.count(), 0)

    def test_natural_key(self):
        an_education_group_type = EducationGroupTypeFactory(name=education_group_types.TrainingType.AGGREGATION.name)
        self.assertEqual(an_education_group_type.natural_key(), (education_group_types.TrainingType.AGGREGATION.name,))

    def test_dump_authorized(self):
        an_authorized_relation_ship = AuthorizedRelationshipFactory(
            parent_type=EducationGroupTypeFactory(name=education_group_types.TrainingType.AGGREGATION.name),
            child_type=EducationGroupTypeFactory(name=education_group_types.TrainingType.CERTIFICATE.name)
        )
        dump_data_alike = serializers.serialize(
            'json',
            [
                an_authorized_relation_ship,
            ],
            use_natural_foreign_keys=True
        )
        dump_data = json.loads(dump_data_alike)

        self.assertEqual(dump_data[0].get('fields').get('parent_type'),
                         [an_authorized_relation_ship.parent_type.name])
        self.assertEqual(dump_data[0].get('fields').get('child_type'),
                         [an_authorized_relation_ship.child_type.name])
