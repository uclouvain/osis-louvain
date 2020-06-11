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
from copy import deepcopy
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from base.business.learning_units import edition as business_edition
from base.enums.component_detail import COMPONENT_DETAILS
from base.enums.component_detail import VOLUME_TOTAL, VOLUME_Q1, VOLUME_Q2, VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1
from base.models.enums import entity_container_year_link_type
from base.models.enums import learning_component_year_type
from base.models.enums import learning_unit_year_subtypes
from base.models.enums.component_type import COMPONENT_TYPES
from base.models.learning_component_year import LearningComponentYear
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory, LearningUnitYearWithComponentsFactory
from reference.tests.factories.language import FrenchLanguageFactory, EnglishLanguageFactory


class LearningUnitEditionTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)
        cls.next_academic_year = AcademicYearFactory(year=cls.academic_year.year + 1)

        cls.entity_version = EntityVersionFactory(parent=None, end_date=None, acronym="DRT")

        cls.learning_unit_year = LearningUnitYearWithComponentsFactory(
            academic_year=cls.academic_year,
            language=EnglishLanguageFactory(),
            learning_container_year__common_title="common title",
            learning_container_year__requirement_entity=cls.entity_version.entity,
            learning_container_year__additional_entity_1=EntityVersionFactory().entity,
            lecturing_component__repartition_volume_requirement_entity=30,
            lecturing_component__repartition_volume_additional_entity_1=10,
            lecturing_component__hourly_volume_total_annual=40,
            lecturing_component__hourly_volume_partial_q1=40,
            lecturing_component__hourly_volume_partial_q2=0,
            lecturing_component__planned_classes=1,
            practical_component__repartition_volume_requirement_entity=10,
            practical_component__repartition_volume_additional_entity_1=5,
            practical_component__hourly_volume_total_annual=40,
            practical_component__hourly_volume_partial_q1=40,
            practical_component__hourly_volume_partial_q2=0,
            practical_component__planned_classes=1,
        )
        cls.learning_container_year = cls.learning_unit_year.learning_container_year

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
        another_learning_unit_year.language = FrenchLanguageFactory()
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
        # Copy the same container and entities + change academic year
        another_learning_container_year = _build_copy(self.learning_container_year)
        another_learning_container_year.academic_year = self.next_academic_year
        another_learning_container_year.save()

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
        next_year_learning_unit_year = LearningUnitYearWithComponentsFactory(
            learning_unit=self.learning_unit_year.learning_unit,
            learning_container_year__acronym=self.learning_unit_year.acronym,
            acronym=self.learning_unit_year.acronym,
            academic_year=self.next_academic_year,
            lecturing_component__repartition_volume_requirement_entity=30,
            lecturing_component__repartition_volume_additional_entity_1=10,
            lecturing_component__hourly_volume_total_annual=40,
            lecturing_component__hourly_volume_partial_q1=40,
            lecturing_component__hourly_volume_partial_q2=0,
            lecturing_component__planned_classes=1,
            practical_component__repartition_volume_requirement_entity=10,
            practical_component__repartition_volume_additional_entity_1=5,
            practical_component__hourly_volume_total_annual=40,
            practical_component__hourly_volume_partial_q1=40,
            practical_component__hourly_volume_partial_q2=0,
            practical_component__planned_classes=1,
        )

        error_list = business_edition._check_postponement_conflict_on_entity_container_year(
            self.learning_container_year,
            next_year_learning_unit_year.learning_container_year
        )

        self.assertIsInstance(error_list, list)
        self.assertEqual(len(error_list), 4)

        generic_error = "The value of field '%(field)s' is different between year %(year)s - %(value)s " \
                        "and year %(next_year)s - %(next_value)s"
        # Error : Requirement entity diff
        error_requirement_entity = _(generic_error) % {
            'field': _(entity_container_year_link_type.REQUIREMENT_ENTITY.lower()),
            'year': self.learning_container_year.academic_year,
            'value': self.learning_unit_year.learning_container_year.requirement_entity.most_recent_acronym,
            'next_year': next_year_learning_unit_year.learning_container_year.academic_year,
            'next_value': next_year_learning_unit_year.learning_container_year.requirement_entity.most_recent_acronym
        }
        self.assertIn(error_requirement_entity, error_list)

        # Error : Additional requirement entity diff
        error_requirement_entity = _(generic_error) % {
            'field': _(entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1.lower()),
            'year': self.learning_container_year.academic_year,
            'value': self.learning_container_year.additional_entity_1.most_recent_acronym,
            'next_year': next_year_learning_unit_year.academic_year,
            'next_value': _('No data')
        }
        self.assertIn(error_requirement_entity, error_list)

    def test_check_postponement_conflict_on_volumes_case_no_diff(self):
        next_year_learning_unit_year = LearningUnitYearWithComponentsFactory(
            learning_unit=self.learning_unit_year.learning_unit,
            learning_container_year__acronym=self.learning_unit_year.acronym,
            acronym=self.learning_unit_year.acronym,
            academic_year=self.next_academic_year,
            lecturing_component__repartition_volume_requirement_entity=30,
            lecturing_component__repartition_volume_additional_entity_1=10,
            lecturing_component__hourly_volume_total_annual=40,
            lecturing_component__hourly_volume_partial_q1=40,
            lecturing_component__hourly_volume_partial_q2=0,
            lecturing_component__planned_classes=1,
            practical_component__repartition_volume_requirement_entity=10,
            practical_component__repartition_volume_additional_entity_1=5,
            practical_component__hourly_volume_total_annual=40,
            practical_component__hourly_volume_partial_q1=40,
            practical_component__hourly_volume_partial_q2=0,
            practical_component__planned_classes=1,
        )
        next_year_learning_container_year = next_year_learning_unit_year.learning_container_year
        error_list = business_edition._check_postponement_conflict_on_volumes(
            self.learning_container_year,
            next_year_learning_container_year
        )
        self.assertIsInstance(error_list, list)
        self.assertFalse(error_list)

    def test_check_postponement_conflict_on_volumes_multiples_differences(self):
        next_year_learning_unit_year = LearningUnitYearWithComponentsFactory(
            learning_unit=self.learning_unit_year.learning_unit,
            learning_container_year__acronym=self.learning_unit_year.acronym,
            acronym=self.learning_unit_year.acronym,
            academic_year=self.next_academic_year,
            lecturing_component__hourly_volume_total_annual=Decimal(50),
            lecturing_component__hourly_volume_partial_q1=Decimal(35),
            lecturing_component__hourly_volume_partial_q2=Decimal(15),
            lecturing_component__repartition_volume_requirement_entity=Decimal(30),
            lecturing_component__repartition_volume_additional_entity_1=Decimal(20),
            lecturing_component__planned_classes=1,
            practical_component__hourly_volume_total_annual=Decimal(50),
            practical_component__hourly_volume_partial_q1=Decimal(35),
            practical_component__hourly_volume_partial_q2=Decimal(15),
            practical_component__repartition_volume_requirement_entity=Decimal(10),
            practical_component__repartition_volume_additional_entity_1=Decimal(10),
            practical_component__planned_classes=1

        )
        next_year_learning_container_year = next_year_learning_unit_year.learning_container_year

        LearningComponentYear.objects.filter(
            learning_unit_year=self.learning_unit_year
        ).update(
            hourly_volume_total_annual=Decimal(60),
            hourly_volume_partial_q1=Decimal(40),
            hourly_volume_partial_q2=Decimal(20)
        )

        error_list = business_edition._check_postponement_conflict_on_volumes(
            self.learning_container_year,
            next_year_learning_container_year
        )
        self.assertIsInstance(error_list, list)
        self.assertEqual(len(error_list), 10)

        tests_cases = [
            {'field': VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1, 'value': Decimal(10), 'next_value': Decimal(20)},
            {'field': VOLUME_TOTAL, 'value': Decimal(60), 'next_value': Decimal(50)},
            {'field': VOLUME_Q1, 'value': Decimal(40), 'next_value': Decimal(35)},
            {'field': VOLUME_Q2, 'value': Decimal(20), 'next_value': Decimal(15)}
        ]
        for test in tests_cases:
            with self.subTest(test=test):
                error_expected = (_("The value of field '%(field)s' for the learning unit %(acronym)s "
                                    "(%(component_type)s) is different between year %(year)s - %(value)s and year "
                                    "%(next_year)s - %(next_value)s") %
                                  {
                                      'field': COMPONENT_DETAILS[test.get('field')].lower(),
                                      'acronym': next_year_learning_container_year.acronym,
                                      'component_type': _(
                                          dict(COMPONENT_TYPES)[learning_component_year_type.LECTURING]),
                                      'year': self.learning_container_year.academic_year,
                                      'value': test.get('value'),
                                      'next_year': next_year_learning_container_year.academic_year,
                                      'next_value': test.get('next_value'),
                                  })
                self.assertIn(error_expected, error_list)

    def test_check_postponement_conflict_on_volumes_case_no_lecturing_component_next_year(self):
        """ The goal of this test is to ensure that there is an error IF the learning unit year on current year have
           component LECTURING that the learning unit year on the next year doesn't have """

        next_year_learning_unit_year = LearningUnitYearWithComponentsFactory(
            learning_unit=self.learning_unit_year.learning_unit,
            learning_container_year__acronym=self.learning_unit_year.acronym,
            acronym=self.learning_unit_year.acronym,
            academic_year=self.next_academic_year,
            lecturing_component=None,
            practical_component__repartition_volume_requirement_entity=10,
            practical_component__repartition_volume_additional_entity_1=5,
            practical_component__hourly_volume_total_annual=40,
            practical_component__hourly_volume_partial_q1=40,
            practical_component__hourly_volume_partial_q2=0,
            practical_component__planned_classes=1,
        )
        _delete_components(next_year_learning_unit_year, learning_component_year_type.LECTURING)

        error_list = business_edition._check_postponement_conflict_on_volumes(
            self.learning_container_year,
            next_year_learning_unit_year.learning_container_year
        )
        self.assertIsInstance(error_list, list)
        self.assertEqual(len(error_list), 1)
        error_expected = _("There is not %(component_type)s for the learning unit %(acronym)s - %(year)s but exist "
                           "in %(existing_year)s") % {
                             'component_type': _(learning_component_year_type.LECTURING),
                             'acronym': self.learning_unit_year.acronym,
                             'year': self.next_academic_year,
                             'existing_year': self.learning_container_year.academic_year
                         }
        self.assertIn(error_expected, error_list)

    def test_check_postponement_conflict_on_volumes_case_no_practical_exercise_component_current_year(self):
        """ The goal of this test is to ensure that there is an error IF the learning unit year on next year have
            component PRACTICAL EXERCISES that the learning unit year on the current year doesn't have """
        next_year_learning_unit_year = LearningUnitYearWithComponentsFactory(
            learning_unit=self.learning_unit_year.learning_unit,
            learning_container_year__acronym=self.learning_unit_year.acronym,
            acronym=self.learning_unit_year.acronym,
            academic_year=self.next_academic_year,
            lecturing_component__repartition_volume_requirement_entity=30,
            lecturing_component__repartition_volume_additional_entity_1=10,
            lecturing_component__hourly_volume_total_annual=40,
            lecturing_component__hourly_volume_partial_q1=40,
            lecturing_component__hourly_volume_partial_q2=0,
            lecturing_component__planned_classes=1,
            practical_component__repartition_volume_requirement_entity=10,
            practical_component__repartition_volume_additional_entity_1=5,
            practical_component__hourly_volume_total_annual=40,
            practical_component__hourly_volume_partial_q1=40,
            practical_component__hourly_volume_partial_q2=0,
            practical_component__planned_classes=1,
        )
        next_year_learning_container_year = next_year_learning_unit_year.learning_container_year

        _delete_components(self.learning_unit_year, learning_component_year_type.PRACTICAL_EXERCISES)

        error_list = business_edition._check_postponement_conflict_on_volumes(
            self.learning_container_year,
            next_year_learning_container_year
        )
        self.assertIsInstance(error_list, list)
        self.assertEqual(len(error_list), 1)
        error_expected = _("There is not %(component_type)s for the learning unit %(acronym)s - %(year)s but exist "
                           "in %(existing_year)s") % {
                             'component_type': _(learning_component_year_type.PRACTICAL_EXERCISES),
                             'acronym': self.learning_unit_year.acronym,
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

        an_entity = EntityFactory()
        EntityVersionFactory(entity=an_entity, parent=None, end_date=None, acronym="AREC")
        another_learning_container_year.requirement_entity = an_entity
        another_learning_container_year.save()

        error_list = business_edition._check_postponement_conflict(self.learning_unit_year, another_learning_unit_year)
        self.assertIsInstance(error_list, list)
        self.assertEqual(len(error_list), 5)

    def test_extends_only_components_of_learning_unit_year(self):
        # Creating partim with components for the same learningContainerYear
        _create_learning_unit_year_with_components(self.learning_container_year,
                                                   create_lecturing_component=True,
                                                   create_pratical_component=True,
                                                   subtype=learning_unit_year_subtypes.PARTIM)

        inital_components_count = LearningComponentYear.objects.all().count()
        number_of_components = LearningComponentYear.objects.filter(learning_unit_year=self.learning_unit_year).count()
        expected_count = inital_components_count + number_of_components
        next_year = self.academic_year.year + 1

        business_edition.duplicate_learning_unit_year(self.learning_unit_year, AcademicYearFactory(year=next_year))

        # assert components of partims are not duplicated too
        self.assertEqual(LearningComponentYear.objects.all().count(), expected_count)


def _create_learning_unit_year_with_components(l_container, create_lecturing_component=True,
                                               create_pratical_component=True, subtype=None):
    if not subtype:
        subtype = learning_unit_year_subtypes.FULL
    language = EnglishLanguageFactory()
    a_learning_unit_year = LearningUnitYearFactory(learning_container_year=l_container,
                                                   acronym=l_container.acronym,
                                                   academic_year=l_container.academic_year,
                                                   status=True,
                                                   language=language,
                                                   campus=CampusFactory(name='MIT'),
                                                   subtype=subtype)

    if create_lecturing_component:
        LearningComponentYearFactory(
            learning_unit_year=a_learning_unit_year,
            type=learning_component_year_type.LECTURING,
            planned_classes=1
        )

    if create_pratical_component:
        LearningComponentYearFactory(
            learning_unit_year=a_learning_unit_year,
            type=learning_component_year_type.PRACTICAL_EXERCISES,
            planned_classes=1
        )

    return a_learning_unit_year


def _create_entity_container_with_components(a_learning_unit_year, entity_container_type, an_entity,
                                             repartition_lecturing=None, repartition_practical_exercises=None):
    container = a_learning_unit_year.learning_container_year
    container.set_entity(entity_container_type, an_entity)
    container.save()

    if repartition_lecturing is not None:
        _create_component_year(
            a_learning_unit_year,
            learning_component_year_type.LECTURING,
            entity_container_type,
            repartition_lecturing
        )

    if repartition_practical_exercises is not None:
        _create_component_year(
            a_learning_unit_year,
            learning_component_year_type.PRACTICAL_EXERCISES,
            entity_container_type,
            repartition_practical_exercises
        )
    return an_entity


def _create_component_year(luy, component_type, entity_container_type, repartition_volume):
    component = LearningComponentYear.objects.get(
        learning_unit_year=luy, type=component_type
    )
    component.set_repartition_volume(entity_container_type, repartition_volume)
    component.save()


def _delete_components(luy, component_type):
    LearningComponentYear.objects.filter(learning_unit_year=luy, type=component_type).delete()


def _build_copy(instance):
    instance_copy = deepcopy(instance)
    instance_copy.pk = None
    instance_copy.uuid = uuid4()
    return instance_copy
