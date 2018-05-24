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

from django import forms
from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils.translation import ugettext_lazy as _

from base.forms.learning_unit.learning_unit_create import LearningUnitYearModelForm
from base.forms.utils.acronym_field import PartimAcronymField, AcronymField
from base.models.entity_component_year import EntityComponentYear
from base.models.enums import learning_container_year_types
from base.models.enums.attribution_procedure import INTERNAL_TEAM
from base.models.enums.entity_container_year_link_type import REQUIREMENT_ENTITY, ALLOCATION_ENTITY, \
    ADDITIONAL_REQUIREMENT_ENTITY_2, ADDITIONAL_REQUIREMENT_ENTITY_1
from base.models.enums.internship_subtypes import PROFESSIONAL_INTERNSHIP
from base.models.enums.learning_container_year_types import MASTER_THESIS, OTHER_INDIVIDUAL
from base.models.enums.learning_unit_year_subtypes import FULL, PARTIM
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import CENTRAL_MANAGER_GROUP, FACULTY_MANAGER_GROUP
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.learning_container import LearningContainerFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory


class TestLearningUnitYearModelFormInit(TestCase):
    """Tests LearningUnitYearModelForm.__init__()"""
    def setUp(self):
        self.central_manager = PersonFactory()
        self.central_manager.user.groups.add(Group.objects.get(name=CENTRAL_MANAGER_GROUP))
        self.faculty_manager = PersonFactory()
        self.faculty_manager.user.groups.add(Group.objects.get(name=FACULTY_MANAGER_GROUP))

    def test_internship_subtype_removed_when_user_is_faculty_manager(self):

        self.form = LearningUnitYearModelForm(data=None, person=self.central_manager, subtype=FULL)
        self.assertIsInstance(self.form.fields.get('internship_subtype'), forms.TypedChoiceField)

        self.form = LearningUnitYearModelForm(data=None, person=self.faculty_manager, subtype=FULL)
        self.assertIsNone(self.form.fields.get('internship_subtype'))

    def test_acronym_field_case_partim(self):
        self.form = LearningUnitYearModelForm(data=None, person=self.central_manager, subtype=PARTIM)
        self.assertIsInstance(self.form.fields.get('acronym'),
                              PartimAcronymField,
                              "should assert field is PartimAcronymField")

    def test_acronym_field_case_full(self):
        self.form = LearningUnitYearModelForm(data=None, person=self.central_manager, subtype=FULL)
        self.assertIsInstance(self.form.fields.get('acronym'), AcronymField, "should assert field is AcronymField")

    def test_label_specific_title_case_partim(self):
        self.form = LearningUnitYearModelForm(data=None, person=self.central_manager, subtype=PARTIM)
        self.assertEqual(self.form.fields['specific_title'].label, _('official_title_proper_to_partim'))
        self.assertEqual(self.form.fields['specific_title_english'].label, _('official_english_title_proper_to_partim'))

    def test_case_update_academic_year_is_disabled(self):
        self.form = LearningUnitYearModelForm(data=None, person=self.central_manager, subtype=PARTIM,
                                              instance=LearningUnitYearFactory())
        self.assertTrue(self.form.fields['academic_year'].disabled)


class TestLearningUnitYearModelFormSave(TestCase):
    """Tests LearningUnitYearModelForm.save()"""

    def setUp(self):
        self.central_manager = PersonFactory()
        self.central_manager.user.groups.add(Group.objects.get(name=CENTRAL_MANAGER_GROUP))
        self.faculty_manager = PersonFactory()
        self.faculty_manager.user.groups.add(Group.objects.get(name=FACULTY_MANAGER_GROUP))
        self.current_academic_year = create_current_academic_year()

        self.learning_container = LearningContainerFactory()
        self.learning_unit = LearningUnitFactory(learning_container=self.learning_container)
        self.learning_container_year = LearningContainerYearFactory(learning_container=self.learning_container,
                                                                    academic_year=self.current_academic_year,
                                                                    container_type=learning_container_year_types.COURSE)
        self.form = LearningUnitYearModelForm(data=None, person=self.central_manager, subtype=FULL)

        self.post_data = {
            'acronym_0': 'L',
            'acronym_1': 'OSIS9001',
            'academic_year': self.current_academic_year.pk,
            'specific_title': 'The hobbit',
            'specific_title_english': 'An Unexpected Journey',
            'credits': 3,
            'session': '3',
            'status': True,
            'quadrimester': 'Q1',
            'internship_subtype': PROFESSIONAL_INTERNSHIP,
            'attribution_procedure': INTERNAL_TEAM
        }

        self.requirement_entity = EntityContainerYearFactory(type=REQUIREMENT_ENTITY,
                                                             learning_container_year=self.learning_container_year)
        self.allocation_entity = EntityContainerYearFactory(type=ALLOCATION_ENTITY,
                                                            learning_container_year=self.learning_container_year)
        self.additional_requirement_entity_1 = EntityContainerYearFactory(
            type=ADDITIONAL_REQUIREMENT_ENTITY_1,
            learning_container_year=self.learning_container_year)
        self.additional_requirement_entity_2 = EntityContainerYearFactory(
            type=ADDITIONAL_REQUIREMENT_ENTITY_2,
            learning_container_year=self.learning_container_year)

        self.entity_container_years = [self.requirement_entity, self.allocation_entity,
                                       self.additional_requirement_entity_1, self.additional_requirement_entity_2]

    def test_case_missing_required_learning_container_year_kwarg(self):
        with self.assertRaises(KeyError):
            self.form.save(learning_unit=self.learning_unit, entity_container_years=[])

    def test_case_missing_required_learning_unit_kwarg(self):
        with self.assertRaises(KeyError):
            self.form.save(learning_container_year=self.learning_container_year, entity_container_years=[])

    def test_case_missing_required_entity_container_years_kwarg(self):
        with self.assertRaises(KeyError):
            self.form.save(learning_container_year=self.learning_container_year, learning_unit=self.learning_unit)

    def test_post_data_correctly_saved_case_creation(self):
        form = LearningUnitYearModelForm(data=self.post_data, person=self.central_manager, subtype=FULL)
        self.assertTrue(form.is_valid(), form.errors)
        luy = form.save(learning_container_year=self.learning_container_year, learning_unit=self.learning_unit,
                        entity_container_years=[])

        self.assertEqual(luy.acronym, ''.join([self.post_data['acronym_0'], self.post_data['acronym_1']]))
        self.assertEqual(luy.academic_year.pk, self.post_data['academic_year'])
        self.assertEqual(luy.specific_title, self.post_data['specific_title'])
        self.assertEqual(luy.specific_title_english, self.post_data['specific_title_english'])
        self.assertEqual(luy.credits, self.post_data['credits'])
        self.assertEqual(luy.session, self.post_data['session'])
        self.assertEqual(luy.quadrimester, self.post_data['quadrimester'])
        self.assertEqual(luy.status, self.post_data['status'])
        self.assertEqual(luy.internship_subtype, self.post_data['internship_subtype'])
        self.assertEqual(luy.attribution_procedure, self.post_data['attribution_procedure'])

    def test_components_are_correctly_saved_when_creation_of_container_type_master_thesis(self):
        self.learning_container_year.container_type = MASTER_THESIS
        self.learning_container_year.save()
        form = LearningUnitYearModelForm(data=self.post_data, person=self.central_manager, subtype=FULL)
        self.assertTrue(form.is_valid(), form.errors)
        luy = form.save(learning_container_year=self.learning_container_year, learning_unit=self.learning_unit,
                        entity_container_years=[])

        qs = LearningComponentYear.objects.filter(learningunitcomponent__learning_unit_year=luy).order_by('acronym')
        self.assertEqual(qs.count(), 2, "should assert 2 components are created (1 TP - 1 LECTURING)")
        self.assertListEqual(list(qs.values_list('acronym', flat=True)), ['CM1', 'TP1'],
                             " acronyms should be ='CM1' and 'TP1")

    def test_components_are_correctly_saved_when_creation_of_container_type_other_individual(self):
        self.learning_container_year.container_type = OTHER_INDIVIDUAL
        self.learning_container_year.save()
        form = LearningUnitYearModelForm(data=self.post_data, person=self.central_manager, subtype=FULL)
        self.assertTrue(form.is_valid(), form.errors)
        luy = form.save(learning_container_year=self.learning_container_year, learning_unit=self.learning_unit,
                        entity_container_years=[])

        qs = LearningComponentYear.objects.filter(learningunitcomponent__learning_unit_year=luy).order_by('acronym')
        self.assertEqual(qs.count(), 1, "should assert 1 only component of type=None is created with acronym 'NT1'")
        self.assertListEqual(list(qs.values_list('acronym', flat=True)), ['NT1'])

    def test_entity_components_year_correctly_saved(self):
        form = LearningUnitYearModelForm(data=self.post_data, person=self.central_manager, subtype=FULL)
        self.assertTrue(form.is_valid(), form.errors)
        luy = form.save(learning_container_year=self.learning_container_year, learning_unit=self.learning_unit,
                        entity_container_years=self.entity_container_years)

        qs = EntityComponentYear.objects.filter(learning_component_year__learningunitcomponent__learning_unit_year=luy)
        self.assertEqual(qs.count(), 6)
        qs_requirement_entity = qs.filter(entity_container_year=self.requirement_entity)
        self.assertEqual(qs_requirement_entity.count(), 2)

    def test_case_update_post_data_correctly_saved(self):
        learning_unit_year_to_update = LearningUnitYearFactory(
            learning_unit=self.learning_unit, learning_container_year=self.learning_container_year, subtype=FULL)

        form = LearningUnitYearModelForm(data=self.post_data, person=self.central_manager, subtype=FULL,
                                         instance=learning_unit_year_to_update)
        self.assertTrue(form.is_valid(), form.errors)
        luy = form.save(learning_container_year=self.learning_container_year, learning_unit=self.learning_unit,
                        entity_container_years=self.entity_container_years)

        self.assertEqual(luy, learning_unit_year_to_update)

    def test_warnings_credit(self):
        learning_unit_year_to_update = LearningUnitYearFactory(
            learning_unit=self.learning_unit, learning_container_year=self.learning_container_year, subtype=FULL)

        partim = LearningUnitYearFactory(learning_container_year=self.learning_container_year, subtype=PARTIM,
                                         credits=120)

        self.post_data['credits'] = 60
        form = LearningUnitYearModelForm(data=self.post_data, person=self.central_manager, subtype=FULL,
                                         instance=learning_unit_year_to_update)
        self.assertTrue(form.is_valid(), form.errors)

        self.assertEqual(form.warnings, [_("The credits value of the partim %(acronym)s is greater or "
                                           "equal than the credits value of the parent learning unit.") % {
            'acronym': partim.acronym}])

    def test_no_warnings_credit(self):
        """ This test will ensure that no message warning message is displayed when no PARTIM attached to FULL"""
        learning_unit_year_to_update = LearningUnitYearFactory(
            learning_unit=self.learning_unit, learning_container_year=self.learning_container_year, subtype=FULL)

        LearningUnitYear.objects.filter(
            learning_container_year=learning_unit_year_to_update.learning_container_year,
            subtype=PARTIM
        ).delete()
        self.post_data['credits'] = 60
        form = LearningUnitYearModelForm(data=self.post_data, person=self.central_manager, subtype=FULL,
                                         instance=learning_unit_year_to_update)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(form.warnings)
