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
from unittest import mock

import factory
import factory.fuzzy
from django.forms import model_to_dict
from django.test import TestCase

from base.forms.learning_unit.edition_volume import SimplifiedVolumeManagementForm
from base.forms.learning_unit.entity_form import EntityContainerBaseForm
from base.forms.learning_unit.learning_unit_create import LearningUnitYearModelForm, \
    LearningUnitModelForm, LearningContainerYearModelForm, LearningContainerModelForm
from base.forms.learning_unit.learning_unit_partim import PARTIM_FORM_READ_ONLY_FIELD, PartimForm, \
    LearningUnitPartimModelForm
from base.forms.utils import acronym_field
from base.models.entity_component_year import EntityComponentYear
from base.models.enums import learning_unit_year_subtypes, organization_type
from base.models.enums.learning_component_year_type import LECTURING, PRACTICAL_EXERCISES
from base.models.enums.learning_unit_year_periodicity import ANNUAL, BIENNIAL_EVEN
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_unit import LearningUnit
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.business.learning_units import GenerateContainer, GenerateAcademicYear
from base.tests.factories.campus import CampusFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory

FULL_ACRONYM = 'LBIR1200'
SUBDIVISION_ACRONYM = 'A'


class LearningUnitPartimFormContextMixin(TestCase):
    """This mixin is used in this test file in order to setup an environment for testing PARTIM FORM"""
    def setUp(self):
        self.current_academic_year = create_current_academic_year()
        self.generated_ac_years = GenerateAcademicYear(self.current_academic_year.year + 1,
                                                       self.current_academic_year.year + 10)

        # Creation of a LearingContainerYear and all related models
        self.learn_unit_structure = GenerateContainer(self.current_academic_year.year, self.current_academic_year.year)
        # Build in Generated Container [first index = start Generate Container ]
        self.generated_container_year = self.learn_unit_structure.generated_container_years[0]

        # Update Full learning unit year acronym
        self.learning_unit_year_full = LearningUnitYear.objects.get(
            learning_unit=self.learn_unit_structure.learning_unit_full,
            academic_year=self.current_academic_year
        )
        self.learning_unit_year_full.acronym = FULL_ACRONYM
        self.learning_unit_year_full.learning_container_year.acronym = FULL_ACRONYM
        self.learning_unit_year_full.learning_container_year.save()
        self.learning_unit_year_full.save()

        # Update Partim learning unit year acronym
        self.learning_unit_year_partim = LearningUnitYear.objects.get(
            learning_unit=self.learn_unit_structure.learning_unit_partim,
            academic_year=self.current_academic_year,
            learning_container_year=self.learning_unit_year_full.learning_container_year
        )
        self.learning_unit_year_partim.acronym = FULL_ACRONYM + SUBDIVISION_ACRONYM
        self.learning_unit_year_partim.save()


class TestPartimFormInit(LearningUnitPartimFormContextMixin):
    """Unit tests for PartimForm.__init__()"""
    def test_subtype_is_partim(self):
        form = _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                                 academic_year=self.current_academic_year)
        self.assertEqual(form.subtype, learning_unit_year_subtypes.PARTIM)

    def test_wrong_learning_unit_full_instance_args(self):
        wrong_lu_full = LearningUnitYearFactory()
        with self.assertRaises(AttributeError):
            _instanciate_form(learning_unit_full=wrong_lu_full, academic_year=self.current_academic_year)

    def test_wrong_instance_args(self):
        wrong_instance = LearningUnitYearFactory()
        with self.assertRaises(AttributeError):
            _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                              academic_year=self.current_academic_year,
                              instance=wrong_instance)

    def test_model_forms_case_creation(self):
        form_classes_expected = [LearningUnitPartimModelForm, LearningUnitYearModelForm, LearningContainerModelForm,
                                 LearningContainerYearModelForm, EntityContainerBaseForm]
        form = _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                                 academic_year=self.current_academic_year)
        for cls in form_classes_expected:
            self.assertIsInstance(form.forms[cls], cls)

    def test_inherit_initial_values(self):
        """This test will check if field are pre-full in by value of full learning unit year"""
        expected_initials = {
            LearningUnitPartimModelForm: {},
            LearningUnitYearModelForm: {
                'acronym': ['L', 'BIR1200', ''],
                'acronym_0': 'L',  # Multiwidget decomposition
                'acronym_1': 'BIR1200',
                'acronym_2': '',
                'academic_year': self.learning_unit_year_full.academic_year.id,
                'internship_subtype': self.learning_unit_year_full.internship_subtype,
                'attribution_procedure': self.learning_unit_year_full.attribution_procedure,
                'subtype': learning_unit_year_subtypes.PARTIM,  # Creation of partim
                'credits': self.learning_unit_year_full.credits,
                'session': self.learning_unit_year_full.session,
                'quadrimester': self.learning_unit_year_full.quadrimester,
                'status': self.learning_unit_year_full.status,
                'specific_title': self.learning_unit_year_full.specific_title,
                'specific_title_english': self.learning_unit_year_full.specific_title_english,
                'language': self.learning_unit_year_full.language,
                'campus': self.learning_unit_year_full.campus,
                'periodicity': self.learning_unit_year_full.periodicity
            }
        }
        partim_form = _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                                        academic_year=self.current_academic_year)
        for form_class, initial in expected_initials.items():
            self.assertEqual(partim_form.forms[form_class].initial, initial)

    def test_instance_partim_values(self):
        partim = LearningUnitYearFactory(
            acronym='LBIR1200Z',
            subtype=learning_unit_year_subtypes.PARTIM,
            learning_container_year=self.learning_unit_year_full.learning_container_year,
            academic_year=self.learning_unit_year_full.academic_year
        )

        partim_form = _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                                        academic_year=self.learning_unit_year_full.academic_year,
                                        instance=partim.learning_unit)
        self.assertEqual(partim_form.forms[LearningUnitYearModelForm].initial['acronym'], ['L', 'BIR1200', 'Z'])

    def test_disabled_fields(self):
        """This function will check if fields is disabled"""
        partim_form = _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                                        academic_year=self.learning_unit_year_full.academic_year)
        expected_disabled_fields = {
            'common_title', 'common_title_english',
            'requirement_entity', 'allocation_entity',
            'academic_year', 'container_type', 'internship_subtype',
            'additional_requirement_entity_1', 'additional_requirement_entity_2'
        }
        all_fields = partim_form.fields.items()
        self.assertTrue(all(field.disabled == (field_name in expected_disabled_fields)
                            for field_name, field in all_fields))

    def test_form_cls_to_validate(self):
        """This function will ensure that only LearningUnitModelForm/LearningUnitYearModelForm is present
           in form_cls_to_validate"""
        partim_form = _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                                        academic_year=self.learning_unit_year_full.academic_year)
        expected_form_cls = [LearningUnitPartimModelForm, LearningUnitYearModelForm, SimplifiedVolumeManagementForm]
        self.assertEqual(partim_form.form_cls_to_validate, expected_form_cls)


class TestPartimFormIsValid(LearningUnitPartimFormContextMixin):
    """Unit tests for is_valid() """
    def _assert_equal_values(self, obj, dictionnary, fields_to_validate):
        for field in fields_to_validate:
            self.assertEqual(getattr(obj, field), dictionnary[field], msg='Error field = {}'.format(field))

    def test_creation_case_correct_post_data(self):
        a_new_learning_unit_partim = LearningUnitYearFactory.build(
            academic_year=self.current_academic_year,
            acronym=FULL_ACRONYM + 'B',
            subtype=learning_unit_year_subtypes.PARTIM,
            language=self.learning_unit_year_full.language
        )
        post_data = get_valid_form_data(a_new_learning_unit_partim)
        form = _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                                 academic_year=self.learning_unit_year_full.academic_year,
                                 post_data=post_data)
        # The form should be valid
        self.assertTrue(form.is_valid(), form.errors)
        # In partim, we can only modify LearningUnitYearModelForm / LearningUnitModelForm
        self._test_learning_unit_model_form_instance(form, post_data)
        self._test_learning_unit_year_model_form_instance(form, post_data)
        # Inherit instance from learning unit year full
        self._test_learning_container_model_form_instance(form)
        self._test_learning_container_year_model_form_instance(form)
        self._test_entity_container_model_formset_instance(form)

    def test_partim_periodicity_biannual_with_parent_annual(self):
        a_new_learning_unit_partim = LearningUnitYearFactory(
            academic_year=self.current_academic_year,
            acronym=FULL_ACRONYM + 'W',
            subtype=learning_unit_year_subtypes.PARTIM,
            credits=0,
            learning_container_year=self.learning_unit_year_full.learning_container_year,
        )
        a_new_learning_unit_partim.learning_unit.learning_container = \
            self.learning_unit_year_full.learning_unit.learning_container
        a_new_learning_unit_partim.learning_unit.save()

        self.learning_unit_year_full.learning_unit.periodicity = ANNUAL
        self.learning_unit_year_full.learning_unit.save()

        post_data = get_valid_form_data(a_new_learning_unit_partim)
        post_data['periodicity'] = BIENNIAL_EVEN

        form = LearningUnitModelForm(data=post_data, instance=a_new_learning_unit_partim.learning_unit)

        # The form should be valid
        self.assertTrue(form.is_valid(), form.errors)

    def _test_learning_unit_model_form_instance(self, partim_form, post_data):
        form_instance = partim_form.forms[LearningUnitPartimModelForm]
        fields_to_validate = ['faculty_remark', 'other_remark']
        self._assert_equal_values(form_instance.instance, post_data, fields_to_validate)

    def _test_learning_unit_year_model_form_instance(self, partim_form, post_data):
        form_instance = partim_form.forms[LearningUnitYearModelForm]
        fields_to_validate = ['specific_title', 'specific_title_english', 'credits',
                              'session', 'quadrimester', 'status', 'subtype', ]
        self._assert_equal_values(form_instance.instance, post_data, fields_to_validate)
        self.assertEqual(form_instance.instance.acronym, FULL_ACRONYM + 'B')

        # Academic year should be the same as learning unit full [Inherit field]
        self.assertEqual(form_instance.instance.academic_year.id, self.learning_unit_year_full.academic_year.id)

    def _test_learning_container_model_form_instance(self, partim_form):
        """In this test, we ensure that the instance of learning container model form inherit
           from full learning container """
        form_instance = partim_form.forms[LearningContainerModelForm]
        self.assertEqual(form_instance.instance,
                         self.learning_unit_year_full.learning_container_year.learning_container)

    def _test_learning_container_year_model_form_instance(self, partim_form):
        """ In this test, we ensure that the instance of learning container year model form inherit
            from full learning container year """
        form_instance = partim_form.forms[LearningContainerYearModelForm]
        self.assertEqual(form_instance.instance,
                         self.learning_unit_year_full.learning_container_year)

    def _test_entity_container_model_formset_instance(self, partim_form):
        """ In this test, we ensure that the instance of learning container year model form inherit
            from full learning container year """
        formset_instance = partim_form.forms[EntityContainerBaseForm]
        self.assertEqual(formset_instance.instance, self.learning_unit_year_full.learning_container_year)
        # Test expected instance
        expected_instance_form = [
            self.generated_container_year.requirement_entity_container_year,
            self.generated_container_year.allocation_entity_container_year,
            self.generated_container_year.additionnal_1_entity_container_year,
            self.generated_container_year.addtionnal_2_entity_container_year,
        ]
        for index, form in enumerate(formset_instance.forms):
            self.assertEqual(expected_instance_form[index], form.instance)

    @mock.patch('base.forms.learning_unit.learning_unit_create.LearningUnitModelForm.is_valid',
                side_effect=lambda *args: False)
    def test_creation_case_wrong_learning_unit_data(self, mock_is_valid):
        a_new_learning_unit_partim = LearningUnitYearFactory.build(
            academic_year=self.current_academic_year,
            acronym=FULL_ACRONYM + 'B',
            subtype=learning_unit_year_subtypes.PARTIM,
            language=self.learning_unit_year_full.language
        )
        post_data = get_valid_form_data(a_new_learning_unit_partim)
        form = _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                                 academic_year=self.learning_unit_year_full.academic_year,
                                 post_data=post_data)
        self.assertFalse(form.is_valid())


class TestPartimFormSave(LearningUnitPartimFormContextMixin):
    """Unit tests for save() for save"""
    def test_save(self):



        learning_container_year_full = self.learning_unit_year_full.learning_container_year
        a_new_learning_unit_partim = LearningUnitYearFactory.build(
            academic_year=self.current_academic_year,
            acronym=FULL_ACRONYM + 'C',
            subtype=learning_unit_year_subtypes.PARTIM,
            language=self.learning_unit_year_full.language
        )
        post_data = get_valid_form_data(a_new_learning_unit_partim)

        form = _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                                 academic_year=self.learning_unit_year_full.academic_year,
                                 post_data=post_data, instance=None)
        self.assertTrue(form.is_valid(), form.errors)
        saved_instance = form.save()

        self.assertIsInstance(saved_instance, LearningUnitYear)
        self.assertEqual(saved_instance.learning_container_year, learning_container_year_full)
        learning_component_year_list = LearningComponentYear.objects.filter(
            learning_unit_year__learning_container_year=saved_instance.learning_container_year
        )
        self.assertEqual(learning_component_year_list.count(), 6)
        self.assertEqual(
            EntityComponentYear.objects.filter(
                learning_component_year__in=learning_component_year_list).count(), 18)
        self.assertTrue(
            learning_component_year_list.filter(type=LECTURING, acronym="PM").exists())
        self.assertTrue(
            learning_component_year_list.filter(type=PRACTICAL_EXERCISES, acronym="PP").exists())

    def test_save_method_create_new_instance(self):
        partim_acronym = FULL_ACRONYM + 'C'
        a_new_learning_unit_partim = LearningUnitYearFactory.build(
            academic_year=self.current_academic_year,
            acronym=partim_acronym,
            subtype=learning_unit_year_subtypes.PARTIM,
            language=self.learning_unit_year_full.language
        )
        post_data = get_valid_form_data(a_new_learning_unit_partim)

        form = _instanciate_form(
            learning_unit_full=self.learning_unit_year_full.learning_unit,
            academic_year=self.learning_unit_year_full.academic_year,
            post_data=post_data, instance=None
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        # Check all related object is created
        self.assertEqual(LearningUnitYear.objects.filter(acronym=partim_acronym,
                                                         academic_year=self.current_academic_year).count(), 1)
        self.assertEqual(LearningUnit.objects.filter(learningunityear__acronym=partim_acronym).count(), 1)

    def test_save_method_update_instance(self):
        post_data = get_valid_form_data(self.learning_unit_year_partim)
        update_fields_luy_model = {
            'credits': 2,
            'specific_title': factory.fuzzy.FuzzyText(length=15).fuzz(),
            'specific_title_english': factory.fuzzy.FuzzyText(length=15).fuzz(),
        }
        post_data.update(update_fields_luy_model)
        update_fields_lu_model = {
            'faculty_remark': factory.fuzzy.FuzzyText(length=15).fuzz(),
            'other_remark': factory.fuzzy.FuzzyText(length=15).fuzz()
        }
        post_data.update(update_fields_lu_model)

        form = _instanciate_form(
            learning_unit_full=self.learning_unit_year_full.learning_unit,
            academic_year=self.learning_unit_year_full.academic_year,
            post_data=post_data,
            instance=self.learning_unit_year_partim.learning_unit
        )
        self.assertTrue(form.is_valid(), msg=form.errors)
        form.save()

        # Refresh learning unit year
        self.learning_unit_year_partim.refresh_from_db()
        # Check learning unit year update
        learning_unit_year_dict = model_to_dict(self.learning_unit_year_partim)
        for field, value in update_fields_luy_model.items():
            self.assertEqual(learning_unit_year_dict[field], value)

        # Check learning unit update
        self.learning_unit_year_partim.learning_unit.refresh_from_db()
        learning_unit_dict = model_to_dict(self.learning_unit_year_partim.learning_unit)
        for field, value in update_fields_lu_model.items():
            self.assertEqual(learning_unit_dict[field], value)

    def test_save_partim_without_container(self):
        post_data = get_valid_form_data(self.learning_unit_year_partim)
        parent_acronym = self.learning_unit_year_partim.learning_container_year.acronym
        partim_acronym = parent_acronym + 'X'
        post_data['acronym_2'] = partim_acronym[-1]
        post_data['credits'] = 2

        form = _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                                 academic_year=self.learning_unit_year_full.academic_year,
                                 post_data=post_data,
                                 instance=self.learning_unit_year_partim.learning_unit)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        # Refresh learning unit year
        self.learning_unit_year_partim.refresh_from_db()
        self.assertEqual(self.learning_unit_year_partim.acronym, partim_acronym)
        self.assertEqual(self.learning_unit_year_partim.learning_container_year.acronym, parent_acronym)

    def test_disable_fields_partim(self):
        form = _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                                 academic_year=self.learning_unit_year_full.academic_year,
                                 instance=self.learning_unit_year_partim.learning_unit)
        disabled_fields = {key for key, value in form.fields.items() if value.disabled == True}
        # acronym_0 and acronym_1 are disabled in the widget, not in the field
        disabled_fields.update({'acronym_0', 'acronym_1'})
        self.assertEqual(disabled_fields, PARTIM_FORM_READ_ONLY_FIELD)


def get_valid_form_data(learning_unit_year_partim):
    acronym_splited = acronym_field.split_acronym(learning_unit_year_partim.acronym)
    return {
        # Learning unit year data model form
        'acronym_2': acronym_splited[2],
        'subtype': learning_unit_year_partim.subtype,
        'specific_title': learning_unit_year_partim.specific_title,
        'specific_title_english': learning_unit_year_partim.specific_title_english,
        'credits': learning_unit_year_partim.credits,
        'session': learning_unit_year_partim.session,
        'quadrimester': learning_unit_year_partim.quadrimester,
        'status': learning_unit_year_partim.status,
        'language': learning_unit_year_partim.language.id,
        'campus': CampusFactory(name='Louvain-la-Neuve', organization__type=organization_type.MAIN).pk,
        'periodicity': learning_unit_year_partim.periodicity,

        # Learning unit data model form
        'faculty_remark': learning_unit_year_partim.learning_unit.faculty_remark,
        'other_remark': learning_unit_year_partim.learning_unit.other_remark,

        # Learning component year data model form
        'component-TOTAL_FORMS': '2',
        'component-INITIAL_FORMS': '0',
        'component-MAX_NUM_FORMS': '2',
        'component-0-hourly_volume_total_annual': 20,
        'component-0-hourly_volume_partial_q1': 10,
        'component-0-hourly_volume_partial_q2': 10,
        'component-1-hourly_volume_total_annual': 20,
        'component-1-hourly_volume_partial_q1': 10,
        'component-1-hourly_volume_partial_q2': 10,
    }


def _instanciate_form(learning_unit_full, academic_year, post_data=None, instance=None):
    person = PersonFactory()
    return PartimForm(person, learning_unit_full, academic_year, data=post_data,
                      learning_unit_instance=instance)
