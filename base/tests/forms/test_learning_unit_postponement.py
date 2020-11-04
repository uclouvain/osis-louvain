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
from collections import OrderedDict
from decimal import Decimal
from unittest import mock

from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils.translation import gettext as _

from base.forms.learning_unit.learning_unit_create import LearningUnitYearModelForm
from base.forms.learning_unit.learning_unit_create_2 import FullForm
from base.forms.learning_unit.learning_unit_partim import PartimForm
from base.forms.learning_unit.learning_unit_postponement import LearningUnitPostponementForm, FIELDS_TO_NOT_POSTPONE
from base.models.academic_year import AcademicYear
from base.models.enums import learning_unit_year_subtypes
from base.models.enums.groups import FACULTY_MANAGER_GROUP
from base.models.enums.learning_component_year_type import LECTURING
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_container_year import LearningContainerYear
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.business.learning_units import GenerateContainer, GenerateAcademicYear
from base.tests.factories.group import FacultyManagerGroupFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory

FULL_ACRONYM = 'LAGRO1000'
SUBDIVISION_ACRONYM = 'C'


class LearningUnitPostponementFormContextMixin(TestCase):
    """This mixin is used in this test file in order to setup an environment for testing LEARNING UNIT POSTPONEMENT
       FORM"""

    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        start_year = AcademicYearFactory(year=cls.current_academic_year.year + 1)
        end_year = AcademicYearFactory(year=cls.current_academic_year.year + 10)
        cls.generated_ac_years = GenerateAcademicYear(start_year, end_year)
        FacultyManagerGroupFactory()

    def setUp(self):
        end_year_6 = AcademicYearFactory(year=self.current_academic_year.year + 6)
        # Creation of a LearingContainerYear and all related models - FOR 6 years
        self.learn_unit_structure = GenerateContainer(self.current_academic_year, end_year_6)
        # Build in Generated Container [first index = start Generate Container ]
        self.generated_container_year = self.learn_unit_structure.generated_container_years[0]

        # Update All full learning unit year acronym
        LearningUnitYear.objects.filter(learning_unit=self.learn_unit_structure.learning_unit_full) \
            .update(acronym=FULL_ACRONYM)
        # Update All partim learning unit year acronym
        LearningUnitYear.objects.filter(learning_unit=self.learn_unit_structure.learning_unit_partim) \
            .update(acronym=FULL_ACRONYM + SUBDIVISION_ACRONYM)

        self.learning_unit_year_full = LearningUnitYear.objects.get(
            learning_unit=self.learn_unit_structure.learning_unit_full,
            academic_year=self.current_academic_year
        )

        self.learning_unit_year_partim = LearningUnitYear.objects.get(
            learning_unit=self.learn_unit_structure.learning_unit_partim,
            academic_year=self.current_academic_year
        )

        self.person = PersonFactory()
        for entity in self.learn_unit_structure.entities:
            PersonEntityFactory(person=self.person, entity=entity)


class TestLearningUnitPostponementFormInit(LearningUnitPostponementFormContextMixin):
    """Unit tests for LearningUnitPostponementForm.__init__()"""

    def _instantiate_postponement_forms(self, end_year=None, is_partim=False):
        if is_partim:
            self.learn_unit_structure.learning_unit_partim.end_year = end_year
            self.learn_unit_structure.learning_unit_partim.save()
        else:
            self.learn_unit_structure.learning_unit_full.end_year = end_year
            self.learn_unit_structure.learning_unit_full.save()
        instance_luy_base_form = _instantiate_base_learning_unit_form(
            self.learning_unit_year_partim if is_partim else self.learning_unit_year_full,
            self.person
        )
        return _instanciate_postponement_form(
            self.person,
            self.learning_unit_year_full.academic_year,
            learning_unit_instance=instance_luy_base_form.learning_unit_instance,
            data=instance_luy_base_form.data,
            learning_unit_full_instance=self.learning_unit_year_full.learning_unit if is_partim else None
        )

    def test_wrong_instance_args(self):
        wrong_instance = LearningUnitYearFactory()
        with self.assertRaises(AttributeError):
            _instanciate_postponement_form(self.person, wrong_instance.academic_year,
                                           learning_unit_instance=wrong_instance)

    def test_consistency_property_default_value_is_true(self):
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        form = _instanciate_postponement_form(
            self.person,
            self.learning_unit_year_full.academic_year,
            learning_unit_instance=instance_luy_base_form.learning_unit_instance,
            data=instance_luy_base_form.data
        )
        self.assertTrue(form.check_consistency)

    def test_forms_property_end_year_is_none(self):
        form = self._instantiate_postponement_forms()
        self.assertIsInstance(form._forms_to_upsert, list)
        self.assertIsInstance(form._forms_to_delete, list)
        self.assertEqual(len(form._forms_to_upsert), 7)
        self.assertFalse(form._forms_to_delete)

    def test_forms_property_end_year_is_current_year(self):
        form = self._instantiate_postponement_forms(end_year=self.current_academic_year)
        self.assertEqual(len(form._forms_to_upsert), 1)  # The current need to be updated
        self.assertEqual(form._forms_to_upsert[0].forms[LearningUnitYearModelForm].instance,
                         self.learning_unit_year_full)
        self.assertEqual(len(form._forms_to_delete), 6)

    def test_forms_property_end_year_is_more_than_current_and_less_than_none(self):
        end_year = AcademicYearFactory(year=self.current_academic_year.year + 2)
        form = self._instantiate_postponement_forms(end_year=end_year)
        self.assertEqual(len(form._forms_to_upsert), 3)  # update the current + 2 inserts in the future
        self.assertEqual(len(form._forms_to_delete), 4)

    def test_forms_property_no_learning_unit_year_in_future(self):
        LearningUnitYear.objects.filter(
            learning_unit=self.learn_unit_structure.learning_unit_full,
            academic_year__year__gt=self.current_academic_year.year
        ).delete()
        form = self._instantiate_postponement_forms()
        self.assertEqual(len(form._forms_to_upsert), 7)
        self.assertFalse(form._forms_to_delete)

    def test_fields_to_not_postpone_param(self):
        expected_keys = {'is_vacant', 'type_declaration_vacant', 'attribution_procedure'}
        diff = expected_keys ^ set(FIELDS_TO_NOT_POSTPONE.keys())
        self.assertFalse(diff)

    def test_get_end_postponement_partim(self):
        form = self._instantiate_postponement_forms(end_year=self.current_academic_year, is_partim=True)
        self.assertEqual(len(form._forms_to_upsert), 1)  # The current need to be updated
        self.assertEqual(form._forms_to_upsert[0].forms[LearningUnitYearModelForm].instance,
                         self.learning_unit_year_partim)
        self.assertEqual(len(form._forms_to_delete), 6)

    def test_update_proposal(self):
        self.faculty_manager = PersonFactory()
        self.faculty_manager.user.groups.add(Group.objects.get(name=FACULTY_MANAGER_GROUP))

        next_learning_unit_year = LearningUnitYear.objects.get(
            learning_unit=self.learn_unit_structure.learning_unit_full,
            academic_year__year=self.current_academic_year.year + 1
        )

        ProposalLearningUnitFactory(learning_unit_year=next_learning_unit_year)
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full,
                                                                      self.faculty_manager)
        form = _instanciate_postponement_form(self.faculty_manager, self.learning_unit_year_full.academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              data=instance_luy_base_form.data)

        self.assertEqual(len(form._forms_to_upsert), 1)


class TestLearningUnitPostponementFormIsValid(LearningUnitPostponementFormContextMixin):
    """Unit tests for LearningUnitPostponementForm.is_valid()"""

    def setUp(self):
        super().setUp()
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        self.form_valid = _instanciate_postponement_form(
            self.person,
            self.learning_unit_year_full.academic_year,
            learning_unit_instance=instance_luy_base_form.learning_unit_instance,
            data=instance_luy_base_form.data
        )

    @mock.patch('base.forms.learning_unit.learning_unit_postponement.LearningUnitPostponementForm._check_consistency')
    def test_is_valid_with_consistency_property_to_false(self, mock_check_consistency):
        self.form_valid.check_consistency = False
        self.assertTrue(self.form_valid.is_valid())
        self.assertFalse(mock_check_consistency.called)

    @mock.patch('base.forms.learning_unit.learning_unit_postponement.LearningUnitPostponementForm._check_consistency')
    def test_is_valid_with_consistency_property_to_true(self, mock_check_consistency):
        self.form_valid.check_consistency = True
        self.assertTrue(self.form_valid.is_valid())
        mock_check_consistency.assert_called_once_with()


class TestLearningUnitPostponementFormSave(LearningUnitPostponementFormContextMixin):
    """Unit tests for LearningUnitPostponementForm.save()"""

    def setUp(self):
        super().setUp()
        LearningUnitYear.objects.filter(
            learning_unit=self.learn_unit_structure.learning_unit_full,
            academic_year__year__gt=self.current_academic_year.year
        ).delete()
        self.instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        self.form = _instanciate_postponement_form(
            self.person,
            self.learning_unit_year_full.academic_year,
            learning_unit_instance=self.instance_luy_base_form.learning_unit_instance,
            data=self.instance_luy_base_form.data
        )
        self.instance_luy_partim_form = _instantiate_base_learning_unit_form(
            self.learning_unit_year_partim,
            self.person
        )
        LearningUnitYear.objects.filter(
            learning_unit=self.learn_unit_structure.learning_unit_partim,
            academic_year__year__gt=self.current_academic_year.year
        ).delete()

    @mock.patch('base.forms.learning_unit.learning_unit_create_2.FullForm.save', side_effect=None)
    def test_save_with_all_luy_to_create(self, mock_baseform_save):
        """This test will ensure that the save will call LearningUnitBaseForm [CREATE] for all luy
           No update because all LUY doesn't exist on db
        """
        self.assertEqual(len(self.form._forms_to_upsert), 7)
        self.form.save()
        self.assertEqual(mock_baseform_save.call_count, 7)

    @mock.patch('base.forms.learning_unit.learning_unit_partim.PartimForm.save', side_effect=None)
    def test_save_with_all_luy_to_create_partim(self, mock_baseform_save):
        form = LearningUnitPostponementForm(self.person, self.learning_unit_year_full.academic_year,
                                            learning_unit_full_instance=self.learning_unit_year_full.learning_unit,
                                            data=self.instance_luy_partim_form.data)

        self.assertEqual(len(form._forms_to_upsert), 7)
        form.save()
        self.assertEqual(mock_baseform_save.call_count, 7)

    @mock.patch('base.forms.learning_unit.learning_unit_partim.PartimForm.save', side_effect=None)
    def test_save_with_all_luy_to_create_partim_with_end_year(self, mock_baseform_save):
        self.instance_luy_partim_form.data.update({
            'end_year': self.learning_unit_year_full.academic_year.year + 2,
            'component-TOTAL_FORMS': 2,
            'component-INITIAL_FORMS': 0,
            'component-MAX_NUM_FORMS': 2,
            'component-0-hourly_volume_total_annual': 20,
            'component-0-hourly_volume_partial_q1': 10,
            'component-0-hourly_volume_partial_q2': 10,
        })

        form = LearningUnitPostponementForm(self.person, self.learning_unit_year_full.academic_year,
                                            learning_unit_full_instance=self.learning_unit_year_full.learning_unit,
                                            data=self.instance_luy_partim_form.data)

        self.assertEqual(len(form._forms_to_upsert), 3)

        form.save()
        self.assertEqual(mock_baseform_save.call_count, 3)

    @mock.patch('base.forms.learning_unit.learning_unit_create_2.FullForm.save', side_effect=None)
    def test_update_luy_in_past(self, mock_baseform_save):
        """ Check if there is no postponement when the learning_unit_year is in the past """

        self.learning_unit_year_full.academic_year = AcademicYearFactory(year=2010)
        self.learning_unit_year_full.save()
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              learning_unit_instance=self.instance_luy_base_form.learning_unit_instance,
                                              data=self.instance_luy_base_form.data)
        self.assertEqual(len(form._forms_to_upsert), 1)
        self.assertEqual(form._forms_to_upsert[0].instance.learning_unit, self.learning_unit_year_full.learning_unit)
        self.assertEqual(len(form._forms_to_delete), 0)

        form.save()
        self.assertEqual(mock_baseform_save.call_count, 1)

    @mock.patch('base.forms.learning_unit.learning_unit_create_2.FullForm.save', side_effect=None)
    def test_create_luy_in_past(self, mock_baseform_save):
        """ Check if there is no postponement when the learning_unit_year is in the past """
        start_insert_year = AcademicYearFactory(year=self.current_academic_year.year - 10)
        self.learning_unit_year_full.academic_year = start_insert_year
        self.learning_unit_year_full.save()
        form = _instanciate_postponement_form(self.person, start_insert_year, data=self.instance_luy_base_form.data)

        self.assertEqual(len(form._forms_to_upsert), 1)
        self.assertEqual(len(form._forms_to_delete), 0)

        form.save()
        self.assertEqual(mock_baseform_save.call_count, 1)

    @mock.patch('base.forms.learning_unit.learning_unit_create_2.FullForm.save', side_effect=None)
    def test_save_with_luy_to_upsert(self, mock_baseform_save):
        """This test will ensure that the save will call LearningUnitBaseForm [CREATE/UPDATE] for all luy
           3 Update because LUY exist until current_academic_year + 2
           4 Create because LUY doesn't exist after current_academic_year + 2
        """
        LearningUnitYear.objects.filter(
            learning_unit=self.learn_unit_structure.learning_unit_full,
            academic_year__year__gt=self.current_academic_year.year + 2
        ).delete()

        self.assertEqual(len(self.form._forms_to_upsert), 7)

        self.form.save()
        self.assertEqual(mock_baseform_save.call_count, 7)

    def test_all_learning_unit_years_have_same_learning_unit(self):
        data = self.instance_luy_base_form.data
        data.update({
            'acronym': 'LDROI1001',
            'acronym_0': 'L',
            'acronym_1': 'DROI1001'
        })
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              data=data)
        self.assertTrue(form.is_valid(), form.errors)
        learning_units = {learning_unit_year.learning_unit for learning_unit_year in form.save()}
        self.assertEqual(len(learning_units), 1)


class TestLearningUnitPostponementFormCheckConsistency(LearningUnitPostponementFormContextMixin):
    """Unit tests for LearningUnitPostponementForm._check_consistency()"""

    def test_when_insert_postponement(self):
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              data=instance_luy_base_form.data)
        self.assertTrue(form._check_consistency())

    def test_when_end_postponement_updated_to_now(self):
        """Nothing to upsert in the future, only deletions."""
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        academic_year = self.learning_unit_year_full.academic_year
        form = _instanciate_postponement_form(self.person, academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              end_postponement=academic_year)
        self.assertTrue(form._check_consistency())

    def test_when_end_postponement_updated_to_next_year(self):
        """Only 1 upsert to perform (next year)."""
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        next_academic_year = AcademicYear.objects.get(year=self.learning_unit_year_full.academic_year.year + 1)
        form = _instanciate_postponement_form(self.person, next_academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              end_postponement=next_academic_year)
        self.assertTrue(form._check_consistency())

    @mock.patch(
        'base.forms.learning_unit.learning_unit_postponement.LearningUnitPostponementForm._find_consistency_errors')
    def test_find_consistency_errors_called(self, mock_find_consistency_errors):
        mock_find_consistency_errors.return_value = {
            self.learning_unit_year_full.academic_year: {'credits': {'current': 10, 'old': 15}}
        }
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              data=instance_luy_base_form.data)
        self.assertFalse(form._check_consistency())
        mock_find_consistency_errors.assert_called_once_with()


class TestLearningUnitPostponementFormFindConsistencyErrors(LearningUnitPostponementFormContextMixin):
    """Unit tests for LearningUnitPostponementForm._find_consistency_errors()"""

    def setUp(self):
        super(TestLearningUnitPostponementFormFindConsistencyErrors, self).setUp()
        self.instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        self.form = _instanciate_postponement_form(
            self.person,
            self.learning_unit_year_full.academic_year,
            learning_unit_instance=self.instance_luy_base_form.learning_unit_instance,
            data=self.instance_luy_base_form.data
        )

    def _change_credits_value(self, academic_year):
        initial_credits_value = self.learning_unit_year_full.credits
        new_credits_value = initial_credits_value + 5
        LearningUnitYear.objects.filter(academic_year=academic_year,
                                        learning_unit=self.learning_unit_year_full.learning_unit) \
            .update(credits=new_credits_value)
        return initial_credits_value, new_credits_value

    def _change_status_value(self, academic_year):
        initial_status_value = self.learning_unit_year_full.status
        new_status_value = not initial_status_value
        LearningUnitYear.objects.filter(academic_year=academic_year,
                                        learning_unit=self.learning_unit_year_full.learning_unit) \
            .update(status=new_status_value)
        return initial_status_value, new_status_value

    def _change_requirement_entity_value(self, academic_year):
        container_year = LearningContainerYear.objects.get(
            learning_container=self.learning_unit_year_full.learning_container_year.learning_container,
            academic_year=academic_year
        )
        initial_status_value = container_year.requirement_entity
        new_entity_value = self.learn_unit_structure.entities[2]
        container_year.requirement_entity = new_entity_value
        container_year.save()
        return initial_status_value, new_entity_value

    def _change_requirement_entity_repartition_vlume(self, academic_year, repartition_volume):
        qs = LearningComponentYear.objects.filter(
            type=LECTURING,
            learning_unit_year__academic_year=academic_year,
            learning_unit_year__learning_unit=self.learning_unit_year_full.learning_unit
        )
        qs.update(repartition_volume_requirement_entity=repartition_volume)
        return qs.get()

    @staticmethod
    def _remove_additional_requirement_entity_2(academic_year):
        # Remove additional requirement entity 2 container year
        learn_container_year = LearningContainerYear.objects.filter(academic_year=academic_year).get()
        initial_entity = learn_container_year.additional_entity_2
        learn_container_year.additional_entity_2 = None
        learn_container_year.save()
        return initial_entity

    def test_when_no_differences_found_in_future(self):
        self.assertTrue(self.form.is_valid())
        expected_result = {}
        self.assertEqual(self.form.consistency_errors, expected_result)

    def test_when_no_differences_found_empty_string_as_null(self):
        # Set specific title to 'None' for current academic year
        self.learning_unit_year_full.specific_title = None
        self.learning_unit_year_full.save()
        # Set specific title to '' for all next academic year
        LearningUnitYear.objects.filter(academic_year__year__gt=self.learning_unit_year_full.academic_year.year,
                                        learning_unit=self.learning_unit_year_full.learning_unit) \
            .update(specific_title='')

        self.assertTrue(self.form.is_valid())
        expected_result = {}
        self.assertEqual(self.form.consistency_errors, expected_result)

    def test_when_difference_found_on_none_value(self):
        # Set specific title to 'None' for learning unit next academic year
        next_academic_year = AcademicYear.objects.get(year=self.learning_unit_year_full.academic_year.year + 1)
        LearningUnitYear.objects.filter(academic_year=next_academic_year,
                                        learning_unit=self.learning_unit_year_full.learning_unit) \
            .update(specific_title=None)

        self.assertTrue(self.form.is_valid())
        result = self.form.consistency_errors
        expected_result = OrderedDict({
            next_academic_year: [
                _("%(col_name)s has been already modified. (%(new_value)s instead of %(current_value)s)") % {
                    'col_name': _('Specific complement (Full)'),
                    'new_value': '-',
                    'current_value': self.instance_luy_base_form.data['specific_title']
                }
            ]
        })
        self.assertEqual(expected_result[next_academic_year], result[next_academic_year])

    def test_when_difference_found_on_boolean_field(self):
        next_academic_year = AcademicYear.objects.get(year=self.learning_unit_year_full.academic_year.year + 1)
        initial_status_value, new_status_value = self._change_status_value(next_academic_year)
        expected_result = OrderedDict({
            next_academic_year: [
                _("%(col_name)s has been already modified. (%(new_value)s instead of %(current_value)s)") % {
                    'col_name': _('Active'),
                    'new_value': _('yes') if new_status_value else _('no'),
                    'current_value': _('yes') if initial_status_value else _('no')
                }
            ]
        })

        self.assertTrue(self.form.is_valid(), self.form.errors)
        result = self.form.consistency_errors
        self.assertIsInstance(result, OrderedDict)
        self.assertEqual(expected_result[next_academic_year], result[next_academic_year])

    def test_when_differences_found_on_2_next_years(self):
        next_academic_year = AcademicYear.objects.get(year=self.learning_unit_year_full.academic_year.year + 1)
        initial_credits_value, new_credits_value = self._change_credits_value(next_academic_year)
        next_academic_year_2 = AcademicYear.objects.get(year=self.learning_unit_year_full.academic_year.year + 2)
        initial_credits_value_2, new_credits_value_2 = self._change_credits_value(next_academic_year)
        expected_result = OrderedDict({
            next_academic_year: [
                _("%(col_name)s has been already modified. (%(new_value)s instead of %(current_value)s)") % {
                    'col_name': "Crédits",
                    'current_value': initial_credits_value,
                    'new_value': new_credits_value
                }
            ],
            next_academic_year_2: [
                _("%(col_name)s has been already modified. (%(new_value)s instead of %(current_value)s)") % {
                    'col_name': "Crédits",
                    'current_value': initial_credits_value_2,
                    'new_value': new_credits_value_2
                }
            ],
        })

        self.assertTrue(self.form.is_valid(), self.form.errors)
        result = self.form.consistency_errors
        self.assertIsInstance(result, OrderedDict)  # Need to be ordered by academic_year
        self.assertEqual(expected_result[next_academic_year], result[next_academic_year])

    def test_when_differences_found_on_entities(self):
        next_academic_year = AcademicYear.objects.get(year=self.learning_unit_year_full.academic_year.year + 1)
        initial_requirement_entity, new_requirement_entity = self._change_requirement_entity_value(next_academic_year)
        expected_result = OrderedDict({
            next_academic_year: [
                _("%(col_name)s has been already modified. (%(new_value)s instead of %(current_value)s)") % {
                    'col_name': _('Requirement entity'),
                    'current_value': initial_requirement_entity,
                    'new_value': new_requirement_entity
                }
            ],
        })

        self.assertTrue(self.form.is_valid(), self.form.errors)
        result = self.form.consistency_errors
        self.assertEqual(result, expected_result)

    def test_when_differences_found_on_repartition_volume(self):
        next_academic_year = AcademicYear.objects.get(year=self.learning_unit_year_full.academic_year.year + 1)
        component = self._change_requirement_entity_repartition_vlume(next_academic_year, 24)

        requirement_entity = component.learning_unit_year.learning_container_year.requirement_entity

        expected_result = OrderedDict({
            next_academic_year: [
                _("The repartition volume of %(col_name)s has been already modified. "
                  "(%(new_value)s instead of %(current_value)s)") % {
                    'col_name': component.acronym + "-" + requirement_entity.most_recent_acronym,
                    'new_value': component.repartition_volume_requirement_entity,
                    'current_value': "30.00"
                }
            ],
        })

        self.assertTrue(self.form.is_valid(), self.form.errors)
        result = self.form.consistency_errors
        self.assertDictEqual(result, expected_result)

    def test_when_differences_found_on_additional_requirement_entities(self):
        """
        In this test, we ensure that if N year have additional_requirement_entity_2 AND N+1 doesn't have,
        it display an error and prevent crash on _check_postponement_repartition_volume [ GET() ]
        """
        next_academic_year = AcademicYear.objects.get(year=self.learning_unit_year_full.academic_year.year + 1)
        initial_entity = self._remove_additional_requirement_entity_2(academic_year=next_academic_year)

        expected_result = OrderedDict({
            next_academic_year: [
                _("%(col_name)s has been already modified. (%(new_value)s instead of %(current_value)s)") % {
                    'col_name': _('Additional requirement entity 2'),
                    'new_value': '-',
                    'current_value': initial_entity
                }
            ],
        })

        self.assertTrue(self.form.is_valid(), self.form.errors)
        result = self.form.consistency_errors
        self.assertEqual(result, expected_result)


def _instantiate_base_learning_unit_form(learning_unit_year_instance, person):
    container_year = learning_unit_year_instance.learning_container_year
    learning_unit_instance = learning_unit_year_instance.learning_unit

    if learning_unit_year_instance.subtype == learning_unit_year_subtypes.FULL:
        form = FullForm
        learning_unit_full_instance = None
    else:
        form = PartimForm
        learning_unit_full_instance = learning_unit_year_instance.parent.learning_unit
    form_args = {
        'academic_year': learning_unit_year_instance.academic_year,
        'learning_unit_full_instance': learning_unit_full_instance,
        'learning_unit_instance': learning_unit_instance,
        'data': {
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
            'component-0-planned_classes': 1,
            'component-1-planned_classes': 1,
            'acronym': learning_unit_year_instance.acronym,
            'acronym_0': learning_unit_year_instance.acronym[0],
            'acronym_1': learning_unit_year_instance.acronym[1:],
            'subtype': learning_unit_year_instance.subtype,
            'academic_year': learning_unit_year_instance.academic_year.id,
            'specific_title': learning_unit_year_instance.specific_title,
            'specific_title_english': learning_unit_year_instance.specific_title_english,
            'credits': learning_unit_year_instance.credits,
            'session': learning_unit_year_instance.session,
            'quadrimester': learning_unit_year_instance.quadrimester,
            'status': learning_unit_year_instance.status,
            'internship_subtype': learning_unit_year_instance.internship_subtype,
            'attribution_procedure': learning_unit_year_instance.attribution_procedure,
            'language': learning_unit_year_instance.language.id,
            'campus': learning_unit_year_instance.campus.id,
            'periodicity': learning_unit_year_instance.periodicity,

            # Learning unit data model form
            'faculty_remark': learning_unit_instance.faculty_remark,
            'other_remark': learning_unit_instance.other_remark,

            # Learning container year data model form
            'common_title': container_year.common_title,
            'common_title_english': container_year.common_title_english,
            'container_type': container_year.container_type,
            'type_declaration_vacant': container_year.type_declaration_vacant,
            'team': container_year.team,
            'is_vacant': container_year.is_vacant,

            'requirement_entity': container_year.requirement_entity.get_latest_entity_version().id,
            'allocation_entity': container_year.allocation_entity.get_latest_entity_version().id,
            'additional_entity_1': container_year.additional_entity_1.get_latest_entity_version().id,
            'additional_entity_2': container_year.additional_entity_2.get_latest_entity_version().id,
        },
        'person': person
    }
    return form(**form_args)


def _instanciate_postponement_form(person, start_postponement, end_postponement=None,
                                   learning_unit_instance=None, data=None, learning_unit_full_instance=None):
    return LearningUnitPostponementForm(person, start_postponement, learning_unit_instance=learning_unit_instance,
                                        learning_unit_full_instance=learning_unit_full_instance,
                                        end_postponement=end_postponement, data=data)
