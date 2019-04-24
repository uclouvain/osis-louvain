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
from datetime import date

from decimal import Decimal
from django.test import TestCase

from base.models.enums import learning_component_year_type, learning_unit_year_subtypes

from attribution.business import attribution_json
from attribution.models.enums import function
from attribution.tests.factories.attribution import AttributionNewFactory
from attribution.tests.factories.attribution_charge_new import AttributionChargeNewFactory
from base.models.learning_component_year import LearningComponentYear
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.tutor import TutorFactory


class AttributionJsonTest(TestCase):
    def setUp(self):
        today = date.today()
        self.academic_year = AcademicYearFactory(year=today.year, start_date=today)

        # Creation Container / UE and components related
        self.l_container = LearningContainerYearFactory(academic_year=self.academic_year, acronym="LBIR1210",
                                                        in_charge=True)
        self.learning_unit_yr = _create_learning_unit_year_with_components(
            academic_year=self.academic_year,
            l_container=self.l_container,
            acronym="LBIR1210",
            subtype=learning_unit_year_subtypes.FULL
        )

        _create_learning_unit_year_with_components(academic_year=self.academic_year, l_container=self.l_container,
                                                   acronym="LBIR1210A", subtype=learning_unit_year_subtypes.PARTIM)
        _create_learning_unit_year_with_components(academic_year=self.academic_year, l_container=self.l_container,
                                                   acronym="LBIR1210B", subtype=learning_unit_year_subtypes.PARTIM)

        # Creation Tutors
        self.tutor_1 = TutorFactory(person=PersonFactory(first_name="Tom", last_name="Dupont", global_id='00012345'))
        self.tutor_2 = TutorFactory(person=PersonFactory(first_name="Paul", last_name="Durant", global_id='08923545'))

        # Creation Attribution and Attributions Charges - Tutor 1 - Holder
        attribution_tutor_1 = AttributionNewFactory(learning_container_year=self.l_container, tutor=self.tutor_1,
                                                    function=function.HOLDER)
        _create_attribution_charge(self.academic_year, attribution_tutor_1, "LBIR1210", Decimal(15.5), Decimal(10))
        _create_attribution_charge(self.academic_year, attribution_tutor_1, "LBIR1210A", None, Decimal(5))

        # Creation Attribution and Attributions Charges - Tutor 2 - Co-holder
        attribution_tutor_2 = AttributionNewFactory(learning_container_year=self.l_container, tutor=self.tutor_2,
                                                    function=function.CO_HOLDER)
        _create_attribution_charge(self.academic_year, attribution_tutor_2, "LBIR1210B", Decimal(7.5))

    def test_build_attributions_json(self):
        attrib_list = attribution_json._compute_list()
        self.assertIsInstance(attrib_list, list)
        self.assertEqual(len(attrib_list), 2)

        attrib_tutor_1 = next(
            (attrib for attrib in attrib_list if attrib['global_id'] == self.tutor_1.person.global_id),
            None)
        self.assertTrue(attrib_tutor_1)
        self.assertEqual(len(attrib_tutor_1['attributions']), 2)

        #Check if attribution is correct
        attrib_tutor_2 = next(
            (attrib for attrib in attrib_list if attrib['global_id'] == self.tutor_2.person.global_id),
            None)
        self.assertTrue(attrib_tutor_2)
        self.assertEqual(len(attrib_tutor_2['attributions']), 1)
        self.assertEqual(attrib_tutor_2['attributions'][0]['acronym'], "LBIR1210B")
        self.assertEqual(attrib_tutor_2['attributions'][0]['function'], function.CO_HOLDER)
        self.assertEqual(attrib_tutor_2['attributions'][0][learning_component_year_type.LECTURING], "7.5")
        self.assertRaises(KeyError, lambda: attrib_tutor_2['attributions'][0][learning_component_year_type.PRACTICAL_EXERCISES + '_CHARGE'])

    def test_learning_unit_in_charge_false(self):
        self.l_container.in_charge = False
        self.l_container.save()

        attrib_list = attribution_json._compute_list()
        self.assertIsInstance(attrib_list, list)
        self.assertEqual(len(attrib_list), 2)

        attrib_tutor_1 = next(
            (attrib for attrib in attrib_list if attrib['global_id'] == self.tutor_1.person.global_id),
            None)
        self.assertTrue(attrib_tutor_1)
        self.assertEqual(len(attrib_tutor_1['attributions']), 0)

    def test_two_attribution_function_to_same_learning_unit(self):
        new_attrib = AttributionNewFactory(learning_container_year=self.l_container, tutor=self.tutor_1,
                                           function=function.COORDINATOR)
        _create_attribution_charge(self.academic_year, new_attrib, "LBIR1210", Decimal(0), Decimal(0))
        attrib_list = attribution_json._compute_list()
        self.assertIsInstance(attrib_list, list)
        self.assertEqual(len(attrib_list), 2)

        attrib_tutor_1 = next(
                 (attrib for attrib in attrib_list if attrib['global_id'] == self.tutor_1.person.global_id),
                  None
        )
        self.assertEqual(len(attrib_tutor_1['attributions']), 3)

    def test_with_specific_global_id(self):
        global_id = self.tutor_2.person.global_id
        attrib_list = attribution_json._compute_list(global_ids=[global_id])
        self.assertIsInstance(attrib_list, list)
        self.assertEqual(len(attrib_list), 1)

        attrib_tutor_2 = next(
            (attrib for attrib in attrib_list if attrib['global_id'] == global_id),
            None
        )
        self.assertEqual(len(attrib_tutor_2['attributions']), 1)

    def test_with_multiple_global_id(self):
        global_id = self.tutor_2.person.global_id
        global_id_with_no_attributions = "4598989898"
        attrib_list = attribution_json._compute_list(global_ids=[global_id, global_id_with_no_attributions])
        self.assertIsInstance(attrib_list, list)
        self.assertEqual(len(attrib_list), 2)

        attribution_data = next(
            (attrib for attrib in attrib_list if attrib['global_id'] == global_id_with_no_attributions),
            None
        )
        self.assertFalse(attribution_data['attributions'])

    def test_get_title_next_luyr(self):
        self.assertIsNone(attribution_json._get_title_next_luyr(self.learning_unit_yr))

        next_academic_year = AcademicYearFactory(year=self.academic_year.year+1)
        self.assertIsNone(attribution_json._get_title_next_luyr(self.learning_unit_yr))

        next_luy = LearningUnitYearFactory(learning_unit=self.learning_unit_yr.learning_unit,
                                           academic_year=next_academic_year)
        self.assertEqual(attribution_json._get_title_next_luyr(self.learning_unit_yr), next_luy.complete_title)


def _create_learning_unit_year_with_components(academic_year, l_container, acronym, subtype):
    l_unit_year = LearningUnitYearFactory(academic_year=academic_year, learning_container_year=l_container,
                                          acronym=acronym, subtype=subtype)

    # Create component - CM - TP
    LearningComponentYearFactory(
        learning_unit_year=l_unit_year,
        type=learning_component_year_type.LECTURING,
        acronym="PM"
    )
    LearningComponentYearFactory(
        learning_unit_year=l_unit_year,
        type=learning_component_year_type.PRACTICAL_EXERCISES,
        acronym="PP"
    )
    return l_unit_year


def _create_attribution_charge(academic_year, attribution, l_acronym, volume_cm=None, volume_tp=None):
    component_qs = LearningComponentYear.objects.filter(
        learning_unit_year__acronym=l_acronym,
        learning_unit_year__academic_year=academic_year
    )
    if volume_cm is not None:
        component = component_qs.filter(type=learning_component_year_type.LECTURING).first()
        AttributionChargeNewFactory(
            attribution=attribution,
            learning_component_year=component,
            allocation_charge=volume_cm
        )

    if volume_tp is not None:
        component = component_qs.filter(type=learning_component_year_type.PRACTICAL_EXERCISES).first()
        AttributionChargeNewFactory(
            attribution=attribution,
            learning_component_year=component,
            allocation_charge=volume_tp
        )
