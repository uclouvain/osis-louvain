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

from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from learning_unit.api.serializers.learning_unit import LearningUnitDetailedSerializer, LearningUnitSerializer, \
    LearningUnitTitleSerializer


class LearningUnitTitleSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        academic_year = AcademicYearFactory()
        learning_unit_year = LearningUnitYearFactory(
            academic_year=academic_year,
        )
        cls.learning_unit_year = LearningUnitYear.objects.filter(pk=learning_unit_year.pk).annotate_full_title().get()

        cls.serializer = LearningUnitTitleSerializer(
            cls.learning_unit_year,
            context={'language': settings.LANGUAGE_CODE_EN}
        )

    def test_contains_expected_fields(self):
        expected_fields = [
            'title',
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)


class LearningUnitSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        academic_year = AcademicYearFactory()
        requirement_entity_version = EntityVersionFactory(
            start_date=AcademicYearFactory(year=academic_year.year - 1).start_date,
            end_date=AcademicYearFactory(year=academic_year.year + 1).end_date,
        )
        learning_unit_year = LearningUnitYearFactory(
            academic_year=academic_year,
            learning_container_year__requirement_entity=requirement_entity_version.entity
        )
        cls.learning_unit_year = LearningUnitYear.objects.filter(pk=learning_unit_year.pk).annotate_full_title().get()
        setattr(cls.learning_unit_year, "entity_requirement", "OSIS")
        setattr(cls.learning_unit_year, "entity_allocation", "OSIS")
        url = reverse('learning_unit_api_v1:learningunits_list')
        cls.serializer = LearningUnitSerializer(cls.learning_unit_year, context={
            'request': RequestFactory().get(url),
            'language': settings.LANGUAGE_CODE_EN
        })

    def test_contains_expected_fields(self):
        expected_fields = [
            'title',
            'url',
            'osis_url',
            'acronym',
            'academic_year',
            'credits',
            'status',
            'requirement_entity',
            'allocation_entity',
            'type',
            'type_text',
            'subtype',
            'subtype_text',
            'has_proposal',
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)


class LearningUnitDetailedSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        anac = AcademicYearFactory()
        requirement_entity = EntityFactory()
        EntityVersionFactory(
            start_date=AcademicYearFactory(year=anac.year - 1).start_date,
            end_date=AcademicYearFactory(year=anac.year + 1).end_date,
            entity=requirement_entity
        )
        luy = LearningUnitYearFactory(
            academic_year=anac,
            learning_container_year__requirement_entity=requirement_entity
        )
        cls.luy = LearningUnitYear.objects.filter(pk=luy.pk).annotate_full_title().get()
        setattr(cls.luy, "entity_requirement", "OSIS")
        setattr(cls.luy, "entity_allocation", "OSIS")
        url_kwargs = {
            'acronym': cls.luy.acronym,
            'year': cls.luy.academic_year.year
        }
        url = reverse('learning_unit_api_v1:learningunits_read', kwargs=url_kwargs)
        cls.serializer = LearningUnitDetailedSerializer(cls.luy, context={
            'request': RequestFactory().get(url),
            'language': settings.LANGUAGE_CODE_EN
        })

    def test_contains_expected_fields(self):
        expected_fields = [
            'title',
            'url',
            'osis_url',
            'acronym',
            'academic_year',
            'credits',
            'status',
            'requirement_entity',
            'allocation_entity',
            'type',
            'type_text',
            'subtype',
            'subtype_text',
            'has_proposal',
            'quadrimester',
            'quadrimester_text',
            'periodicity',
            'periodicity_text',
            'campus',
            'team',
            'language',
            'components',
            'parent',
            'partims',
            'proposal',
            'summary_status',
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)
