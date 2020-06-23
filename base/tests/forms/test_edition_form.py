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

from django.test import TestCase, RequestFactory
from django.utils.translation import gettext

from base.business.learning_unit_year_with_context import get_with_context
from base.forms.learning_unit.edition_volume import VolumeEditionForm, VolumeEditionBaseFormset, \
    VolumeEditionFormsetContainer
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.business.learning_units import GenerateContainer, GenerateAcademicYear
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.person import CentralManagerForUEFactory, FacultyManagerForUEFactory


class TestVolumeEditionForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.start_year = AcademicYearFactory(year=2010)
        cls.end_year = AcademicYearFactory(year=2020)
        cls.generated_ac_years = GenerateAcademicYear(cls.start_year, cls.end_year)
        cls.generated_container = GenerateContainer(cls.start_year, cls.end_year)
        cls.first_learning_unit_year = cls.generated_container.generated_container_years[0].learning_unit_year_full
        cls.learning_unit_with_context = get_with_context(
            learning_container_year_id=cls.first_learning_unit_year.learning_container_year)[0]

    def test_get_volume_form(self):
        for component, component_values in self.learning_unit_with_context.components.items():
            component_values = VolumeEditionBaseFormset._clean_component_keys(component_values)
            form = VolumeEditionForm(learning_unit_year=self.learning_unit_with_context,
                                     initial=component_values,
                                     component=component,
                                     entities=self.learning_unit_with_context.entities)

            self.assertEqual(form.initial, component_values)

    def test_post_volume_form(self):
        for component, component_values in self.learning_unit_with_context.components.items():
            component_values = VolumeEditionBaseFormset._clean_component_keys(component_values)
            form = VolumeEditionForm(
                data=_get_valid_data(),
                learning_unit_year=self.learning_unit_with_context,
                initial=component_values,
                component=component,
                entities=self.learning_unit_with_context.entities)
            self.assertTrue(form.is_valid())

    def test_post_volume_form_empty_field(self):
        for component, component_values in self.learning_unit_with_context.components.items():
            component_values = VolumeEditionBaseFormset._clean_component_keys(component_values)
            form = VolumeEditionForm(
                data=_get_wrong_data_empty_field(),
                learning_unit_year=self.learning_unit_with_context,
                initial=component_values,
                component=component,
                entities=self.learning_unit_with_context.entities)
            self.assertFalse(form.is_valid())

    def test_post_volume_form_wrong_volume_total(self):
        for component, component_values in self.learning_unit_with_context.components.items():
            component_values = VolumeEditionBaseFormset._clean_component_keys(component_values)
            form = VolumeEditionForm(
                data=_get_wrong_data_volume_tot(),
                learning_unit_year=self.learning_unit_with_context,
                initial=component_values,
                component=component,
                entities=self.learning_unit_with_context.entities)
            self.assertFalse(form.is_valid())

    def test_post_volume_form_wrong_volume_tot_requirement(self):
        for component, component_values in self.learning_unit_with_context.components.items():
            component_values = VolumeEditionBaseFormset._clean_component_keys(component_values)
            form = VolumeEditionForm(
                data=_get_wrong_data_volume_tot(),
                learning_unit_year=self.learning_unit_with_context,
                initial=component_values,
                component=component,
                entities=self.learning_unit_with_context.entities)
            self.assertFalse(form.is_valid())

    def test_post_volume_form_wrong_vol_req_entity(self):
        for component, component_values in self.learning_unit_with_context.components.items():
            component_values = VolumeEditionBaseFormset._clean_component_keys(component_values)
            form = VolumeEditionForm(
                data=_get_wrong_data_vol_req_entity(),
                learning_unit_year=self.learning_unit_with_context,
                initial=component_values,
                component=component,
                entities=self.learning_unit_with_context.entities)
            self.assertFalse(form.is_valid())  # Don't accept that vol_global is not equal to sum of volumes of entities

    def test_post_volume_form_wrong_vol_req_entity_without_additional(self):
        for component, component_values in self.learning_unit_with_context.components.items():
            component_values = VolumeEditionBaseFormset._clean_component_keys(component_values)
            form = VolumeEditionForm(
                data=_get_wrong_data_vol_req_entity_without_additional(),
                learning_unit_year=self.learning_unit_with_context,
                initial=component_values,
                component=component,
                entities=self.learning_unit_with_context.entities)
            self.assertFalse(form.is_valid())

    def test_post_volume_form_partim_q1(self):
        for component, component_values in self.learning_unit_with_context.components.items():
            component_values = VolumeEditionBaseFormset._clean_component_keys(component_values)
            form = VolumeEditionForm(
                data=_get_valid_partim_data_alter(),
                learning_unit_year=self.learning_unit_with_context,
                initial=component_values,
                component=component,
                entities=self.learning_unit_with_context.entities)
            self.assertTrue(form.is_valid())


def _get_wrong_data_empty_field():
    data = _get_valid_data()
    data['volume_total'] = ''
    return data


def _get_wrong_data_volume_tot():
    data = _get_valid_data()
    data['volume_total'] = 3
    data['volume_q1'] = 2
    data['volume_Q2'] = 2
    return data


def _get_wrong_data_vol_req_entity():
    data = _get_valid_data()
    data['volume_additional_requirement_entity_1'] = 2
    return data


def _get_wrong_data_vol_req_entity_without_additional():
    data = _get_valid_data()
    data['volume_additional_requirement_entity_1'] = None
    data['volume_additional_requirement_entity_2'] = None
    return data


def _get_valid_data():
    return {
        'volume_total': 2,
        'volume_q1': 0,
        'volume_q2': 2,
        'planned_classes': 1,
        'volume_requirement_entity': 1,
        'volume_additional_requirement_entity_1': 0.5,
        'volume_additional_requirement_entity_2': 0.5,
        'volume_total_requirement_entities': 2
    }


def _get_valid_partim_data():
    return {
        'volume_total': 1,
        'volume_q1': 0,
        'volume_q2': 1,
        'planned_classes': 1,
        'volume_requirement_entity': 0.5,
        'volume_additional_requirement_entity_1': 0.25,
        'volume_additional_requirement_entity_2': 0.25,
        'volume_total_requirement_entities': 1
    }


def _get_valid_partim_data_alter():
    return {
        'volume_total': 4,
        'volume_q1': 1,
        'volume_q2': 3,
        'planned_classes': 2,
        'volume_requirement_entity': 6,
        'volume_additional_requirement_entity_1': 1,
        'volume_additional_requirement_entity_2': 1,
        'volume_total_requirement_entities': 8
    }


class TestVolumeEditionFormsetContainer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.start_year, cls.end_year = AcademicYearFactory.produce_in_future(quantity=2)
        cls.generated_ac_years = GenerateAcademicYear(cls.start_year, cls.end_year)
        cls.generated_container = GenerateContainer(cls.start_year, cls.end_year)
        cls.generated_container_year = cls.generated_container.generated_container_years[0]
        cls.learning_container_year = cls.generated_container.generated_container_years[0].learning_container_year
        cls.learning_units_with_context = get_with_context(
            learning_container_year_id=cls.learning_container_year
        )

        cls.learning_unit_year_full = cls.generated_container_year.learning_unit_year_full
        cls.learning_unit_year_partim = cls.generated_container_year.learning_unit_year_partim
        cls.central_manager = CentralManagerForUEFactory()
        cls.faculty_manager = FacultyManagerForUEFactory()
        cls.request_factory = RequestFactory()
        cls.data_forms = get_valid_formset_data(cls.learning_unit_year_full.acronym)

    def test_should_generate_container_of_formset_for_each_learing_unit_when_instantiating(self):
        volume_edition_formset_container = VolumeEditionFormsetContainer(
            self.request_factory.get(None),
            self.learning_units_with_context,
            self.central_manager
        )

        self.assertCountEqual(
            list(volume_edition_formset_container.formsets.keys()),
            [self.learning_unit_year_full, self.learning_unit_year_partim]
        )

        first_formset = volume_edition_formset_container.formsets[self.learning_unit_year_full]
        self.assertEqual(len(first_formset.forms), 2)

    def test_should_be_valid_when_all_forms_contained_are_valid(self):
        self.data_forms.update({
            **get_valid_formset_data(self.learning_unit_year_partim.acronym, is_partim=True),
            'postponement': 1
        })

        volume_edition_formset_container = VolumeEditionFormsetContainer(
            self.request_factory.post(None, data=self.data_forms),
            self.learning_units_with_context,
            self.central_manager
        )

        self.assertTrue(volume_edition_formset_container.is_valid())

    def test_should_disable_fields_for_full_course_when_user_is_faculty_manager(self):
        volume_edition_formset_container = VolumeEditionFormsetContainer(
            self.request_factory.get(None),
            self.learning_units_with_context,
            self.faculty_manager
        )

        full_formset = volume_edition_formset_container.formsets[self.learning_unit_year_full]
        first_form = full_formset.forms[0]

        fields = first_form.fields
        for key, field in fields.items():
            if key in first_form._faculty_manager_fields:
                self.assertFalse(field.disabled)
            else:
                self.assertTrue(field.disabled)

        partim_formset = volume_edition_formset_container.formsets[self.learning_unit_year_partim]
        first_form = partim_formset.forms[0]

        fields = first_form.fields
        for key, field in fields.items():
            self.assertFalse(field.disabled)

    def test_volume_edition_as_faculty_manager(self):
        component = LearningComponentYearFactory()
        form = VolumeEditionForm(
            data={'volume_q1': 12, 'volume_q2': 12, 'volume_total': 24},
            component=component,
            learning_unit_year=self.learning_unit_year_full,
            is_faculty_manager=True, initial={'volume_q1': 0, 'volume_q2': 12}
        )

        form.is_valid()
        self.assertEqual(form.errors['volume_q2'][1], gettext('One of the partial volumes must have a value to 0.'))
        self.assertEqual(form.errors['volume_q1'][1], gettext('One of the partial volumes must have a value to 0.'))

        form = VolumeEditionForm(
            data={'volume_q1': 0, 'volume_q2': 12, 'volume_total': 24},
            component=component,
            learning_unit_year=self.learning_unit_year_full,
            is_faculty_manager=True, initial={'volume_q1': 12, 'volume_q2': 12}
        )

        form.is_valid()
        self.assertEqual(form.errors['volume_q1'][1], gettext('The volume can not be set to 0.'))

        form = VolumeEditionForm(
            data={'volume_q1': 12, 'volume_q2': 0, 'volume_total': 24},
            component=component,
            learning_unit_year=self.learning_unit_year_full,
            is_faculty_manager=True, initial={'volume_q1': 12, 'volume_q2': 12}
        )

        form.is_valid()
        self.assertEqual(form.errors['volume_q2'][1], gettext('The volume can not be set to 0.'))


def get_valid_formset_data(prefix, is_partim=False):
    form_data = {}
    data = _get_valid_data() if not is_partim else _get_valid_partim_data()

    for i in range(2):
        form_data.update({'{}-{}'.format(i, k): v for k, v in data.items()})

    form_data.update(
        {'INITIAL_FORMS': '0',
         'MAX_NUM_FORMS': '1000',
         'MIN_NUM_FORMS': '0',
         'TOTAL_FORMS': '2'}
    )
    return {'{}-{}'.format(prefix, k): v for k, v in form_data.items()}
