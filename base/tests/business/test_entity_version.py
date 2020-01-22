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

from base.business.entity_version import find_entity_version_according_academic_year
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory


class EntityVersionTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        today = datetime.date.today()
        cls.current_academic_year = AcademicYearFactory(start_date=today,
                                                         end_date=today.replace(year=today.year + 1),
                                                         year=today.year)

        cls.entity_parent = EntityFactory()

        cls.entity_versions = []
        for _ in range(20):
            child_entity_version = EntityVersionFactory(
                parent=cls.entity_parent,
                start_date=cls.current_academic_year.start_date,
                end_date=cls.current_academic_year.end_date
            )

            cls.entity_parent = child_entity_version.entity
            cls.entity_versions.append(child_entity_version)

    def test_find_entity_version_according_academic_year(self):
        entity = EntityFactory()
        entity_version_before_ac = EntityVersionFactory(
            parent=None,
            entity=entity,
            start_date=self.current_academic_year.start_date - datetime.timedelta(days=365),
            end_date=self.current_academic_year.start_date - datetime.timedelta(days=20),
        )
        entity_version_in_ac = EntityVersionFactory(
            parent=None,
            entity=entity,
            start_date=self.current_academic_year.start_date + datetime.timedelta(days=19),
            end_date=self.current_academic_year.end_date + datetime.timedelta(days=1),
        )
        all_entity_version = [entity_version_before_ac, entity_version_in_ac]
        self.assertEqual(find_entity_version_according_academic_year(all_entity_version, self.current_academic_year),
                         entity_version_in_ac)
