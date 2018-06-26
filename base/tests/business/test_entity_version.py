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

from base.business import learning_unit_year_with_context
from base.business.entity_version import find_entity_version_descendants, find_entity_version_according_academic_year
from base.models.enums import entity_container_year_link_type as entity_types, organization_type, \
    entity_container_year_link_type
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_component_year import EntityComponentYearFactory
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.academic_year import AcademicYearFactory
import datetime
from django.utils.translation import ugettext_lazy as _

from base.tests.factories.organization import OrganizationFactory
from reference.tests.factories.country import CountryFactory


class EntityVersionTestCase(TestCase):
    def setUp(self):
        today = datetime.date.today()
        self.current_academic_year = AcademicYearFactory(start_date=today,
                                                         end_date=today.replace(year=today.year + 1),
                                                         year=today.year)

        self.entity_parent = EntityFactory()

        self.entity_versions = []
        for _ in range(20):
            child_entity_version = EntityVersionFactory(
                parent=self.entity_parent,
                start_date=self.current_academic_year.start_date,
                end_date=self.current_academic_year.end_date
            )

            self.entity_parent = child_entity_version.entity
            self.entity_versions.append(child_entity_version)

    def test_find_entity_version_descendants(self):
        descendants_id = find_entity_version_descendants(self.entity_versions[0], self.current_academic_year.start_date)
        self.assertEqual(len(descendants_id), 19)

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
        all_entity_version = [entity_version_before_ac,entity_version_in_ac]
        self.assertEqual(find_entity_version_according_academic_year(all_entity_version, self.current_academic_year),
                         entity_version_in_ac)
