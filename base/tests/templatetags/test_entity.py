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
import datetime

from django.test import TestCase
from django.utils import timezone

from base.templatetags.entity import requirement_entity, entity_last_version
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.business.learning_units import GenerateContainer
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory

ENTITY_REQUIREMENT_ACRONYM = "DRT"

today = datetime.date.today()
today2 = datetime.datetime.today()


class EntityTagTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        yr = timezone.now().year
        cls.start_year = AcademicYearFactory(year=yr - 1)
        cls.end_year = AcademicYearFactory(year=yr)
        generator_learning_container = GenerateContainer(start_year=cls.start_year, end_year=cls.end_year)
        cls.a_learning_unit_year = generator_learning_container.generated_container_years[0].learning_unit_year_full
        cls.entity_1 = generator_learning_container.entities[0]
        cls.entity_version_1 = EntityVersionFactory(entity=cls.entity_1, acronym=ENTITY_REQUIREMENT_ACRONYM)

    def test_requirement_entity(self):
        lu = self.a_learning_unit_year
        lu.entities = {'REQUIREMENT_ENTITY': self.entity_version_1}
        self.assertEqual(requirement_entity([lu], 0), ENTITY_REQUIREMENT_ACRONYM)

    def test_no_requirement_entity(self):
        lu = self.a_learning_unit_year
        lu.entities = {}
        self.assertEqual(requirement_entity([lu], 0), '')

    def test_entity_last_version_when_only_one_version(self):
        self.assertEqual(entity_last_version(self.entity_1), self.entity_version_1.acronym)

    def test_entity_last_version_when_several_versions(self):
        an_entity = EntityFactory()
        newest_acronym = "NEW"
        _create_2_entity_version(an_entity, "OLD", newest_acronym)
        self.assertEqual(entity_last_version(an_entity), newest_acronym)


def _create_2_entity_version(an_entity, old_acronym, newest_acronym):
    EntityVersionFactory(entity=an_entity, acronym=old_acronym,
                         start_date=datetime.date(2015, 1, 1).isoformat(),
                         end_date=datetime.date(2016, 1, 1).isoformat())
    EntityVersionFactory(entity=an_entity, acronym=newest_acronym,
                         start_date=datetime.date(2017, 1, 1).isoformat(),
                         end_date=datetime.date(2018, 1, 1).isoformat())
