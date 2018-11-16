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
import datetime

from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils.translation import ugettext_lazy as _

from base.forms.learning_unit.learning_unit_create import LearningUnitYearModelForm
from base.forms.utils.acronym_field import PartimAcronymField, AcronymField
from base.models.enums import learning_container_year_types, organization_type
from base.models.enums.attribution_procedure import INTERNAL_TEAM
from base.models.enums.entity_container_year_link_type import REQUIREMENT_ENTITY, ALLOCATION_ENTITY, \
    ADDITIONAL_REQUIREMENT_ENTITY_2, ADDITIONAL_REQUIREMENT_ENTITY_1
from base.models.enums.internship_subtypes import PROFESSIONAL_INTERNSHIP
from base.models.enums.learning_unit_year_periodicity import ANNUAL
from base.models.enums.learning_unit_year_subtypes import FULL, PARTIM
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import CENTRAL_MANAGER_GROUP, FACULTY_MANAGER_GROUP
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_container import LearningContainerFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory
from reference.tests.factories.language import LanguageFactory


class TestLearningUnitYearModelFormInit(TestCase):
    """Tests LearningUnitYearModelForm.__init__()"""
    def setUp(self):
        create_current_academic_year()
        self.central_manager = PersonFactory()
        self.central_manager.user.groups.add(Group.objects.get(name=CENTRAL_MANAGER_GROUP))
        self.faculty_manager = PersonFactory()
        self.faculty_manager.user.groups.add(Group.objects.get(name=FACULTY_MANAGER_GROUP))

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
        self.assertEqual(self.form.fields['specific_title'].label, _('Title proper to the partim'))
        self.assertEqual(self.form.fields['specific_title_english'].label, _('English title proper to the partim'))

    def test_case_update_academic_year_is_disabled(self):
        self.form = LearningUnitYearModelForm(data=None, person=self.central_manager, subtype=PARTIM,
                                              instance=LearningUnitYearFactory())
        self.assertTrue(self.form.fields['academic_year'].disabled)

    def test_case_update_internship_subtype_is_disabled(self):
        container = LearningContainerYearFactory(container_type=learning_container_year_types.COURSE)
        self.form = LearningUnitYearModelForm(
            data=None, person=self.central_manager, subtype=PARTIM,
            instance=LearningUnitYearFactory(learning_container_year=container)
        )

        self.assertTrue(self.form.fields['internship_subtype'].disabled)

        container.container_type = learning_container_year_types.INTERNSHIP
        container.save()
        self.form = LearningUnitYearModelForm(
            data=None, person=self.central_manager, subtype=PARTIM,
            instance=LearningUnitYearFactory(learning_container_year=container)
        )

        self.assertFalse(self.form.fields['internship_subtype'].disabled)


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
        campus = CampusFactory(organization=OrganizationFactory(type=organization_type.MAIN))
        self.language = LanguageFactory(code='FR')

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
            'attribution_procedure': INTERNAL_TEAM,
            'campus': campus.pk,
            'language': self.language.pk,
            'periodicity': ANNUAL,

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

        EntityVersionFactory(entity=self.additional_requirement_entity_1.entity,
                             start_date=self.learning_container_year.academic_year.start_date,
                             end_date=self.learning_container_year.academic_year.end_date)

        EntityVersionFactory(entity=self.additional_requirement_entity_2.entity,
                             start_date=self.learning_container_year.academic_year.start_date,
                             end_date=self.learning_container_year.academic_year.end_date)

        self.allocation_entity_version = EntityVersionFactory(
            entity=self.allocation_entity.entity, start_date=self.learning_container_year.academic_year.start_date,
            end_date=self.learning_container_year.academic_year.end_date)

        self.requirement_entity_version = EntityVersionFactory(
            entity=self.requirement_entity.entity, start_date=self.learning_container_year.academic_year.start_date,
            end_date=self.learning_container_year.academic_year.end_date)

        self.entity_container_years = [self.requirement_entity, self.allocation_entity,
                                       self.additional_requirement_entity_1, self.additional_requirement_entity_2]

    def test_case_missing_required_learning_container_year_kwarg(self):
        with self.assertRaises(KeyError):
            self.form.save(learning_unit=self.learning_unit)

    def test_case_missing_required_learning_unit_kwarg(self):
        with self.assertRaises(KeyError):
            self.form.save(learning_container_year=self.learning_container_year)

    def test_post_data_correctly_saved_case_creation(self):
        form = LearningUnitYearModelForm(data=self.post_data, person=self.central_manager, subtype=FULL)
        self.assertTrue(form.is_valid(), form.errors)
        luy = form.save(learning_container_year=self.learning_container_year, learning_unit=self.learning_unit)

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

    def test_case_update_post_data_correctly_saved(self):
        learning_unit_year_to_update = LearningUnitYearFactory(
            learning_unit=self.learning_unit, learning_container_year=self.learning_container_year, subtype=FULL,
            academic_year=self.current_academic_year
        )

        form = LearningUnitYearModelForm(data=self.post_data, person=self.central_manager, subtype=FULL,
                                         instance=learning_unit_year_to_update)
        self.assertTrue(form.is_valid(), form.errors)
        luy = form.save(learning_container_year=self.learning_container_year, learning_unit=self.learning_unit)

        self.assertEqual(luy, learning_unit_year_to_update)

    def test_warnings_credit(self):
        learning_unit_year_to_update = LearningUnitYearFactory(
            learning_unit=self.learning_unit, learning_container_year=self.learning_container_year, subtype=FULL,
            academic_year=self.current_academic_year
        )

        partim = LearningUnitYearFactory(learning_container_year=self.learning_container_year, subtype=PARTIM,
                                         credits=120)

        self.post_data['credits'] = 60
        form = LearningUnitYearModelForm(data=self.post_data, person=self.central_manager, subtype=FULL,
                                         instance=learning_unit_year_to_update)
        self.assertTrue(form.is_valid(), form.errors)

        self.assertEqual(form.instance.warnings, [_("The credits value of the partim %(acronym)s is greater or "
                                                    "equal than the credits value of the parent learning unit.") % {
            'acronym': partim.acronym}])

    def test_no_warnings_credit(self):
        """ This test will ensure that no message warning message is displayed when no PARTIM attached to FULL"""
        learning_unit_year_to_update = LearningUnitYearFactory(
            learning_unit=self.learning_unit, learning_container_year=self.learning_container_year, subtype=FULL,
            academic_year=self.current_academic_year
        )

        LearningUnitYear.objects.filter(
            learning_container_year=learning_unit_year_to_update.learning_container_year,
            subtype=PARTIM
        ).delete()
        self.post_data['credits'] = 60
        form = LearningUnitYearModelForm(data=self.post_data, person=self.central_manager, subtype=FULL,
                                         instance=learning_unit_year_to_update)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(form.instance.warnings)

    def test_single_warnings_entity_container_year(self):
        learning_unit_year_to_update = LearningUnitYearFactory(
            learning_unit=self.learning_unit, learning_container_year=self.learning_container_year, subtype=FULL,
            academic_year=self.current_academic_year
        )
        self.requirement_entity_version.start_date = datetime.date(1990, 9, 15)
        self.requirement_entity_version.end_date = datetime.date(1990, 9, 15)
        self.requirement_entity_version.save()
        self.requirement_entity.refresh_from_db()
        form = LearningUnitYearModelForm(data=self.post_data, person=self.central_manager, subtype=FULL,
                                         instance=learning_unit_year_to_update)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(len(form.instance.warnings), 1)
        self.assertEqual(form.instance.warnings,
                         [_("The linked %(entity)s does not exist at the start date of the academic year linked to this"
                            " learning unit") % {'entity': _(REQUIREMENT_ENTITY.lower())}])

    def test_multiple_warnings_entity_container_year(self):
        learning_unit_year_to_update = LearningUnitYearFactory(
            learning_unit=self.learning_unit, learning_container_year=self.learning_container_year, subtype=FULL,
            academic_year=self.current_academic_year
        )
        self.requirement_entity_version.start_date = datetime.date(1990, 9, 15)
        self.requirement_entity_version.end_date = datetime.date(1990, 9, 15)
        self.requirement_entity_version.save()
        self.requirement_entity.refresh_from_db()

        self.allocation_entity_version.start_date = datetime.date(1990, 9, 15)
        self.allocation_entity_version.end_date = datetime.date(1990, 9, 15)
        self.allocation_entity_version.save()
        self.allocation_entity_version.refresh_from_db()

        form = LearningUnitYearModelForm(data=self.post_data, person=self.central_manager, subtype=FULL,
                                         instance=learning_unit_year_to_update)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(len(form.instance.warnings), 2)
        self.assertTrue(_("The linked %(entity)s does not exist at the start date of the academic year linked to this"
                          " learning unit") % {'entity': _(REQUIREMENT_ENTITY.lower())} in form.instance.warnings)
        self.assertTrue(_("The linked %(entity)s does not exist at the start date of the academic year linked to this"
                          " learning unit") % {'entity': _(ALLOCATION_ENTITY.lower())} in form.instance.warnings)
