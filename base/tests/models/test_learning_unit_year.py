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
from django.utils.translation import ugettext_lazy as _

from attribution.models import attribution
from base.models import learning_unit_year
from base.models.entity_component_year import EntityComponentYear
from base.models.enums import learning_unit_year_subtypes
from base.models.enums.entity_container_year_link_type import REQUIREMENT_ENTITY
from base.models.enums.learning_component_year_type import LECTURING, PRACTICAL_EXERCISES
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_unit_year import find_max_credits_of_related_partims
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.business.learning_units import GenerateAcademicYear, GenerateContainer
from base.tests.factories.external_learning_unit_year import ExternalLearningUnitYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory, create_learning_units_year
from base.tests.factories.tutor import TutorFactory


class LearningUnitYearTest(TestCase):
    def setUp(self):
        self.tutor = TutorFactory()
        self.academic_year = create_current_academic_year()
        self.learning_unit_year = LearningUnitYearFactory(acronym="LDROI1004",
                                                          specific_title="Juridic law courses",
                                                          academic_year=self.academic_year,
                                                          subtype=learning_unit_year_subtypes.FULL)

    def test_find_by_tutor_with_none_argument(self):
        self.assertEqual(attribution.find_by_tutor(None), None)

    def test_subdivision_computation(self):
        l_container_year = LearningContainerYearFactory(acronym="LBIR1212", academic_year=self.academic_year)
        l_unit_1 = LearningUnitYearFactory(acronym="LBIR1212", learning_container_year=l_container_year,
                                           academic_year=self.academic_year)
        l_unit_2 = LearningUnitYearFactory(acronym="LBIR1212A", learning_container_year=l_container_year,
                                           academic_year=self.academic_year)
        l_unit_3 = LearningUnitYearFactory(acronym="LBIR1212B", learning_container_year=l_container_year,
                                           academic_year=self.academic_year)

        self.assertFalse(l_unit_1.subdivision)
        self.assertEqual(l_unit_2.subdivision, 'A')
        self.assertEqual(l_unit_3.subdivision, 'B')

    def test_search_acronym_by_regex(self):
        regex_valid = '^LD.+1+'
        query_result_valid = learning_unit_year.search(acronym=regex_valid)
        self.assertEqual(len(query_result_valid), 1)
        self.assertEqual(self.learning_unit_year.acronym, query_result_valid[0].acronym)

    def test_property_in_charge(self):
        self.assertFalse(self.learning_unit_year.in_charge)

        a_container_year = LearningContainerYearFactory(acronym=self.learning_unit_year.acronym,
                                                        academic_year=self.academic_year)
        self.learning_unit_year.learning_container_year = a_container_year

        self.assertFalse(self.learning_unit_year.in_charge)

        a_container_year.in_charge = True

        self.assertTrue(self.learning_unit_year.in_charge)

    def test_find_gte_learning_units_year(self):
        learning_unit = LearningUnitFactory()
        dict_learning_unit_year = create_learning_units_year(2000, 2017, learning_unit)

        selected_learning_unit_year = dict_learning_unit_year[2007]

        result = list(selected_learning_unit_year.find_gte_learning_units_year().values_list('academic_year__year',
                                                                                             flat=True))
        self.assertListEqual(result, list(range(2007,2018)))

    def test_find_gte_learning_units_year_case_no_future(self):
        learning_unit = LearningUnitFactory()
        dict_learning_unit_year = create_learning_units_year(2000, 2017, learning_unit)

        selected_learning_unit_year = dict_learning_unit_year[2017]

        result = list(selected_learning_unit_year.find_gte_learning_units_year().values_list('academic_year__year',
                                                                                             flat=True))
        self.assertEqual(result, [2017])

    def test_find_gt_learning_unit_year(self):
        learning_unit = LearningUnitFactory()
        dict_learning_unit_year = create_learning_units_year(2000, 2017, learning_unit)

        selected_learning_unit_year = dict_learning_unit_year[2007]

        result = list(selected_learning_unit_year.find_gt_learning_units_year().values_list('academic_year__year',
                                                                                             flat=True))
        self.assertListEqual(result, list(range(2008, 2018)))

    def test_find_gt_learning_units_year_case_no_future(self):
        learning_unit = LearningUnitFactory()
        dict_learning_unit_year = create_learning_units_year(2000, 2017, learning_unit)

        selected_learning_unit_year = dict_learning_unit_year[2017]

        result = list(selected_learning_unit_year.find_gt_learning_units_year().values_list('academic_year__year',
                                                                                             flat=True))
        self.assertEqual(result, [])

    def test_get_learning_unit_parent(self):
        lunit_container_year = LearningContainerYearFactory(academic_year=self.academic_year, acronym='LBIR1230')
        luy_parent = LearningUnitYearFactory(academic_year=self.academic_year, acronym='LBIR1230',
                                             learning_container_year=lunit_container_year,
                                             subtype=learning_unit_year_subtypes.FULL)
        luy_partim = LearningUnitYearFactory(academic_year=self.academic_year, acronym='LBIR1230B',
                                             learning_container_year=lunit_container_year,
                                             subtype=learning_unit_year_subtypes.PARTIM)
        self.assertEqual(luy_partim.parent, luy_parent)

    def test_get_learning_unit_parent_without_parent(self):
        lunit_container_year = LearningContainerYearFactory(academic_year=self.academic_year, acronym='LBIR1230')
        luy_parent = LearningUnitYearFactory(academic_year=self.academic_year, acronym='LBIR1230',
                                             learning_container_year=lunit_container_year,
                                             subtype=learning_unit_year_subtypes.FULL)
        self.assertIsNone(luy_parent.parent)

    def test_search_by_title(self):
        common_part = "commun"
        a_common_title = "Titre {}".format(common_part)
        a_specific_title = "Specific title {}".format(common_part)
        lunit_container_yr = LearningContainerYearFactory(academic_year=self.academic_year,
                                                          common_title=a_common_title)
        luy = LearningUnitYearFactory(academic_year=self.academic_year,
                                      specific_title=a_specific_title,
                                      learning_container_year=lunit_container_yr)

        self.assertEqual(learning_unit_year.search(title="{} en plus".format(a_common_title)).count(), 0)
        self.assertEqual(learning_unit_year.search(title=a_common_title)[0], luy)
        self.assertEqual(learning_unit_year.search(title=common_part)[0], luy)
        self.assertEqual(learning_unit_year.search(title=a_specific_title)[0], luy)


    def test_find_max_credits_of_partims(self):
        self.partim_1 = LearningUnitYearFactory(academic_year=self.academic_year,
                                                learning_container_year=self.learning_unit_year.learning_container_year,
                                                subtype=learning_unit_year_subtypes.PARTIM, credits=15)
        self.partim_2 = LearningUnitYearFactory(academic_year=self.academic_year,
                                                learning_container_year=self.learning_unit_year.learning_container_year,
                                                subtype=learning_unit_year_subtypes.PARTIM, credits=20)
        max_credits = find_max_credits_of_related_partims(self.learning_unit_year)
        self.assertEqual(max_credits, 20)

    def test_find_max_credits_of_partims_when_no_partims_related(self):
        max_credits = find_max_credits_of_related_partims(self.learning_unit_year)
        self.assertEqual(max_credits, None)

    def test_ccomplete_title_when_no_learning_container_year(self):
        specific_title = 'part 1: Vertebrate'

        luy = LearningUnitYearFactory(specific_title=specific_title, learning_container_year=None)
        self.assertEqual(luy.complete_title, specific_title)

    def test_complete_title_property_case_common_title_is_empty(self):
        specific_title = 'part 1: Vertebrate'

        luy = LearningUnitYearFactory(specific_title=specific_title, learning_container_year__common_title="")
        self.assertEqual(luy.complete_title, specific_title)

        luy = LearningUnitYearFactory(specific_title=specific_title, learning_container_year__common_title=None)
        self.assertEqual(luy.complete_title, specific_title)

    def test_complete_title_property_case_common_and_specific_title_are_set(self):
        specific_title = 'part 1: Vertebrate'
        common_title = 'Zoology'

        luy = LearningUnitYearFactory(specific_title=specific_title, learning_container_year__common_title=common_title)
        self.assertEqual(luy.complete_title, '{} {}'.format(common_title, specific_title))

    def test_common_title_property(self):
        self.assertEqual(self.learning_unit_year.container_common_title,
                         self.learning_unit_year.learning_container_year.common_title)

    def test_common_title_property_no_container(self):
        self.learning_unit_year.learning_container_year = None
        self.assertEqual(self.learning_unit_year.container_common_title, '')

    def test_can_be_updated_by_faculty_manager(self):
        previous_academic_years = GenerateAcademicYear(start_year=self.academic_year.year-3,
                                                       end_year=self.academic_year.year-1).academic_years
        next_academic_years = GenerateAcademicYear(start_year=self.academic_year.year+1,
                                                   end_year=self.academic_year.year+3).academic_years
        previous_luys = [LearningUnitYearFactory(academic_year=ac, learning_unit=self.learning_unit_year.learning_unit)
                         for ac in previous_academic_years]
        next_luys = [LearningUnitYearFactory(academic_year=ac, learning_unit=self.learning_unit_year.learning_unit)
                     for ac in next_academic_years]

        for luy in previous_luys:
            self.assertFalse(luy.can_update_by_faculty_manager())

        self.assertTrue(self.learning_unit_year.can_update_by_faculty_manager())
        self.assertTrue(next_luys[0].can_update_by_faculty_manager())
        self.assertTrue(next_luys[1].can_update_by_faculty_manager())

        self.assertFalse(next_luys[2].can_update_by_faculty_manager())

    def test_is_external(self):
        luy = LearningUnitYearFactory()
        ExternalLearningUnitYearFactory(learning_unit_year=luy)
        self.assertTrue(luy.is_external())

    def test_is_not_external(self):
        luy = LearningUnitYearFactory()
        self.assertFalse(luy.is_external())


class LearningUnitYearWarningsTest(TestCase):
    def setUp(self):
        self.start_year = 2010
        self.end_year = 2020
        self.generated_ac_years = GenerateAcademicYear(self.start_year, self.end_year)
        self.generated_container = GenerateContainer(self.start_year, self.end_year)
        self.luy_full = self.generated_container.generated_container_years[0].learning_unit_year_full
        self.learning_component_year_full_lecturing = LearningComponentYear.objects.filter(
            type=LECTURING,
            learningunitcomponent__learning_unit_year=self.luy_full
        ).first()
        self.entity_component_year_full_lecturing_requirement = EntityComponentYear.objects.get(
            learning_component_year=self.learning_component_year_full_lecturing,
            entity_container_year__type=REQUIREMENT_ENTITY
        )

    def test_warning_volumes_vol_tot(self):
        self.learning_component_year_full_lecturing.hourly_volume_partial_q1 = 15.0
        self.learning_component_year_full_lecturing.hourly_volume_partial_q2 = 15.0
        self.learning_component_year_full_lecturing.hourly_volume_total_annual = 40.0
        self.learning_component_year_full_lecturing.planned_classes = 1
        self.learning_component_year_full_lecturing.save()

        self.entity_component_year_full_lecturing_requirement.repartition_volume = 30.0
        self.entity_component_year_full_lecturing_requirement.save()

        excepted_error = "{} ({})".format(_('Volumes are inconsistent'), _('Vol_tot is not equal to vol_q1 + vol_q2'))
        self.assertIn(excepted_error, self.learning_component_year_full_lecturing.warnings)
        self.assertIn(excepted_error, self.luy_full.warnings)

    def test_warning_volumes_vol_global(self):
        self.learning_component_year_full_lecturing.hourly_volume_partial_q1 = 15.0
        self.learning_component_year_full_lecturing.hourly_volume_partial_q2 = 15.0
        self.learning_component_year_full_lecturing.hourly_volume_total_annual = 30.0
        self.learning_component_year_full_lecturing.planned_classes = 1
        self.learning_component_year_full_lecturing.save()

        self.entity_component_year_full_lecturing_requirement.repartition_volume = 40.0
        self.entity_component_year_full_lecturing_requirement.save()

        excepted_error = "{} ({})".format(
            _('Volumes are inconsistent'), _('Vol_global is not equal to Vol_tot * planned_classes'))
        self.assertIn(excepted_error, self.learning_component_year_full_lecturing.warnings)
        self.assertIn(excepted_error, self.luy_full.warnings)

    def test_warning_volumes_vol_global_and_total(self):
        self.entity_component_year_full_lecturing_requirement.repartition_volume = 42.0
        self.entity_component_year_full_lecturing_requirement.save()

        self.learning_component_year_full_lecturing.hourly_volume_partial_q1 = 10.0
        self.learning_component_year_full_lecturing.hourly_volume_partial_q2 = 15.0
        self.learning_component_year_full_lecturing.hourly_volume_total_annual = 36.0
        self.learning_component_year_full_lecturing.planned_classes = 2
        self.learning_component_year_full_lecturing.save()

        excepted_error_1 = "{} ({})".format(
            _('Volumes are inconsistent'), _('Vol_global is not equal to Vol_tot * planned_classes'))
        self.assertIn(excepted_error_1, self.learning_component_year_full_lecturing.warnings)
        self.assertIn(excepted_error_1, self.luy_full.warnings)

        excepted_error_2 = "{} ({})".format(_('Volumes are inconsistent'), _('Vol_tot is not equal to vol_q1 + vol_q2'))
        self.assertIn(excepted_error_2, self.learning_component_year_full_lecturing.warnings)
        self.assertIn(excepted_error_2, self.luy_full.warnings)

    def test_warning_volumes_no_warning(self):
        self.luy_full.credits = self.luy_full.credits + 1
        self.luy_full.save()

        test_cases = [
            {'vol_q1': 15, 'vol_q2': 15, 'vol_tot_annual': 30, 'planned_classes': 1, 'vol_tot_global': 30},
            {'vol_q1': 10, 'vol_q2': 20, 'vol_tot_annual': 30, 'planned_classes': 2, 'vol_tot_global': 60}
        ]

        for case in test_cases:
            with self.subTest(case=case):
                self.learning_component_year_full_lecturing.hourly_volume_partial_q1 = case.get('vol_q1')
                self.learning_component_year_full_lecturing.hourly_volume_partial_q2 = case.get('vol_q2')
                self.learning_component_year_full_lecturing.hourly_volume_total_annual = case.get('vol_tot_annual')
                self.learning_component_year_full_lecturing.planned_classes = case.get('planned_classes')
                self.learning_component_year_full_lecturing.save()

                self.entity_component_year_full_lecturing_requirement.repartition_volume = case.get('vol_tot_global')
                self.entity_component_year_full_lecturing_requirement.save()

                self.assertFalse(self.learning_component_year_full_lecturing.warnings)
                self.assertFalse(self.luy_full.warnings)

    def test_warning_all_volumes_partim_greater_than_full(self):
        luy_partim = self.generated_container.generated_container_years[0].learning_unit_year_partim
        learning_component_year_partim_lecturing = LearningComponentYear.objects.filter(
            type=LECTURING,
            learningunitcomponent__learning_unit_year=luy_partim
        ).first()
        entity_component_year_partim_lecturing_requirement = EntityComponentYear.objects.get(
            learning_component_year=learning_component_year_partim_lecturing,
            entity_container_year__type=REQUIREMENT_ENTITY
        )

        self.learning_component_year_full_lecturing.hourly_volume_partial_q1 = 15.0
        self.learning_component_year_full_lecturing.hourly_volume_partial_q2 = 15.0
        self.learning_component_year_full_lecturing.hourly_volume_total_annual = 30.0
        self.learning_component_year_full_lecturing.planned_classes = 1
        self.learning_component_year_full_lecturing.save()
        self.entity_component_year_full_lecturing_requirement.repartition_volume = 30.0
        self.entity_component_year_full_lecturing_requirement.save()

        learning_component_year_partim_lecturing.hourly_volume_partial_q1 = 20.0
        learning_component_year_partim_lecturing.hourly_volume_partial_q2 = 20.0
        learning_component_year_partim_lecturing.hourly_volume_total_annual = 40.0
        learning_component_year_partim_lecturing.planned_classes = 2
        learning_component_year_partim_lecturing.save()
        entity_component_year_partim_lecturing_requirement.repartition_volume = 80.0
        entity_component_year_partim_lecturing_requirement.save()

        excepted_error = "{} ({})".format(
            _('Volumes are inconsistent'),
            _('At least a partim volume value is greater than corresponding volume of parent'))
        self.assertIn(excepted_error, self.luy_full.learning_container_year.warnings)
        self.assertIn(excepted_error, self.luy_full.warnings)
        self.assertIn(excepted_error, luy_partim.warnings)

    def test_warning_one_volume_partim_greater_than_full(self):
        luy_partim = self.generated_container.generated_container_years[0].learning_unit_year_partim
        learning_component_year_partim_lecturing = LearningComponentYear.objects.filter(
            type=LECTURING,
            learningunitcomponent__learning_unit_year=luy_partim
        ).first()
        entity_component_year_partim_lecturing_requirement = EntityComponentYear.objects.get(
            learning_component_year=learning_component_year_partim_lecturing,
            entity_container_year__type=REQUIREMENT_ENTITY
        )

        self.learning_component_year_full_lecturing.hourly_volume_partial_q1 = 15.0
        self.learning_component_year_full_lecturing.hourly_volume_partial_q2 = 15.0
        self.learning_component_year_full_lecturing.hourly_volume_total_annual = 30.0
        self.learning_component_year_full_lecturing.planned_classes = 1
        self.learning_component_year_full_lecturing.save()
        self.entity_component_year_full_lecturing_requirement.repartition_volume = 30.0
        self.entity_component_year_full_lecturing_requirement.save()

        learning_component_year_partim_lecturing.hourly_volume_partial_q1 = 10.0
        learning_component_year_partim_lecturing.hourly_volume_partial_q2 = 10.0
        learning_component_year_partim_lecturing.hourly_volume_total_annual = 20.0
        learning_component_year_partim_lecturing.planned_classes = 1
        learning_component_year_partim_lecturing.save()
        entity_component_year_partim_lecturing_requirement.repartition_volume = 80.0
        entity_component_year_partim_lecturing_requirement.save()

        excepted_error = "{} ({})".format(
            _('Volumes are inconsistent'),
            _('At least a partim volume value is greater than corresponding volume of parent'))
        self.assertIn(excepted_error, self.luy_full.learning_container_year.warnings)
        self.assertIn(excepted_error, self.luy_full.warnings)
        self.assertIn(excepted_error, luy_partim.warnings)

    def test_no_warning_when_volumes_ok_but_other_component_of_partim_has_higher_values(self):
        self.luy_full.credits = self.luy_full.credits + 1
        self.luy_full.save()

        luy_partim = self.generated_container.generated_container_years[0].learning_unit_year_partim

        learning_component_year_partim_lecturing = LearningComponentYear.objects.filter(
            type=LECTURING,
            learningunitcomponent__learning_unit_year=luy_partim
        ).first()
        entity_component_year_partim_lecturing_requirement = EntityComponentYear.objects.get(
            learning_component_year=learning_component_year_partim_lecturing,
            entity_container_year__type=REQUIREMENT_ENTITY
        )

        learning_component_year_partim_practical = LearningComponentYear.objects.filter(
            type=PRACTICAL_EXERCISES,
            learningunitcomponent__learning_unit_year=luy_partim
        ).first()
        entity_component_year_partim_lecturing_practical = EntityComponentYear.objects.get(
            learning_component_year=learning_component_year_partim_practical,
            entity_container_year__type=REQUIREMENT_ENTITY
        )

        learning_component_year_full_practical = LearningComponentYear.objects.filter(
            type=PRACTICAL_EXERCISES,
            learningunitcomponent__learning_unit_year=self.luy_full
        ).first()
        entity_component_year_full_practical = EntityComponentYear.objects.get(
            learning_component_year=learning_component_year_full_practical,
            entity_container_year__type=REQUIREMENT_ENTITY
        )

        self.learning_component_year_full_lecturing.hourly_volume_partial_q1 = 15.0
        self.learning_component_year_full_lecturing.hourly_volume_partial_q2 = 15.0
        self.learning_component_year_full_lecturing.hourly_volume_total_annual = 30.0
        self.learning_component_year_full_lecturing.planned_classes = 1
        self.learning_component_year_full_lecturing.save()
        self.entity_component_year_full_lecturing_requirement.repartition_volume = 30.0
        self.entity_component_year_full_lecturing_requirement.save()

        learning_component_year_partim_lecturing.hourly_volume_partial_q1 = 10.0
        learning_component_year_partim_lecturing.hourly_volume_partial_q2 = 10.0
        learning_component_year_partim_lecturing.hourly_volume_total_annual = 20.0
        learning_component_year_partim_lecturing.planned_classes = 1
        learning_component_year_partim_lecturing.save()
        entity_component_year_partim_lecturing_requirement.repartition_volume = 20.0
        entity_component_year_partim_lecturing_requirement.save()

        learning_component_year_full_practical.hourly_volume_partial_q1 = 10.0
        learning_component_year_full_practical.hourly_volume_partial_q2 = 15.0
        learning_component_year_full_practical.hourly_volume_total_annual = 25.0
        learning_component_year_full_practical.planned_classes = 1
        learning_component_year_full_practical.save()
        entity_component_year_full_practical.repartition_volume = 25.0
        entity_component_year_full_practical.save()

        learning_component_year_partim_practical.hourly_volume_partial_q1 = 10.0
        learning_component_year_partim_practical.hourly_volume_partial_q2 = 10.0
        learning_component_year_partim_practical.hourly_volume_total_annual = 20.0
        learning_component_year_partim_practical.planned_classes = 1
        learning_component_year_partim_practical.save()
        entity_component_year_partim_lecturing_practical.repartition_volume = 25.0
        entity_component_year_partim_lecturing_practical.save()

        self.assertFalse(self.luy_full.learning_container_year.warnings)
        self.assertFalse(self.luy_full.warnings)
