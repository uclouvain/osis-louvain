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
from django.test.utils import override_settings
from django.utils.translation import gettext

from base.models.learning_unit_year import LearningUnitYear
from base.business.learning_units.comparison import get_keys, _get_changed_values, get_value, \
    compare_learning_unit_years, compare_learning_component_year, compare_volumes, get_entity_by_type
from base.tests.factories.learning_unit_year import create_learning_unit_year
from base.models.enums import entity_container_year_link_type
from base.models.enums import quadrimesters, learning_unit_year_session, attribution_procedure
from base.models.enums import learning_unit_year_periodicity
from base.models.enums import learning_unit_year_subtypes
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_class_year import LearningClassYearFactory
from decimal import Decimal

TITLE = 'Intitulé'
OTHER_TITLE = 'title 1'
NEW_ACRONYM = "LDROI1005"


class TestComparison(TestCase):
    def setUp(self):
        learning_unit = LearningUnitFactory()
        self.academic_year = create_current_academic_year()
        self.learning_unit_year = create_learning_unit_year(self.academic_year, TITLE, learning_unit)
        self.previous_academic_yr = AcademicYearFactory(year=self.academic_year.year - 1)
        self.previous_learning_unit_year = create_learning_unit_year(self.previous_academic_yr, OTHER_TITLE,
                                                                     learning_unit)

    @override_settings(LANGUAGES=[('fr-be', 'French'), ('en', 'English'), ], LANGUAGE_CODE='fr-be')
    def test_get_value_for_boolean(self):
        data = self.learning_unit_year.__dict__
        self.assertEqual(get_value(LearningUnitYear, data, 'status'), 'Actif')

    @override_settings(LANGUAGES=[('fr-be', 'French'), ('en', 'English'), ], LANGUAGE_CODE='fr-be')
    def test_get_value_for_enum(self):
        data = self.learning_unit_year.__dict__
        self.assertEqual(get_value(LearningUnitYear, data, 'subtype'), 'FULL')

    @override_settings(LANGUAGES=[('fr-be', 'French'), ('en', 'English'), ], LANGUAGE_CODE='fr-be')
    def test_get_value(self):
        data = self.learning_unit_year.__dict__
        self.assertEqual(get_value(LearningUnitYear, data, 'specific_title'), TITLE)

    def test_get_keys(self):
        self.assertCountEqual(get_keys(['a1', 'c3'], ['a1', 'b2', 'c1']), ['a1', 'b2', 'c1', 'c3'])


class LearningUnitYearComparaisonTest(TestCase):

    def setUp(self):
        self.academic_year = create_current_academic_year()
        self.previous_academic_year = AcademicYearFactory(year=self.academic_year.year + 1)

        self.learning_unit_year = self.create_learning_unit_yr(self.academic_year, "LDR", True,
                                                               learning_unit_year_subtypes.FULL)
        self.previous_learning_unit_year = self.create_learning_unit_yr(self.previous_academic_year, NEW_ACRONYM, False,
                                                                        learning_unit_year_subtypes.PARTIM)

    def create_learning_unit_yr(self, academic_year, acronym, status, subtype):
        return LearningUnitYearFactory(acronym=acronym,
                                       academic_year=academic_year,
                                       subtype=subtype,
                                       status=status,
                                       internship_subtype=None,
                                       credits=5,
                                       periodicity=learning_unit_year_periodicity.ANNUAL,
                                       language=None,
                                       professional_integration=True,
                                       specific_title="Juridic law courses",
                                       specific_title_english=None,
                                       quadrimester=quadrimesters.Q1,
                                       session=learning_unit_year_session.SESSION_123,
                                       attribution_procedure=attribution_procedure.EXTERNAL
                                       )

    @override_settings(LANGUAGES=[('fr-be', 'French'), ('en', 'English'), ], LANGUAGE_CODE='fr-be')
    def test_compare(self):
        self.assertCountEqual(compare_learning_unit_years(self.learning_unit_year, self.previous_learning_unit_year),
                              {'acronym': NEW_ACRONYM,
                               'status': 'Non',
                               'subtype': 'Partim'})

    @override_settings(LANGUAGES=[('fr-be', 'French'), ('en', 'English'), ], LANGUAGE_CODE='fr-be')
    def test_get_changed_value_wrong_fieldname(self):
        data_obj1, data_obj2 = self.learning_unit_year.__dict__, self.previous_learning_unit_year.__dict__
        del data_obj2['acronym']
        with self.assertRaises(KeyError):
            _get_changed_values(data_obj1, data_obj2, ['acronym'], LearningUnitYear)

    def test_compare_learning_component_year(self):
        acronym_used_twice = 'PM1'
        acronym_used_once = 'PM2'

        l_comp_yr_current = LearningComponentYearFactory(acronym=acronym_used_twice,
                                                         planned_classes=1)
        LearningClassYearFactory(learning_component_year=l_comp_yr_current)
        l_comp_yr_previous = LearningComponentYearFactory(acronym=acronym_used_twice,
                                                          planned_classes=1)
        l_comp_yr_next = LearningComponentYearFactory(acronym=acronym_used_once,
                                                      planned_classes=1)

        data = compare_learning_component_year(l_comp_yr_current, l_comp_yr_previous, l_comp_yr_next)
        self.assertEqual(data.get('acronym'),
                         [l_comp_yr_previous.acronym, l_comp_yr_current.acronym, l_comp_yr_next.acronym])
        self.assertEqual(data.get('real_classes'),
                         [l_comp_yr_previous.real_classes, l_comp_yr_current.real_classes, l_comp_yr_next.real_classes])

    def test_compare_volumes(self):
        previous_volume_global = 12.0
        current_volume_global = 10

        previous_planned_classes = 1
        current_planned_classes = 2

        current_volume_q1 = 20
        next_volume_q1 = 10

        data_volumes_previous = {
            'volumes': {
                'VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2': 0, 'VOLUME_TOTAL': Decimal('12.00'),
                'VOLUME_GLOBAL': previous_volume_global,
                'PLANNED_CLASSES': previous_planned_classes,
                'VOLUME_Q1': None,
                'VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1': 0.0, 'VOLUME_Q2': Decimal('30.00'),
                'VOLUME_REQUIREMENT_ENTITY': 12.0
            }
        }

        data_volumes_current = {
            'volumes': {
                'VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2': 0,
                'VOLUME_TOTAL': Decimal('12.00'),
                'VOLUME_GLOBAL': current_volume_global,
                'PLANNED_CLASSES': current_planned_classes,
                'VOLUME_Q1': current_volume_q1,
                'VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1': 0.0,
                'VOLUME_Q2': Decimal('30.00'),
                'VOLUME_REQUIREMENT_ENTITY': 12.0
            }
        }
        data_volumes_next = {
            'volumes': {
                'VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2': 0, 'VOLUME_TOTAL': Decimal('12.00'),
                'VOLUME_GLOBAL': 12.0, 'PLANNED_CLASSES': 1, 'VOLUME_Q1': next_volume_q1,
                'VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1': 0.0, 'VOLUME_Q2': Decimal('30.00'),
                'VOLUME_REQUIREMENT_ENTITY': 12.0
            }
        }

        data = compare_volumes(data_volumes_current, data_volumes_previous, data_volumes_next)
        self.assertEqual(data.get('VOLUME_GLOBAL'), [previous_volume_global, current_volume_global, 12.0])
        self.assertEqual(data.get('VOLUME_Q1'), [None, current_volume_q1, next_volume_q1])
        self.assertEqual(len(list(data.keys())), 2)

    def test_get_entity_by_type(self):
        learning_cont_yr = LearningContainerYearFactory(academic_year=self.academic_year)
        entity_container_yr = EntityContainerYearFactory(
            learning_container_year=learning_cont_yr,
            type=entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1
        )
        luy = LearningUnitYear(academic_year=self.academic_year, learning_container_year=learning_cont_yr)
        self.assertEqual(get_entity_by_type(luy, entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1),
                         entity_container_yr.entity)
        self.assertIsNone(get_entity_by_type(luy, entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_2))
