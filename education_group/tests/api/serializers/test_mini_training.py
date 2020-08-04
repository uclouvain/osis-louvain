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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.conf import settings
from django.test import TestCase, RequestFactory
from django.urls import reverse

from base.models.enums import organization_type
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import MiniTrainingFactory
from base.tests.factories.entity_version import EntityVersionFactory
from education_group.api.serializers.mini_training import MiniTrainingDetailSerializer, MiniTrainingListSerializer
from education_group.api.views.mini_training import MiniTrainingList
from program_management.tests.factories.education_group_version import StandardEducationGroupVersionFactory


class MiniTrainingListSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2018)
        cls.entity_version = EntityVersionFactory(
            entity__organization__type=organization_type.MAIN
        )

        cls.mini_training = MiniTrainingFactory(
            academic_year=cls.academic_year,
            management_entity=cls.entity_version.entity,
        )
        cls.version = StandardEducationGroupVersionFactory(
            offer=cls.mini_training,
            root_group__partial_acronym='LLOGO2100'
        )
        url = reverse('education_group_api_v1:' + MiniTrainingList.name)
        cls.serializer = MiniTrainingListSerializer(cls.version, context={
            'request': RequestFactory().get(url),
            'language': settings.LANGUAGE_CODE_EN
        })

    def test_contains_expected_fields(self):
        expected_fields = [
            'title',
            'url',
            'version_name',
            'acronym',
            'code',
            'education_group_type',
            'education_group_type_text',
            'academic_year',
            'management_entity',
            'management_faculty',
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)

    def test_ensure_academic_year_field_is_slugified(self):
        self.assertEqual(
            self.serializer.data['academic_year'],
            self.academic_year.year
        )

    def test_ensure_education_group_type_field_is_slugified(self):
        self.assertEqual(
            self.serializer.data['education_group_type'],
            self.mini_training.education_group_type.name
        )

    def test_ensure_code_is_an_alias_to_partial_acronym(self):
        self.assertEqual(
            self.serializer.data['code'],
            self.version.root_group.partial_acronym
        )


class MiniTrainingDetailSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2018)
        cls.entity_version = EntityVersionFactory(
            entity__organization__type=organization_type.MAIN
        )
        cls.mini_training = MiniTrainingFactory(
            partial_acronym='LGENR100I',
            academic_year=cls.academic_year,
            management_entity=cls.entity_version.entity,
        )
        cls.version = StandardEducationGroupVersionFactory(offer=cls.mini_training)
        url = reverse('education_group_api_v1:mini_training_read', kwargs={
            'official_partial_acronym': cls.version.root_group.partial_acronym,
            'year': cls.academic_year.year
        })
        cls.serializer = MiniTrainingDetailSerializer(cls.version, context={
            'request': RequestFactory().get(url),
            'language': settings.LANGUAGE_CODE_FR
        })

    def test_contains_expected_fields(self):
        expected_fields = [
            'title',
            'url',
            'version_name',
            'acronym',
            'code',
            'education_group_type',
            'education_group_type_text',
            'academic_year',
            'management_entity',
            'management_faculty',
            'active',
            'active_text',
            'schedule_type',
            'schedule_type_text',
            'keywords',
            'credits',
            'min_constraint',
            'max_constraint',
            'constraint_type',
            'constraint_type_text',
            'remark',
            'campus',
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)

    def test_ensure_academic_year_field_is_slugified(self):
        self.assertEqual(
            self.serializer.data['academic_year'],
            self.academic_year.year
        )

    def test_ensure_education_group_type_field_is_slugified(self):
        self.assertEqual(
            self.serializer.data['education_group_type'],
            self.mini_training.education_group_type.name
        )
