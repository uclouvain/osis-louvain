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
from unittest.mock import patch

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from base.business.utils.model import model_to_dict_fk
from base.forms.education_group.training import TrainingForm, TrainingEducationGroupYearForm
from base.models.education_group_type import EducationGroupType
from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_categories, internship_presence
from base.models.enums.active_status import ACTIVE
from base.models.enums.schedule_type import DAILY
from base.tests.factories.academic_calendar import AcademicCalendarEducationGroupEditionFactory
from base.tests.factories.academic_year import create_current_academic_year, get_current_year
from base.tests.factories.business.learning_units import GenerateAcademicYear
from base.tests.factories.certificate_aim import CertificateAimFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import TrainingFactory, EducationGroupYearFactory
from base.tests.factories.education_group_year_domain import EducationGroupYearDomainFactory
from base.tests.factories.entity_version import MainEntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.forms.education_group.test_common import EducationGroupYearModelFormMixin
from reference.tests.factories.domain import DomainFactory
from reference.tests.factories.language import LanguageFactory
from rules_management.enums import TRAINING_DAILY_MANAGEMENT, TRAINING_PGRM_ENCODING_PERIOD
from rules_management.tests.fatories import PermissionFactory, FieldReferenceFactory


class TestTrainingEducationGroupYearForm(EducationGroupYearModelFormMixin):
    def setUp(self):
        self.education_group_type = EducationGroupTypeFactory(category=education_group_categories.TRAINING)
        self.form_class = TrainingEducationGroupYearForm
        super(TestTrainingEducationGroupYearForm, self).setUp(education_group_type=self.education_group_type)

    @patch('base.forms.education_group.common.find_authorized_types')
    def test_get_context_for_field_references_case_not_in_editing_pgrm_period(self, mock_authorized_types):
        mock_authorized_types.return_value = EducationGroupType.objects.all()
        context = self.form_class(
            parent=self.parent_education_group_year,
            education_group_type=self.education_group_type,
            user=self.user,
        ).get_context()
        self.assertTrue(context, TRAINING_DAILY_MANAGEMENT)

    @patch('base.forms.education_group.common.find_authorized_types')
    def test_get_context_for_field_references_case_in_editing_pgrm_period(self, mock_authorized_types):
        mock_authorized_types.return_value = EducationGroupType.objects.all()
        # Create an academic calendar for event EDUCATION_GROUP_EDITION
        AcademicCalendarEducationGroupEditionFactory(
            start_date=datetime.date.today() - datetime.timedelta(days=5),
            end_date=datetime.date.today() + datetime.timedelta(days=30),
        )
        context = self.form_class(
            parent=self.parent_education_group_year,
            education_group_type=self.education_group_type,
            user=self.user,
        ).get_context()
        self.assertTrue(context, TRAINING_PGRM_ENCODING_PERIOD)


class TestPostponementEducationGroupYear(TestCase):
    def setUp(self):
        administration_entity_version = MainEntityVersionFactory()
        management_entity_version = MainEntityVersionFactory()

        self.education_group_year = TrainingFactory(
            academic_year=create_current_academic_year(),
            management_entity=management_entity_version.entity,
            administration_entity=administration_entity_version.entity,
        )
        self.education_group_type = EducationGroupTypeFactory(
            category=education_group_categories.TRAINING
        )

        self.list_acs = GenerateAcademicYear(get_current_year(), get_current_year() + 40).academic_years

        self.data = {
            'title': 'Métamorphose',
            'title_english': 'Transfiguration',
            'education_group_type': self.education_group_type.pk,
            'credits': 42,
            'acronym': 'CRSCHOIXDVLD',
            'partial_acronym': 'LDVLD101R',
            'management_entity': management_entity_version.pk,
            'administration_entity': MainEntityVersionFactory().pk,
            'main_teaching_campus': "",
            'academic_year': create_current_academic_year().pk,
            'active': ACTIVE,
            'schedule_type': DAILY,
            "internship": internship_presence.NO,
            "primary_language": LanguageFactory().pk,
            "start_year": 2010,
            "constraint_type": "",
        }

        # Create user and attached it to management entity
        person = PersonFactory()
        PersonEntityFactory(person=person, entity=self.education_group_year.management_entity)
        self.user = person.user

    def test_init(self):
        # In case of creation
        form = TrainingForm({}, user=self.user, education_group_type=self.education_group_type)
        self.assertFalse(form.dict_initial_egy)

        # In case of update
        form = TrainingForm(
            {},
            user=self.user,
            instance=self.education_group_year
        )
        dict_initial_egy = model_to_dict_fk(
            self.education_group_year, exclude=form.field_to_exclude
        )

        self.assertEqual(str(form.dict_initial_egy), str(dict_initial_egy))

    def test_save_with_postponement(self):
        # Create postponed egy
        form = TrainingForm(
            self.data,
            instance=self.education_group_year,
            user=self.user
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.assertEqual(len(form.education_group_year_postponed), 6)

        self.assertEqual(
            EducationGroupYear.objects.filter(education_group=self.education_group_year.education_group).count(), 7
        )
        self.assertEqual(len(form.warnings), 0)

        # Update egys
        self.education_group_year.refresh_from_db()

        self.data["title"] = "Defence Against the Dark Arts"
        form = TrainingForm(self.data, instance=self.education_group_year, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.assertEqual(
            EducationGroupYear.objects.filter(
                education_group=self.education_group_year.education_group
            ).count(), 7
        )
        self.assertEqual(len(form.warnings), 0, form.warnings)

    def test_save_with_postponement_error(self):
        EducationGroupYearFactory(
            academic_year=self.list_acs[4],
            education_group=self.education_group_year.education_group,
            duration=100
        )

        form = TrainingForm(
            self.data,
            instance=self.education_group_year,
            user=self.user
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.assertEqual(len(form.education_group_year_postponed), 5)

        egs = EducationGroupYear.objects.filter(education_group=self.education_group_year.education_group)

        self.assertEqual(egs.count(), 7)
        self.assertGreater(len(form.warnings), 0)

    def test_save_with_postponement_m2m(self):
        domains = [DomainFactory(name="Alchemy"), DomainFactory(name="Muggle Studies")]
        self.data["secondary_domains"] = '|'.join([str(domain.pk) for domain in domains])

        certificate_aims = [CertificateAimFactory(code=code) for code in range(100, 103)]
        self.data["certificate_aims"] = [str(aim.pk) for aim in certificate_aims]

        form = TrainingForm(
            self.data,
            instance=self.education_group_year,
            user=self.user
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.assertEqual(len(form.education_group_year_postponed), 6)

        self.assertEqual(
            EducationGroupYear.objects.filter(education_group=self.education_group_year.education_group).count(), 7
        )
        last = EducationGroupYear.objects.filter(education_group=self.education_group_year.education_group
                                                 ).order_by('academic_year').last()

        self.education_group_year.refresh_from_db()
        self.assertEqual(self.education_group_year.secondary_domains.count(), 2)
        self.assertEqual(last.secondary_domains.count(), 2)
        self.assertEqual(last.certificate_aims.count(), 3)
        self.assertEqual(len(form.warnings), 0)

        # update with a conflict
        dom3 = DomainFactory(name="Divination")
        EducationGroupYearDomainFactory(domain=dom3, education_group_year=last)

        domains = [DomainFactory(name="Care of Magical Creatures"), DomainFactory(name="Muggle Studies")]

        self.data["secondary_domains"] = '|'.join([str(domain.pk) for domain in domains])

        form = TrainingForm(self.data, instance=self.education_group_year, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.assertEqual(len(form.education_group_year_postponed), 5)

        self.assertEqual(
            EducationGroupYear.objects.filter(education_group=self.education_group_year.education_group).count(), 7
        )
        last.refresh_from_db()
        self.education_group_year.refresh_from_db()

        self.assertEqual(self.education_group_year.secondary_domains.count(), 2)
        self.assertEqual(last.secondary_domains.count(), 3)
        self.assertEqual(len(form.warnings), 1)


class TestPermissionField(TestCase):
    def setUp(self):
        self.permissions = [PermissionFactory() for _ in range(10)]

        FieldReferenceFactory(
            content_type=ContentType.objects.get(app_label="base", model="educationgroupyear"),
            field_name="main_teaching_campus",
            context=TRAINING_DAILY_MANAGEMENT,
            permissions=self.permissions,
        )

        FieldReferenceFactory(
            content_type=ContentType.objects.get(app_label="base", model="educationgroupyear"),
            field_name="partial_acronym",
            context="",
            permissions=self.permissions,
        )

        person = PersonFactory()
        self.user_with_perm = person.user
        self.user_with_perm.user_permissions.add(self.permissions[2])

        person = PersonFactory()
        self.user_without_perm = person.user
        self.user_without_perm.user_permissions.add(PermissionFactory())

        self.education_group_type = EducationGroupTypeFactory(
            category=education_group_categories.TRAINING
        )

    def test_init_case_user_with_perms(self):
        """
        In this test, we ensure that field present in FieldReference and user have permission is NOT disabled
         ==> [main_teaching_campus]
        For field which are not present in FieldReference (same context), the field is not disabled by default
         ==> [partial_acronym]
        """
        form = TrainingForm(
            {},
            user=self.user_with_perm,
            education_group_type=self.education_group_type,
            context=TRAINING_DAILY_MANAGEMENT,
        )
        self.assertFalse(form.forms[forms.ModelForm].fields["main_teaching_campus"].disabled)
        self.assertFalse(form.forms[forms.ModelForm].fields["partial_acronym"].disabled)

    def test_init_case_user_without_perms(self):
        """
        In this test, we ensure that field present in FieldReference and user don't have permission is disabled
         ==> [main_teaching_campus]
        For field which are not present in FieldReference (same context), the field is not disabled by default
         ==> [partial_acronym]
        """
        form = TrainingForm(
            {},
            user=self.user_without_perm,
            education_group_type=self.education_group_type,
            context=TRAINING_DAILY_MANAGEMENT,
        )
        self.assertTrue(form.forms[forms.ModelForm].fields["main_teaching_campus"].disabled)
        self.assertFalse(form.forms[forms.ModelForm].fields["partial_acronym"].disabled)
