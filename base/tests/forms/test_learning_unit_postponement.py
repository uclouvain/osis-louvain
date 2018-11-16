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
from unittest import mock

from django.test import TestCase
from django.utils.translation import ugettext as _

from base.forms.learning_unit.learning_unit_create import LearningUnitYearModelForm
from base.forms.learning_unit.learning_unit_create_2 import FullForm
from base.forms.learning_unit.learning_unit_partim import PartimForm
from base.forms.learning_unit.learning_unit_postponement import LearningUnitPostponementForm, FIELDS_TO_NOT_POSTPONE
from base.models import entity_container_year
from base.models.academic_year import AcademicYear
from base.models.entity_component_year import EntityComponentYear
from base.models.entity_container_year import EntityContainerYear
from base.models.enums import attribution_procedure, entity_container_year_link_type, learning_unit_year_subtypes, \
    vacant_declaration_type
from base.models.enums.entity_container_year_link_type import REQUIREMENT_ENTITY, ADDITIONAL_REQUIREMENT_ENTITY_2
from base.models.enums.learning_component_year_type import LECTURING
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.business.learning_units import GenerateContainer, GenerateAcademicYear
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory

FULL_ACRONYM = 'LAGRO1000'
SUBDIVISION_ACRONYM = 'C'


class LearningUnitPostponementFormContextMixin(TestCase):
    """This mixin is used in this test file in order to setup an environment for testing LEARNING UNIT POSTPONEMENT
       FORM"""

    def setUp(self):
        self.current_academic_year = create_current_academic_year()
        self.generated_ac_years = GenerateAcademicYear(self.current_academic_year.year + 1,
                                                       self.current_academic_year.year + 10)

        # Creation of a LearingContainerYear and all related models - FOR 6 years
        self.learn_unit_structure = GenerateContainer(self.current_academic_year.year,
                                                      self.current_academic_year.year + 6)
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

    def test_wrong_instance_args(self):
        wrong_instance = LearningUnitYearFactory()
        with self.assertRaises(AttributeError):
            _instanciate_postponement_form(self.person, wrong_instance.academic_year,
                                           learning_unit_instance=wrong_instance)

    def test_consistency_property_default_value_is_true(self):
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              data=instance_luy_base_form.data)
        self.assertTrue(form.check_consistency)

    def test_forms_property_end_year_is_none(self):
        self.learn_unit_structure.learning_unit_full.end_year = None
        self.learn_unit_structure.learning_unit_full.save()
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              data=instance_luy_base_form.data)

        self.assertIsInstance(form._forms_to_upsert, list)
        self.assertIsInstance(form._forms_to_delete, list)
        self.assertEqual(len(form._forms_to_upsert), 7)
        self.assertFalse(form._forms_to_delete)

    def test_forms_property_end_year_is_current_year(self):
        self.learn_unit_structure.learning_unit_full.end_year = self.current_academic_year.year
        self.learn_unit_structure.learning_unit_full.save()
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              data=instance_luy_base_form.data)
        self.assertEqual(len(form._forms_to_upsert), 1)  # The current need to be updated
        self.assertEqual(form._forms_to_upsert[0].forms[LearningUnitYearModelForm].instance,
                         self.learning_unit_year_full)
        self.assertEqual(len(form._forms_to_delete), 6)

    def test_forms_property_end_year_is_more_than_current_and_less_than_none(self):
        self.learn_unit_structure.learning_unit_full.end_year = self.current_academic_year.year + 2
        self.learn_unit_structure.learning_unit_full.save()

        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              data=instance_luy_base_form.data)

        self.assertEqual(len(form._forms_to_upsert), 3)  # update the current + 2 inserts in the future
        self.assertEqual(len(form._forms_to_delete), 4)

    def test_forms_property_no_learning_unit_year_in_future(self):
        self.learn_unit_structure.learning_unit_full.end_year = None
        self.learn_unit_structure.learning_unit_full.save()
        LearningUnitYear.objects.filter(
            learning_unit=self.learn_unit_structure.learning_unit_full,
            academic_year__year__gt=self.current_academic_year.year
        ).delete()

        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              data=instance_luy_base_form.data)
        self.assertEqual(len(form._forms_to_upsert), 7)
        self.assertFalse(form._forms_to_delete)

    def test_fields_to_not_postpone_param(self):
        expected_keys = {'is_vacant', 'type_declaration_vacant', 'attribution_procedure'}
        diff = expected_keys ^ set(FIELDS_TO_NOT_POSTPONE.keys())
        self.assertFalse(diff)

    def test_get_end_postponement_partim(self):
        self.learn_unit_structure.learning_unit_partim.end_year = self.current_academic_year.year
        self.learn_unit_structure.learning_unit_partim.save()
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_partim, self.person)
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_partim.academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              learning_unit_full_instance=self.learning_unit_year_full.learning_unit,
                                              data=instance_luy_base_form.data)
        self.assertEqual(len(form._forms_to_upsert), 1)  # The current need to be updated
        self.assertEqual(form._forms_to_upsert[0].forms[LearningUnitYearModelForm].instance,
                         self.learning_unit_year_partim)
        self.assertEqual(len(form._forms_to_delete), 6)


class TestLearningUnitPostponementFormIsValid(LearningUnitPostponementFormContextMixin):
    """Unit tests for LearningUnitPostponementForm.is_valid()"""

    @mock.patch('base.forms.learning_unit.learning_unit_postponement.LearningUnitPostponementForm._check_consistency',
                side_effect=None)
    def test_is_valid_with_consitency_property_to_false(self, mock_check_consistency):
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              data=instance_luy_base_form.data)
        form.check_consistency = False
        self.assertTrue(form.is_valid())
        self.assertFalse(mock_check_consistency.called)

    @mock.patch('base.forms.learning_unit.learning_unit_postponement.LearningUnitPostponementForm._check_consistency',
                side_effect=None)
    def test_is_valid_with_consitency_property_to_true(self, mock_check_consistency):
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              data=instance_luy_base_form.data)
        form.check_consistency = True
        self.assertTrue(form.is_valid())
        mock_check_consistency.assert_called_once_with()


class TestLearningUnitPostponementFormSave(LearningUnitPostponementFormContextMixin):
    """Unit tests for LearningUnitPostponementForm.save()"""

    @mock.patch('base.forms.learning_unit.learning_unit_create_2.FullForm.save', side_effect=None)
    def test_save_with_all_luy_to_create(self, mock_baseform_save):
        """This test will ensure that the save will call LearningUnitBaseForm [CREATE] for all luy
           No update because all LUY doesn't exist on db
        """
        LearningUnitYear.objects.filter(
            learning_unit=self.learn_unit_structure.learning_unit_full,
            academic_year__year__gt=self.current_academic_year.year
        ).delete()
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              data=instance_luy_base_form.data)
        self.assertEqual(len(form._forms_to_upsert), 7)

        form.save()
        self.assertEqual(mock_baseform_save.call_count, 7)

    @mock.patch('base.forms.learning_unit.learning_unit_partim.PartimForm.save', side_effect=None)
    def test_save_with_all_luy_to_create_partim(self, mock_baseform_save):
        LearningUnitYear.objects.filter(
            learning_unit=self.learn_unit_structure.learning_unit_partim,
            academic_year__year__gt=self.current_academic_year.year
        ).delete()
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_partim, self.person)
        form = LearningUnitPostponementForm(self.person, self.learning_unit_year_full.academic_year,
                                            learning_unit_full_instance=self.learning_unit_year_full.learning_unit,
                                            data=instance_luy_base_form.data)

        self.assertEqual(len(form._forms_to_upsert), 7)

        form.save()
        self.assertEqual(mock_baseform_save.call_count, 7)

    @mock.patch('base.forms.learning_unit.learning_unit_partim.PartimForm.save', side_effect=None)
    def test_save_with_all_luy_to_create_partim_with_end_year(self, mock_baseform_save):
        LearningUnitYear.objects.filter(
            learning_unit=self.learn_unit_structure.learning_unit_partim,
            academic_year__year__gt=self.current_academic_year.year
        ).delete()

        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_partim, self.person)
        instance_luy_base_form.data['end_year'] = self.learning_unit_year_full.academic_year.year + 2
        instance_luy_base_form.data['form-TOTAL_FORMS'] = 2
        instance_luy_base_form.data['form-INITIAL_FORMS'] = 0
        instance_luy_base_form.data['form-MAX_NUM_FORMS'] = 2
        instance_luy_base_form.data['form-0-hourly_volume_total_annual'] = 20
        instance_luy_base_form.data['form-0-hourly_volume_partial_q1'] = 10
        instance_luy_base_form.data['form-0-hourly_volume_partial_q2'] = 10

        form = LearningUnitPostponementForm(self.person, self.learning_unit_year_full.academic_year,
                                            learning_unit_full_instance=self.learning_unit_year_full.learning_unit,
                                            data=instance_luy_base_form.data)

        self.assertEqual(len(form._forms_to_upsert), 3)

        form.save()
        self.assertEqual(mock_baseform_save.call_count, 3)

    @mock.patch('base.forms.learning_unit.learning_unit_create_2.FullForm.save', side_effect=None)
    def test_update_luy_in_past(self, mock_baseform_save):
        """ Check if there is no postponement when the learning_unit_year is in the past """

        self.learning_unit_year_full.academic_year = AcademicYearFactory(year=2010)
        self.learning_unit_year_full.save()
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              data=instance_luy_base_form.data)
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
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        form = _instanciate_postponement_form(self.person, start_insert_year, data=instance_luy_base_form.data)

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

        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              data=instance_luy_base_form.data)
        self.assertEqual(len(form._forms_to_upsert), 7)

        form.save()
        self.assertEqual(mock_baseform_save.call_count, 7)

    def test_all_learning_unit_years_have_same_learning_unit(self):
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        data = dict(instance_luy_base_form.data)
        data['acronym'] = 'LDROI1001'
        data['acronym_0'] = 'L'
        data['acronym_1'] = 'DROI1001'
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              data=data)
        self.assertTrue(form.is_valid(), form.errors)
        learning_units = {learning_unit_year.learning_unit for learning_unit_year in form.save()}
        self.assertEqual(len(learning_units), 1)

    def test_save_ensure_fields_to_not_postpone(self):
        # Update fields to not postpone for next learning unit year
        next_learning_unit_year = LearningUnitYear.objects.get(
            learning_unit=self.learning_unit_year_full.learning_unit,
            academic_year__year=self.learning_unit_year_full.academic_year.year + 1
        )
        next_learning_unit_year.attribution_procedure = attribution_procedure.EXTERNAL
        next_learning_unit_year.save()
        next_learning_unit_year.learning_container_year.is_vacant = False
        next_learning_unit_year.learning_container_year.type_declaration_vacant = vacant_declaration_type.DO_NOT_ASSIGN
        next_learning_unit_year.learning_container_year.save()

        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        data = dict(instance_luy_base_form.data)
        data['is_vacant'] = True
        data['attribution_procedure'] = attribution_procedure.INTERNAL_TEAM
        data['type_declaration_vacant'] = vacant_declaration_type.EXCEPTIONAL_PROCEDURE
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              data=data)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        # Ensure that modifications is done for first item
        self.learning_unit_year_full.refresh_from_db()
        self.learning_unit_year_full.learning_container_year.refresh_from_db()
        self.assertEqual(data['is_vacant'], self.learning_unit_year_full.learning_container_year.is_vacant)
        self.assertEqual(data['type_declaration_vacant'],
                         self.learning_unit_year_full.learning_container_year.type_declaration_vacant)
        self.assertEqual(data['attribution_procedure'], self.learning_unit_year_full.attribution_procedure)

        # Ensure that postponement modification is not done for next year
        next_learning_unit_year.refresh_from_db()
        next_learning_unit_year.learning_container_year.refresh_from_db()
        self.assertFalse(next_learning_unit_year.learning_container_year.is_vacant)
        self.assertEqual(next_learning_unit_year.learning_container_year.type_declaration_vacant,
                         vacant_declaration_type.DO_NOT_ASSIGN)
        self.assertEqual(next_learning_unit_year.attribution_procedure, attribution_procedure.EXTERNAL)


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
        entity_version_by_type = entity_container_year.find_last_entity_version_grouped_by_linktypes(
            self.learning_unit_year_full.learning_container_year
        )
        initial_status_value = entity_version_by_type.get(entity_container_year_link_type.REQUIREMENT_ENTITY).entity
        new_entity_value = self.learn_unit_structure.entities[2]
        EntityContainerYear.objects.filter(
            learning_container_year__learning_container=self.learning_unit_year_full.learning_container_year.learning_container,
            learning_container_year__academic_year=academic_year,
            type=entity_container_year_link_type.REQUIREMENT_ENTITY
        ).update(entity=new_entity_value)
        return initial_status_value, new_entity_value

    def _change_cm_component_value(self, academic_year, new_hourly_total_value):
        LearningComponentYear.objects.filter(
            type=LECTURING,
            learning_container_year__academic_year=academic_year,
            learning_container_year__learning_container=self.learning_unit_year_full.learning_container_year.learning_container
        ).update(hourly_volume_total_annual=new_hourly_total_value)

    def _change_entity_component_value(self, academic_year, repartition_volume):
        qs = EntityComponentYear.objects.filter(
            learning_component_year__type=LECTURING,
            entity_container_year__type=REQUIREMENT_ENTITY,
            learning_component_year__learning_container_year__academic_year=academic_year,
            learning_component_year__learningunitcomponent__learning_unit_year__learning_unit=
            self.learning_unit_year_full.learning_unit
        )
        qs.update(repartition_volume=repartition_volume)
        return qs.get()

    def _remove_additional_requirement_entity_2(self, academic_year):
        # Remove additional requirements entities component year
        learning_unit_full = self.learning_unit_year_full.learning_unit
        EntityComponentYear.objects.filter(
            entity_container_year__type=ADDITIONAL_REQUIREMENT_ENTITY_2,
            learning_component_year__learning_container_year__academic_year=academic_year,
            learning_component_year__learningunitcomponent__learning_unit_year__learning_unit=learning_unit_full
        ).delete()

        # Remove additional requirement entity 2 container year
        initial_entity_container_year = EntityContainerYear.objects.get(
            type=ADDITIONAL_REQUIREMENT_ENTITY_2,
            learning_container_year__academic_year=academic_year
        )
        initial_entity = initial_entity_container_year.entity
        initial_entity_container_year.delete()
        return initial_entity

    def test_when_no_differences_found_in_future(self):
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              data=instance_luy_base_form.data)
        self.assertTrue(form.is_valid())
        expected_result = {}
        self.assertEqual(form.consistency_errors, expected_result)

    def test_when_no_differences_found_empty_string_as_null(self):
        # Set specific title to 'None' for current academic year
        self.learning_unit_year_full.specific_title = None
        self.learning_unit_year_full.save()
        # Set specific title to '' for all next academic year
        LearningUnitYear.objects.filter(academic_year__year__gt=self.learning_unit_year_full.academic_year.year,
                                        learning_unit=self.learning_unit_year_full.learning_unit) \
            .update(specific_title='')

        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              data=instance_luy_base_form.data)
        self.assertTrue(form.is_valid())
        expected_result = {}
        self.assertEqual(form.consistency_errors, expected_result)

    def test_when_difference_found_on_none_value(self):
        # Set specific title to 'None' for learning unit next academic year
        next_academic_year = AcademicYear.objects.get(year=self.learning_unit_year_full.academic_year.year + 1)
        LearningUnitYear.objects.filter(academic_year=next_academic_year,
                                        learning_unit=self.learning_unit_year_full.learning_unit) \
            .update(specific_title=None)
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              data=instance_luy_base_form.data)
        self.assertTrue(form.is_valid())
        result = form.consistency_errors
        expected_result = OrderedDict({
            next_academic_year: [
                _("%(col_name)s has been already modified. ({%(new_value)s} instead of {%(current_value)s})") % {
                    'col_name': _('English title proper'),
                    'new_value': '-',
                    'current_value': instance_luy_base_form.data['specific_title']
                }
            ]
        })
        self.assertEqual(expected_result[next_academic_year], result[next_academic_year])

    def test_when_difference_found_on_boolean_field(self):
        next_academic_year = AcademicYear.objects.get(year=self.learning_unit_year_full.academic_year.year + 1)
        initial_status_value, new_status_value = self._change_status_value(next_academic_year)
        expected_result = OrderedDict({
            next_academic_year: [
                _("%(col_name)s has been already modified. ({%(new_value)s} instead of {%(current_value)s})") % {
                    'col_name': _('Active'),
                    'new_value': _('yes') if new_status_value else _('no'),
                    'current_value': _('yes') if initial_status_value else _('no')
                }
            ]
        })
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              data=instance_luy_base_form.data)

        self.assertTrue(form.is_valid(), form.errors)
        result = form.consistency_errors
        self.assertIsInstance(result, OrderedDict)
        self.assertEqual(expected_result[next_academic_year], result[next_academic_year])

    def test_when_differences_found_on_2_next_years(self):
        next_academic_year = AcademicYear.objects.get(year=self.learning_unit_year_full.academic_year.year + 1)
        initial_credits_value, new_credits_value = self._change_credits_value(next_academic_year)
        next_academic_year_2 = AcademicYear.objects.get(year=self.learning_unit_year_full.academic_year.year + 2)
        initial_credits_value_2, new_credits_value_2 = self._change_credits_value(next_academic_year)
        expected_result = OrderedDict({
            next_academic_year: [
                _("%(col_name)s has been already modified. ({%(new_value)s} instead of {%(current_value)s})") % {
                    'col_name': "Crédits",
                    'current_value': initial_credits_value,
                    'new_value': new_credits_value
                }
            ],
            next_academic_year_2: [
                _("%(col_name)s has been already modified. ({%(new_value)s} instead of {%(current_value)s})") % {
                    'col_name': "Crédits",
                    'current_value': initial_credits_value_2,
                    'new_value': new_credits_value_2
                }
            ],
        })

        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              data=instance_luy_base_form.data)

        self.assertTrue(form.is_valid(), form.errors)
        result = form.consistency_errors
        self.assertIsInstance(result, OrderedDict)  # Need to be ordered by academic_year
        self.assertEqual(expected_result[next_academic_year], result[next_academic_year])

    def test_when_differences_found_on_entities(self):
        next_academic_year = AcademicYear.objects.get(year=self.learning_unit_year_full.academic_year.year + 1)
        initial_requirement_entity, new_requirement_entity = self._change_requirement_entity_value(next_academic_year)
        expected_result = OrderedDict({
            next_academic_year: [
                _("%(col_name)s has been already modified. ({%(new_value)s} instead of {%(current_value)s})") % {
                    'col_name': _('Requirement entity'),
                    'current_value': initial_requirement_entity,
                    'new_value': new_requirement_entity
                }
            ],
        })
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              data=instance_luy_base_form.data)

        self.assertTrue(form.is_valid(), form.errors)
        result = form.consistency_errors
        self.assertEqual(result, expected_result)

    def test_when_differences_found_on_components(self):
        next_academic_year = AcademicYear.objects.get(year=self.learning_unit_year_full.academic_year.year + 1)
        self._change_cm_component_value(next_academic_year, 12)

        expected_result = OrderedDict({
            next_academic_year: [
                _("%(col_name)s has been already modified. ({%(new_value)s} instead of {%(current_value)s})") % {
                    'col_name': _("Lecturing") + ' (' + _('hourly volume total annual') + ')',
                    'current_value': '-',
                    'new_value': '12.00'
                }
            ],
        })
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)

        form = LearningUnitPostponementForm(
            self.person,
            self.learning_unit_year_full.academic_year,
            learning_unit_instance=instance_luy_base_form.learning_unit_instance,
            data=instance_luy_base_form.data
        )

        self.assertTrue(form.is_valid(), form.errors)
        result = form.consistency_errors
        self.assertDictEqual(result, expected_result)

    def test_when_differences_found_on_entity_component(self):
        next_academic_year = AcademicYear.objects.get(year=self.learning_unit_year_full.academic_year.year + 1)
        component = self._change_entity_component_value(next_academic_year, 24)

        expected_result = OrderedDict({
            next_academic_year: [
                _("The repartition volume of %(col_name)s has been already modified. "
                  "({%(new_value)s} instead of {%(current_value)s})") % {
                    'col_name': component.learning_component_year.acronym + "-" + component.entity_container_year.entity.most_recent_acronym,
                    'new_value': component.repartition_volume,
                    'current_value': '0.00'
                }
            ],
        })
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)

        form = LearningUnitPostponementForm(
            self.person,
            self.learning_unit_year_full.academic_year,
            learning_unit_instance=instance_luy_base_form.learning_unit_instance,
            data=instance_luy_base_form.data
        )
        self.assertTrue(form.is_valid(), form.errors)
        result = form.consistency_errors
        self.assertDictEqual(result, expected_result)

    def test_postponement_with_proposal(self):
        next_academic_year = AcademicYear.objects.get(year=self.learning_unit_year_full.academic_year.year + 2)
        luy = LearningUnitYear.objects.filter(
            academic_year=next_academic_year, learning_unit=self.learning_unit_year_full.learning_unit
        ).get()

        ProposalLearningUnitFactory(learning_unit_year=luy)

        msg_proposal = _("The learning unit %(luy)s is in proposal, can not save "
                         "the change from the year %(academic_year)s") % {
                           'luy': luy.acronym, 'academic_year': next_academic_year
                       }

        expected_result = OrderedDict({
            next_academic_year: [msg_proposal],
        })

        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              data=instance_luy_base_form.data)

        self.assertTrue(form.is_valid(), form.errors)
        result = form.consistency_errors
        self.assertIsInstance(result, OrderedDict)  # Need to be ordered by academic_year
        self.assertEqual(expected_result[next_academic_year], result[next_academic_year])

    def test_when_differences_found_on_additional_requirement_entities(self):
        """
        In this test, we ensure that if N year have additional_requirement_entity_2 AND N+1 doesn't have,
        it display an error and prevent crash on _check_postponement_repartition_volume [ GET() ]
        """
        next_academic_year = AcademicYear.objects.get(year=self.learning_unit_year_full.academic_year.year + 1)
        initial_entity = self._remove_additional_requirement_entity_2(academic_year=next_academic_year)

        expected_result = OrderedDict({
            next_academic_year: [
                _("%(col_name)s has been already modified. ({%(new_value)s} instead of {%(current_value)s})") % {
                    'col_name': _('Additional requirement entity 2'),
                    'new_value': '-',
                    'current_value': initial_entity
                }
            ],
        })
        instance_luy_base_form = _instantiate_base_learning_unit_form(self.learning_unit_year_full, self.person)
        form = _instanciate_postponement_form(self.person, self.learning_unit_year_full.academic_year,
                                              learning_unit_instance=instance_luy_base_form.learning_unit_instance,
                                              data=instance_luy_base_form.data)
        self.assertTrue(form.is_valid(), form.errors)
        result = form.consistency_errors
        self.assertEqual(result, expected_result)


def _instantiate_base_learning_unit_form(learning_unit_year_instance, person):
    entity_version_by_type = entity_container_year.find_last_entity_version_grouped_by_linktypes(
        learning_unit_year_instance.learning_container_year
    )
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
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '2',
            'form-0-hourly_volume_total_annual': 20,
            'form-0-hourly_volume_partial_q1': 10,
            'form-0-hourly_volume_partial_q2': 10,
            'form-1-hourly_volume_total_annual': 20,
            'form-1-hourly_volume_partial_q1': 10,
            'form-1-hourly_volume_partial_q2': 10,

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
            'common_title': learning_unit_year_instance.learning_container_year.common_title,
            'common_title_english': learning_unit_year_instance.learning_container_year.common_title_english,
            'container_type': learning_unit_year_instance.learning_container_year.container_type,
            'type_declaration_vacant': learning_unit_year_instance.learning_container_year.type_declaration_vacant,
            'team': learning_unit_year_instance.learning_container_year.team,
            'is_vacant': learning_unit_year_instance.learning_container_year.is_vacant,

            'requirement_entity-entity':
                entity_version_by_type.get(entity_container_year_link_type.REQUIREMENT_ENTITY).id,
            'allocation_entity-entity':
                entity_version_by_type.get(entity_container_year_link_type.ALLOCATION_ENTITY).id,
            'additional_requirement_entity_1-entity':
                entity_version_by_type.get(entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1).id,
            'additional_requirement_entity_2-entity':
                entity_version_by_type.get(entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_2).id,
        },
        'person': person
    }
    return form(**form_args)


def _instanciate_postponement_form(person, start_postponement, end_postponement=None,
                                   learning_unit_instance=None, data=None, learning_unit_full_instance=None):
    return LearningUnitPostponementForm(person, start_postponement, learning_unit_instance=learning_unit_instance,
                                        learning_unit_full_instance=learning_unit_full_instance,
                                        end_postponement=end_postponement, data=data)
