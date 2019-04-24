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
from django.utils.translation import ugettext_lazy as _

from attribution.business import attribution_charge_new
from attribution.business import xls_build as xls_build_attribution
from attribution.business.xls_build import LEARNING_UNIT_TITLES
from attribution.tests.factories.attribution_charge_new import AttributionChargeNewFactory
from base.models.enums import entity_container_year_link_type
from base.tests.factories.business.learning_units import GenerateContainer
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.user import UserFactory
from osis_common.document import xls_build

ACRONYM_REQUIREMENT = 'INFO'
ACRONYM_ALLOCATION = 'DRT'


class TestXlsBuild(TestCase):

    def setUp(self):
        generator_container = GenerateContainer(datetime.date.today().year-2, datetime.date.today().year)
        self.learning_unit_yr_1 = generator_container.generated_container_years[0].learning_unit_year_full

        self.learning_unit_yr_1.entities = {
            entity_container_year_link_type.REQUIREMENT_ENTITY: EntityVersionFactory(acronym=ACRONYM_REQUIREMENT),
            entity_container_year_link_type.ALLOCATION_ENTITY: EntityVersionFactory(acronym=ACRONYM_ALLOCATION)
        }

        component_1 = LearningComponentYearFactory(learning_unit_year=self.learning_unit_yr_1)
        self.attribution_1 = AttributionChargeNewFactory(learning_component_year=component_1)
        self.learning_unit_yr_1.attribution_charge_news = attribution_charge_new. \
            find_attribution_charge_new_by_learning_unit_year_as_dict(self.learning_unit_yr_1)
        self.user = UserFactory()

    def test_prepare_xls_content_no_data(self):
        self.assertEqual(xls_build_attribution.prepare_xls_content([]), [])

    def test_prepare_xls_content_with_data(self):
        attributions = xls_build_attribution.prepare_xls_content([self.learning_unit_yr_1])
        self.assertEqual(len(attributions), len(self.learning_unit_yr_1.attribution_charge_news))
        an_attribution = self.learning_unit_yr_1.attribution_charge_news.get(self.attribution_1.attribution.id)
        self.assertEqual(attributions[0], self.get_xls_data(an_attribution, self.learning_unit_yr_1))

    def test_prepare_titles(self):
        self.assertCountEqual(xls_build_attribution._prepare_titles(),
                              LEARNING_UNIT_TITLES + xls_build_attribution.ATTRIBUTION_TITLES)

    def get_xls_data(self, an_attribution, learning_unit_yr):
        return [learning_unit_yr.academic_year.name,
                learning_unit_yr.acronym,
                learning_unit_yr.complete_title,
                xls_build.translate(learning_unit_yr.learning_container_year.container_type),
                xls_build.translate(learning_unit_yr.subtype),
                ACRONYM_REQUIREMENT,
                ACRONYM_ALLOCATION,
                learning_unit_yr.credits,
                xls_build.translate(learning_unit_yr.status),
                an_attribution.get('person'),
                xls_build.translate((an_attribution.get('function'))),
                an_attribution.get('substitute'),
                an_attribution.get('LECTURING'),
                an_attribution.get('PRACTICAL_EXERCISES'),
                an_attribution.get('start_year'),
                an_attribution.get('duration')
                ]


def _generate_xls_build_parameter(xls_data, user):
    return {
        xls_build.LIST_DESCRIPTION_KEY: _(xls_build_attribution.XLS_DESCRIPTION),
        xls_build.FILENAME_KEY: _(xls_build_attribution.XLS_FILENAME),
        xls_build.USER_KEY: user.username,
        xls_build.WORKSHEETS_DATA: [{
            xls_build.CONTENT_KEY: xls_data,
            xls_build.HEADER_TITLES_KEY: LEARNING_UNIT_TITLES + xls_build_attribution.ATTRIBUTION_TITLES,
            xls_build.WORKSHEET_TITLE_KEY: _(xls_build_attribution.WORKSHEET_TITLE),
        }]
    }
