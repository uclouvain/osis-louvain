##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
import random
from copy import deepcopy
from datetime import timedelta
from uuid import uuid4

from django.test import TestCase
from django.utils.translation import ugettext_lazy as _

from base.business.learning_unit_year_with_context import ENTITY_TYPES_VOLUME
from base.business.learning_units import edition as business_edition
from base.models.entity_component_year import EntityComponentYear
from base.models.entity_container_year import EntityContainerYear
from base.models.enums import entity_container_year_link_type
from base.models.enums import learning_component_year_type
from base.models.enums import learning_unit_year_subtypes
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_unit_component import LearningUnitComponent
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_component_year import EntityComponentYearFactory
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_component import LearningUnitComponentFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from reference.tests.factories.language import LanguageFactory


class LearningUnitEditionTestCase(TestCase):
    def setUp(self):
        self.academic_year = create_current_academic_year()
        self.next_academic_year = AcademicYearFactory(year=self.academic_year.year + 1)

        self.learning_container_year = LearningContainerYearFactory(
            academic_year=self.academic_year,
            common_title='common title',
        )
        self.learning_unit_year = _create_learning_unit_year_with_components(self.learning_container_year,
                                                                             create_lecturing_component=True,
                                                                             create_pratical_component=True)

        an_entity = EntityFactory()
        self.entity_version = EntityVersionFactory(entity=an_entity, parent=None, end_date=None, acronym="DRT")
        self.allocation_entity = _create_entity_container_with_entity_components(
            self.learning_unit_year,
            entity_container_year_link_type.ALLOCATION_ENTITY,
            an_entity
        )
        self.requirement_entity = _create_entity_container_with_entity_components(
            self.learning_unit_year,
            entity_container_year_link_type.REQUIREMENT_ENTITY,
            an_entity,
            repartition_lecturing=30,
            repartition_practical_exercises=10
        )
        self.add_requirement_entity_1 = _create_entity_container_with_entity_components(
            self.learning_unit_year,
            entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1,
            an_entity,
            repartition_lecturing=10,
            repartition_practical_exercises=5
        )

    def test_update_or_create_entity_container_year_with_components_type_requirement(self):
        """In this test, we ensure that when we create an entity_container type requirement,
           we have an entity_component created"""
        an_entity = EntityFactory()
        a_learning_container_year = LearningContainerYearFactory(academic_year=self.academic_year)
        LearningComponentYearFactory(acronym="PM", learning_container_year=a_learning_container_year)
        LearningComponentYearFactory(acronym="PP", learning_container_year=a_learning_container_year)
        link_type = random.choice(ENTITY_TYPES_VOLUME)

        business_edition.update_or_create_entity_container_year_with_components(
            an_entity, a_learning_container_year, link_type
        )
        self.assertEqual(EntityContainerYear.objects.filter(
            learning_container_year=a_learning_container_year).count(), 1)
        self.assertEqual(EntityComponentYear.objects.filter(
            entity_container_year__learning_container_year=a_learning_container_year
        ).count(), 2)

    def test_update_or_create_entity_container_year_with_components_type_allocation(self):
        """In this test, we ensure that when we create an entity_container type allocation,
           we have NO entity_component created"""
        an_entity = EntityFactory()
        a_learning_container_year = LearningContainerYearFactory(academic_year=self.academic_year)
        LearningComponentYearFactory(acronym="PM", learning_container_year=a_learning_container_year)
        LearningComponentYearFactory(acronym="PP", learning_container_year=a_learning_container_year)
        link_type = entity_container_year_link_type.ALLOCATION_ENTITY

        business_edition.update_or_create_entity_container_year_with_components(an_entity, a_learning_container_year,
                                                                                link_type)
        self.assertEqual(EntityContainerYear.objects.filter(
            learning_container_year=a_learning_container_year).count(), 1)
        self.assertEqual(EntityComponentYear.objects.filter(
            entity_container_year__learning_container_year=a_learning_container_year).count(), 0)

    def test_check_postponement_conflict_learning_unit_year_no_differences(self):
        # Copy the same learning unit + change academic year
        another_learning_unit_year = _build_copy(self.learning_unit_year)
        another_learning_unit_year.academic_year = self.next_academic_year
        another_learning_unit_year.save()

        error_list = business_edition._check_postponement_conflict_on_learning_unit_year(self.learning_unit_year,
                                                                                         another_learning_unit_year)
        self.assertIsInstance(error_list, list)
        self.assertFalse(error_list)

    def test_check_postponement_conflict_learning_unit_year_differences_found(self):
        # Copy the same learning unit + change academic year / acronym / specific_title_english
        another_learning_unit_year = _build_copy(self.learning_unit_year)
        another_learning_unit_year.academic_year = self.next_academic_year
        another_learning_unit_year.acronym = 'LBIR1000'
        another_learning_unit_year.specific_title_english = None  # Remove value
        another_learning_unit_year.save()

        error_list = business_edition._check_postponement_conflict_on_learning_unit_year(self.learning_unit_year,
                                                                                         another_learning_unit_year)
        self.assertIsInstance(error_list, list)
        self.assertEqual(len(error_list), 2)
        generic_error = "The value of field '%(field)s' is different between year %(year)s - %(value)s " \
                        "and year %(next_year)s - %(next_value)s"
        # Error : Acronym diff
        error_acronym = _(generic_error) % {
            'field': _('Acronym'),
            'year': self.learning_unit_year.academic_year,
            'value': getattr(self.learning_unit_year, 'acronym'),
            'next_year': another_learning_unit_year.academic_year,
            'next_value': getattr(another_learning_unit_year, 'acronym')
        }
        self.assertIn(error_acronym, error_list)
        # Error : Specific title english diff
        error_specific_title_english = _(generic_error) % {
            'field': _('English title proper'),
            'year': self.learning_unit_year.academic_year,
            'value': getattr(self.learning_unit_year, 'specific_title_english'),
            'next_year': another_learning_unit_year.academic_year,
            'next_value': _('No data')
        }
        self.assertIn(error_specific_title_english, error_list)

    def test_check_postponement_conflict_learning_unit_year_status_diff(self):
        # Copy the same learning unit + change academic year / acronym / specific_title_english
        another_learning_unit_year = _build_copy(self.learning_unit_year)
        another_learning_unit_year.academic_year = self.next_academic_year
        another_learning_unit_year.status = False
        another_learning_unit_year.save()

        error_list = business_edition._check_postponement_conflict_on_learning_unit_year(self.learning_unit_year,
                                                                                         another_learning_unit_year)
        self.assertIsInstance(error_list, list)
        self.assertEqual(len(error_list), 1)
        generic_error = "The value of field '%(field)s' is different between year %(year)s - %(value)s " \
                        "and year %(next_year)s - %(next_value)s"
        # Error : Status diff
        error_status = _(generic_error) % {
            'field': _('Status'),
            'year': self.learning_unit_year.academic_year,
            'value': _('yes'),
            'next_year': another_learning_unit_year.academic_year,
            'next_value': _('no')
        }
        self.assertIn(error_status, error_list)

    def test_check_postponement_conflict_learning_unit_year_case_language_diff(self):
        # Copy the same learning unit year + change academic year, language
        another_learning_unit_year = _build_copy(self.learning_unit_year)
        another_learning_unit_year.academic_year = self.next_academic_year
        another_learning_unit_year.language = LanguageFactory(code='FR', name='French')
        another_learning_unit_year.save()

        error_list = business_edition._check_postponement_conflict_on_learning_unit_year(
            self.learning_unit_year, another_learning_unit_year
        )
        self.assertIsInstance(error_list, list)
        self.assertEqual(len(error_list), 1)
        generic_error = "The value of field '%(field)s' is different between year %(year)s - %(value)s " \
                        "and year %(next_year)s - %(next_value)s"

        # Error : Language diff
        error_language = _(generic_error) % {
            'field': _('Language'),
            'year': self.learning_container_year.academic_year,
            'value': getattr(self.learning_unit_year, 'language'),
            'next_year': another_learning_unit_year.academic_year,
            'next_value': getattr(another_learning_unit_year, 'language')
        }
        self.assertIn(error_language, error_list)

    def test_check_postponement_conflict_learning_container_year_no_differences(self):
        # Copy the same + change academic year
        another_learning_container_year = _build_copy(self.learning_container_year)
        another_learning_container_year.academic_year = self.next_academic_year
        another_learning_container_year.save()
        # No diff found
        error_list = business_edition._check_postponement_conflict_on_learning_container_year(
            self.learning_container_year,
            another_learning_container_year
        )
        self.assertIsInstance(error_list, list)
        self.assertFalse(error_list)

    def test_check_postponement_conflict_learning_container_year_case_common_title_diff(self):
        # Copy the same container + change academic year,common title
        another_learning_container_year = _build_copy(self.learning_container_year)
        another_learning_container_year.academic_year = self.next_academic_year
        another_learning_container_year.common_title = 'Another common title'
        another_learning_container_year.save()

        error_list = business_edition._check_postponement_conflict_on_learning_container_year(
            self.learning_container_year, another_learning_container_year
        )
        self.assertIsInstance(error_list, list)
        self.assertEqual(len(error_list), 1)
        generic_error = "The value of field '%(field)s' is different between year %(year)s - %(value)s " \
                        "and year %(next_year)s - %(next_value)s"

        # Error : Common title diff
        error_common_title = _(generic_error) % {
            'field': _('Common title'),
            'year': self.learning_container_year.academic_year,
            'value': getattr(self.learning_container_year, 'common_title'),
            'next_year': another_learning_container_year.academic_year,
            'next_value': getattr(another_learning_container_year, 'common_title')
        }
        self.assertIn(error_common_title, error_list)

    def test_check_postponement_conflict_learning_unit_year_case_camp_diff(self):
        # Copy the same container + change academic year + campus
        another_learning_unit_year = _build_copy(self.learning_unit_year)
        another_learning_unit_year.academic_year = self.next_academic_year
        another_learning_unit_year.campus = CampusFactory(name='Paris')
        another_learning_unit_year.save()

        error_list = business_edition._check_postponement_conflict_on_learning_unit_year(
            self.learning_unit_year, another_learning_unit_year
        )
        self.assertIsInstance(error_list, list)
        self.assertEqual(len(error_list), 1)
        generic_error = "The value of field '%(field)s' is different between year %(year)s - %(value)s " \
                        "and year %(next_year)s - %(next_value)s"

        # Error : Campus diff
        error_campus = _(generic_error) % {
            'field': _('Campus'),
            'year': self.learning_unit_year.academic_year,
            'value': getattr(self.learning_unit_year, 'campus'),
            'next_year': another_learning_unit_year.academic_year,
            'next_value': getattr(another_learning_unit_year, 'campus')
        }
        self.assertIn(error_campus, error_list)

    def test_check_postponement_conflict_entity_container_year_no_difference_found(self):
        # Copy the same container + change academic year
        another_learning_container_year = _build_copy(self.learning_container_year)
        another_learning_container_year.academic_year = self.next_academic_year
        another_learning_container_year.save()

        # Copy same entity
        for entity_container_to_copy in [self.allocation_entity, self.requirement_entity,
                                         self.add_requirement_entity_1]:
            entity_copied = _build_copy(entity_container_to_copy)
            entity_copied.learning_container_year = another_learning_container_year
            entity_copied.save()

        # No diff found
        error_list = business_edition._check_postponement_conflict_on_entity_container_year(
            self.learning_container_year, another_learning_container_year
        )
        self.assertIsInstance(error_list, list)
        self.assertFalse(error_list)

    def test_check_postponement_conflict_entity_container_year_entity_doesnt_exist_anymore(self):
        # Copy the same container + change academic year
        another_learning_container_year = _build_copy(self.learning_container_year)
        another_learning_container_year.academic_year = self.next_academic_year
        another_learning_container_year.save()

        # Copy same entity
        for entity_container_to_copy in [self.allocation_entity, self.requirement_entity,
                                         self.add_requirement_entity_1]:
            entity_copied = _build_copy(entity_container_to_copy)
            entity_copied.learning_container_year = another_learning_container_year
            entity_copied.save()

        # Modify end_date of entity_version
        self.entity_version.end_date = self.next_academic_year.start_date - timedelta(days=1)
        self.entity_version.save()

        error_list = business_edition._check_postponement_conflict_on_entity_container_year(
            self.learning_container_year, another_learning_container_year
        )
        self.assertIsInstance(error_list, list)
        error_entity_not_exist = _("The entity '%(acronym)s' doesn't exist anymore in %(year)s" % {
            'acronym': self.entity_version.acronym,
            'year': self.next_academic_year
        })
        self.assertIn(error_entity_not_exist, error_list)

    def test_check_postponement_conflict_entity_container_year_differences_found(self):
        # Copy the same container + change academic year
        another_learning_container_year = _build_copy(self.learning_container_year)
        another_learning_container_year.academic_year = self.next_academic_year
        another_learning_container_year.save()

        # Copy same allocation entity
        allocation_entity = _build_copy(self.allocation_entity)
        allocation_entity.learning_container_year = another_learning_container_year
        allocation_entity.save()

        # Link to another entity for requirement
        entityversion = EntityVersionFactory(parent=None, end_date=None, acronym="AREC")

        requirement_entity = EntityContainerYearFactory(
            learning_container_year=another_learning_container_year,
            type=entity_container_year_link_type.REQUIREMENT_ENTITY,
            entity=entityversion.entity
        )

        error_list = business_edition._check_postponement_conflict_on_entity_container_year(
            self.learning_container_year, another_learning_container_year
        )

        self.assertIsInstance(error_list, list)
        self.assertEqual(len(error_list), 2)

        # invalidate cache
        del self.requirement_entity.entity.most_recent_acronym

        generic_error = "The value of field '%(field)s' is different between year %(year)s - %(value)s " \
                        "and year %(next_year)s - %(next_value)s"
        # Error : Requirement entity diff
        error_requirement_entity = _(generic_error) % {
            'field': _(entity_container_year_link_type.REQUIREMENT_ENTITY.lower()),
            'year': self.learning_container_year.academic_year,
            'value': self.requirement_entity.entity.most_recent_acronym,
            'next_year': another_learning_container_year.academic_year,
            'next_value': requirement_entity.entity.most_recent_acronym
        }
        self.assertIn(error_requirement_entity, error_list)

        # Error : Additional requirement entity diff
        error_requirement_entity = _(generic_error) % {
            'field': _(entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1.lower()),
            'year': self.learning_container_year.academic_year,
            'value': self.add_requirement_entity_1.entity.most_recent_acronym,
            'next_year': another_learning_container_year.academic_year,
            'next_value': _('No data')
        }
        self.assertIn(error_requirement_entity, error_list)

    def test_check_postponement_conflict_on_volumes_case_no_diff(self):
        # Copy the same container + change academic year
        another_learning_container_year = _build_copy(self.learning_container_year)
        another_learning_container_year.academic_year = self.next_academic_year
        another_learning_container_year.save()

        # Create LUY with components LECTURING / PRACTICAL EXERCICES + link to the same learning unit
        another_learning_unit_year = _create_learning_unit_year_with_components(another_learning_container_year,
                                                                                create_pratical_component=True,
                                                                                create_lecturing_component=True)
        another_learning_unit_year.learning_unit = self.learning_unit_year.learning_unit
        another_learning_unit_year.save()

        _create_entity_container_with_entity_components(another_learning_unit_year,
                                                        entity_container_year_link_type.ALLOCATION_ENTITY,
                                                        self.allocation_entity.entity)
        _create_entity_container_with_entity_components(another_learning_unit_year,
                                                        entity_container_year_link_type.REQUIREMENT_ENTITY,
                                                        self.requirement_entity.entity,
                                                        repartition_lecturing=30,
                                                        repartition_practical_exercises=10)
        _create_entity_container_with_entity_components(another_learning_unit_year,
                                                        entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1,
                                                        self.add_requirement_entity_1.entity,
                                                        repartition_lecturing=10,
                                                        repartition_practical_exercises=5)

        error_list = business_edition._check_postponement_conflict_on_volumes(self.learning_container_year,
                                                                              another_learning_container_year)
        self.assertIsInstance(error_list, list)
        self.assertFalse(error_list)

    def test_check_postponement_conflict_on_volumes_multiples_differences(self):
        # Copy the same container + change academic year
        another_learning_container_year = _build_copy(self.learning_container_year)
        another_learning_container_year.academic_year = self.next_academic_year
        another_learning_container_year.save()

        # Create LUY with components LECTURING / PRACTICAL EXERCICES + link to the same learning unit
        another_learning_unit_year = _create_learning_unit_year_with_components(another_learning_container_year,
                                                                                create_pratical_component=True,
                                                                                create_lecturing_component=True)
        another_learning_unit_year.learning_unit = self.learning_unit_year.learning_unit
        LearningComponentYear.objects.filter(
            learningunitcomponent__learning_unit_year=self.learning_unit_year
        ).update(
            hourly_volume_total_annual=60,
            hourly_volume_partial_q1=40,
            hourly_volume_partial_q2=20
        )
        LearningComponentYear.objects.filter(
            learningunitcomponent__learning_unit_year=another_learning_unit_year
        ).update(
            hourly_volume_total_annual=50,
            hourly_volume_partial_q1=35,
            hourly_volume_partial_q2=15
        )
        another_learning_unit_year.save()

        _create_entity_container_with_entity_components(another_learning_unit_year,
                                                        entity_container_year_link_type.ALLOCATION_ENTITY,
                                                        self.allocation_entity.entity)
        _create_entity_container_with_entity_components(another_learning_unit_year,
                                                        entity_container_year_link_type.REQUIREMENT_ENTITY,
                                                        self.requirement_entity.entity,
                                                        repartition_lecturing=30,
                                                        repartition_practical_exercises=10)
        _create_entity_container_with_entity_components(another_learning_unit_year,
                                                        entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1,
                                                        self.add_requirement_entity_1.entity,
                                                        repartition_lecturing=20,
                                                        repartition_practical_exercises=10)

        error_list = business_edition._check_postponement_conflict_on_volumes(self.learning_container_year,
                                                                              another_learning_container_year)
        self.assertIsInstance(error_list, list)
        self.assertEqual(len(error_list), 10)

        tests_cases = [
            {'field': 'volume_additional_requirement_entity_1', 'value': 10.0, 'next_value': 20.0},
            {'field': 'volume_total', 'value': 60.0, 'next_value': 50.0},
            {'field': 'volume_q1', 'value': 40.0, 'next_value': 35.0},
            {'field': 'volume_q2', 'value': 20.0, 'next_value': 15.0}
        ]
        for test in tests_cases:
            with self.subTest(test=test):
                error_expected = (_("The value of field '%(field)s' for the learning unit %(acronym)s "
                                    "(%(component_type)s) is different between year %(year)s - %(value)s and year "
                                    "%(next_year)s - %(next_value)s") %
                                  {
                                      'field': _(test.get('field')),
                                      'acronym': another_learning_container_year.acronym,
                                      'component_type': _(learning_component_year_type.LECTURING),
                                      'year': self.learning_container_year.academic_year,
                                      'value': test.get('value'),
                                      'next_year': another_learning_container_year.academic_year,
                                      'next_value': test.get('next_value'),
                                  })
                self.assertIn(error_expected, error_list)

    def test_check_postponement_conflict_on_volumes_case_no_lecturing_component_next_year(self):
        """ The goal of this test is to ensure that there is an error IF the learning unit year on current year have
           component LECTURING that the learning unit year on the next year doesn't have """

        # Copy the same container + change academic year
        another_learning_container_year = _build_copy(self.learning_container_year)
        another_learning_container_year.academic_year = self.next_academic_year
        another_learning_container_year.save()

        # Create LUY with components PRACTICAL EXERCICES + link to the same learning unit
        another_learning_unit_year = _create_learning_unit_year_with_components(another_learning_container_year,
                                                                                create_pratical_component=True,
                                                                                create_lecturing_component=False)
        another_learning_unit_year.learning_unit = self.learning_unit_year.learning_unit
        another_learning_unit_year.save()

        _create_entity_container_with_entity_components(another_learning_unit_year,
                                                        entity_container_year_link_type.ALLOCATION_ENTITY,
                                                        self.allocation_entity.entity)
        _create_entity_container_with_entity_components(another_learning_unit_year,
                                                        entity_container_year_link_type.REQUIREMENT_ENTITY,
                                                        self.requirement_entity.entity,
                                                        repartition_practical_exercises=10)
        _create_entity_container_with_entity_components(another_learning_unit_year,
                                                        entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1,
                                                        self.add_requirement_entity_1.entity,
                                                        repartition_practical_exercises=5)

        error_list = business_edition._check_postponement_conflict_on_volumes(self.learning_container_year,
                                                                              another_learning_container_year)
        self.assertIsInstance(error_list, list)
        self.assertEqual(len(error_list), 1)
        error_expected = _("There is not %(component_type)s for the learning unit %(acronym)s - %(year)s but exist "
                           "in %(existing_year)s") % {
                             'component_type': _(learning_component_year_type.LECTURING),
                             'acronym': self.learning_container_year.acronym,
                             'year': self.next_academic_year,
                             'existing_year': self.learning_container_year.academic_year
                         }
        self.assertIn(error_expected, error_list)

    def test_check_postponement_conflict_on_volumes_case_no_practical_exercise_component_current_year(self):
        """ The goal of this test is to ensure that there is an error IF the learning unit year on next year have
            component PRACTICAL EXERCISES that the learning unit year on the current year doesn't have """

        # Copy the same container + change academic year
        another_learning_container_year = _build_copy(self.learning_container_year)
        another_learning_container_year.academic_year = self.next_academic_year
        another_learning_container_year.save()

        # Create LUY with components LECTURING / PRACTICAL EXERCISES + link to the same learning unit
        another_learning_unit_year = _create_learning_unit_year_with_components(another_learning_container_year,
                                                                                create_pratical_component=True,
                                                                                create_lecturing_component=True)
        another_learning_unit_year.learning_unit = self.learning_unit_year.learning_unit
        another_learning_unit_year.save()

        _create_entity_container_with_entity_components(another_learning_unit_year,
                                                        entity_container_year_link_type.ALLOCATION_ENTITY,
                                                        self.allocation_entity.entity)
        _create_entity_container_with_entity_components(another_learning_unit_year,
                                                        entity_container_year_link_type.REQUIREMENT_ENTITY,
                                                        self.requirement_entity.entity,
                                                        repartition_lecturing=30,
                                                        repartition_practical_exercises=10)
        _create_entity_container_with_entity_components(another_learning_unit_year,
                                                        entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1,
                                                        self.add_requirement_entity_1.entity,
                                                        repartition_lecturing=10,
                                                        repartition_practical_exercises=5)

        # REMOVE PRATICAL_EXERCICE component for current learning unit year
        _delete_components(self.learning_unit_year, learning_component_year_type.PRACTICAL_EXERCISES)

        error_list = business_edition._check_postponement_conflict_on_volumes(self.learning_container_year,
                                                                              another_learning_container_year)
        self.assertIsInstance(error_list, list)
        self.assertEqual(len(error_list), 1)
        error_expected = _("There is not %(component_type)s for the learning unit %(acronym)s - %(year)s but exist "
                           "in %(existing_year)s") % {
                             'component_type': _(learning_component_year_type.PRACTICAL_EXERCISES),
                             'acronym': self.learning_container_year.acronym,
                             'year': self.learning_container_year.academic_year,
                             'existing_year': self.next_academic_year
                         }
        self.assertIn(error_expected, error_list)

    def test_check_postponement_conflict_on_all_sections(self):
        # LEARNING CONTAINER YEAR - Title modified
        another_learning_container_year = _build_copy(self.learning_container_year)
        another_learning_container_year.academic_year = self.next_academic_year
        another_learning_container_year.common_title = "Title Modified"
        another_learning_container_year.save()

        # LEARNING UNIT YEAR - Modify specific title
        another_learning_unit_year = _build_copy(self.learning_unit_year)
        another_learning_unit_year.academic_year = self.next_academic_year
        another_learning_unit_year.learning_container_year = another_learning_container_year
        another_learning_unit_year.specific_title = "Specific title modified"
        another_learning_unit_year.save()

        # ENTITY - Same allocation but NOT same requirement entity
        allocation_entity = _build_copy(self.allocation_entity)
        allocation_entity.learning_container_year = another_learning_container_year
        allocation_entity.save()
        an_entity = EntityFactory()
        EntityVersionFactory(entity=an_entity, parent=None, end_date=None, acronym="AREC")
        EntityContainerYearFactory(learning_container_year=another_learning_container_year,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY,
                                   entity=an_entity)

        error_list = business_edition._check_postponement_conflict(self.learning_unit_year, another_learning_unit_year)
        self.assertIsInstance(error_list, list)
        self.assertEqual(len(error_list), 6)

    def test_extends_only_components_of_learning_unit_year(self):
        # Creating partim with components for the same learningContainerYear
        _create_learning_unit_year_with_components(self.learning_container_year,
                                                   create_lecturing_component=True,
                                                   create_pratical_component=True,
                                                   subtype=learning_unit_year_subtypes.PARTIM)

        inital_components_count = LearningComponentYear.objects.all().count()
        number_of_components = LearningUnitComponent.objects.filter(learning_unit_year=self.learning_unit_year).count()
        expected_count = inital_components_count + number_of_components
        next_year = self.academic_year.year + 1

        business_edition.duplicate_learning_unit_year(self.learning_unit_year, AcademicYearFactory(year=next_year))

        # assert components of partims are not duplicated too
        self.assertEqual(LearningComponentYear.objects.all().count(), expected_count)


def _create_learning_unit_year_with_components(l_container, create_lecturing_component=True,
                                               create_pratical_component=True, subtype=None):
    if not subtype:
        subtype = learning_unit_year_subtypes.FULL
    language = LanguageFactory(code='EN', name='English')
    a_learning_unit_year = LearningUnitYearFactory(learning_container_year=l_container,
                                                   acronym=l_container.acronym,
                                                   academic_year=l_container.academic_year,
                                                   status=True,
                                                   language=language,
                                                   campus=CampusFactory(name='MIT'),
                                                   subtype=subtype)

    if create_lecturing_component:
        a_component = LearningComponentYearFactory(
            learning_container_year=l_container,
            type=learning_component_year_type.LECTURING,
            planned_classes=1
        )
        LearningUnitComponentFactory(learning_unit_year=a_learning_unit_year, learning_component_year=a_component)

    if create_pratical_component:
        a_component = LearningComponentYearFactory(
            learning_container_year=l_container,
            type=learning_component_year_type.PRACTICAL_EXERCISES,
            planned_classes=1
        )
        LearningUnitComponentFactory(learning_unit_year=a_learning_unit_year, learning_component_year=a_component)

    return a_learning_unit_year


def _create_entity_container_with_entity_components(a_learning_unit_year, container_type, an_entity,
                                                    repartition_lecturing=None, repartition_practical_exercises=None):
    an_entity_container = EntityContainerYearFactory(
        learning_container_year=a_learning_unit_year.learning_container_year,
        type=container_type,
        entity=an_entity
    )

    if repartition_lecturing is not None:
        _create_entity_component_year(a_learning_unit_year, learning_component_year_type.LECTURING,
                                      an_entity_container, repartition_lecturing)
    if repartition_practical_exercises is not None:
        _create_entity_component_year(a_learning_unit_year, learning_component_year_type.PRACTICAL_EXERCISES,
                                      an_entity_container, repartition_practical_exercises)
    return an_entity_container


def _create_entity_component_year(luy, component_type, entity_container_year, repartition_volume):
    a_learning_unit_component = LearningUnitComponent.objects.get(learning_unit_year=luy,
                                                                  learning_component_year__type=component_type)
    EntityComponentYearFactory(entity_container_year=entity_container_year,
                               learning_component_year=a_learning_unit_component.learning_component_year,
                               repartition_volume=repartition_volume)


def _delete_components(luy, component_type):
    LearningUnitComponent.objects.filter(learning_unit_year=luy, learning_component_year__type=component_type) \
        .delete()


def _build_copy(instance):
    instance_copy = deepcopy(instance)
    instance_copy.pk = None
    instance_copy.uuid = uuid4()
    return instance_copy
