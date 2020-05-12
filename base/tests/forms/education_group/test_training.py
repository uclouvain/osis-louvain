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
from django.utils.translation import gettext_lazy as _

from base.business.education_groups.postponement import FIELD_TO_EXCLUDE_IN_SET
from base.business.utils.model import model_to_dict_fk
from base.forms.education_group.training import TrainingForm, TrainingEducationGroupYearForm, \
    HopsEducationGroupYearModelForm, CertificateAimsForm
from base.models.education_group_certificate_aim import EducationGroupCertificateAim
from base.models.education_group_organization import EducationGroupOrganization
from base.models.education_group_type import EducationGroupType
from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_categories, internship_presence, education_group_types, entity_type
from base.models.enums.active_status import ACTIVE
from base.models.enums.schedule_type import DAILY
from base.tests.factories.academic_calendar import AcademicCalendarEducationGroupEditionFactory
from base.tests.factories.academic_year import create_current_academic_year, get_current_year, AcademicYearFactory
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.business.learning_units import GenerateAcademicYear
from base.tests.factories.certificate_aim import CertificateAimFactory
from base.tests.factories.education_group_certificate_aim import EducationGroupCertificateAimFactory
from base.tests.factories.education_group_organization import EducationGroupOrganizationFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import TrainingFactory, EducationGroupYearFactory
from base.tests.factories.education_group_year_domain import EducationGroupYearDomainFactory
from base.tests.factories.entity_version import MainEntityVersionFactory
from base.tests.factories.group import GroupFactory
from base.tests.factories.hops import HopsFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory
from base.tests.forms.education_group.test_common import EducationGroupYearModelFormMixin
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from reference.tests.factories.domain import DomainFactory
from reference.tests.factories.language import LanguageFactory
from rules_management.enums import TRAINING_DAILY_MANAGEMENT, TRAINING_PGRM_ENCODING_PERIOD
from rules_management.tests.fatories import PermissionFactory, FieldReferenceFactory


class TestTrainingEducationGroupYearForm(EducationGroupYearModelFormMixin):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=get_current_year())
        cls.central_manager = GroupFactory(name='central_managers')
        cls.education_group_type = EducationGroupTypeFactory(category=education_group_categories.TRAINING)
        cls.form_class = TrainingEducationGroupYearForm
        cls.hops_form_class = HopsEducationGroupYearModelForm
        super(TestTrainingEducationGroupYearForm, cls).setUpTestData(education_group_type=cls.education_group_type)

    def setUp(self):
        self.hops = HopsFactory(
            education_group_year=self.parent_education_group_year,
            ares_study=100,
            ares_graca=200,
            ares_ability=300
        )

    def test_clean_certificate_aims(self):
        administration_entity_version = MainEntityVersionFactory(end_date=None)
        management_entity_version = MainEntityVersionFactory(end_date=None)
        person = PersonFactory()
        CentralManagerFactory(
            person=person,
            entity=management_entity_version.entity
        )

        parent_education_group_year = TrainingFactory(academic_year=self.academic_year,
                                                      education_group_type=self.education_group_type,
                                                      management_entity=management_entity_version.entity,
                                                      administration_entity=administration_entity_version.entity,
                                                      )
        AuthorizedRelationshipFactory(
            parent_type=parent_education_group_year.education_group_type,
            child_type=self.education_group_type,
        )

        cert = [CertificateAimFactory(code=code, section=2) for code in range(100, 102)]
        for i in range(0, len(cert)):
            with self.subTest(i=i):
                cert_for_form = [str(cert[j].pk) for j in range(0, i + 1)]

                form = self.form_class(
                    data={
                        'acronym': "EEDY2020",
                        'partial_acronym': 'EEDY2020F',
                        'title': "Test",
                        'internship': 'OPTIONAL',
                        'primary_language': LanguageFactory().pk,
                        'active': 'ACTIVE',
                        'schedule_type': 'DAILY',
                        'administration_entity': administration_entity_version.pk,
                        'management_entity': management_entity_version.pk,
                        'diploma_printing_title': 'Diplome en test',
                        'certificate_aims': cert_for_form,
                    },
                    parent=parent_education_group_year,
                    education_group_type=parent_education_group_year.education_group_type,
                    user=person.user,
                )
                if i == 0:
                    self.assertTrue(form.is_valid())
                else:
                    self.assertFalse(form.is_valid())

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

    def test_valid_hopsform(self):
        form_education_group_year = HopsEducationGroupYearModelForm(
            data={
                'ares_study': 1,
                'ares_graca': 2,
                'ares_ability': 3,
            },
            user=self.user,
            instance=self.hops
        )
        self.assertFalse(form_education_group_year.fields["ares_study"].required)
        self.assertFalse(form_education_group_year.fields["ares_graca"].required)
        self.assertFalse(form_education_group_year.fields["ares_ability"].required)

    def test_not_valid_hopsform(self):
        form_education_group_year = HopsEducationGroupYearModelForm(
            data={
                'ares_study': 1,
            },
            user=self.user,
            instance=self.hops)
        self.assertFalse(form_education_group_year.is_valid())
        self.assertEqual(list(form_education_group_year.errors['ares_study'])[0],
                         _('The fields concerning ARES have to be ALL filled-in or none of them'))

    def test_save_hopsform(self):
        form_education_group_year = HopsEducationGroupYearModelForm(
            data={
                'ares_study': 10,
                'ares_graca': 20,
                'ares_ability': 30,
            },
            user=self.user,
            instance=self.hops
        )
        if form_education_group_year.is_valid():
            hops_updated = form_education_group_year.save(education_group_year=self.parent_education_group_year)
            self.assertEqual(hops_updated.ares_study, 10)
            self.assertEqual(hops_updated.ares_graca, 20)
            self.assertEqual(hops_updated.ares_ability, 30)
            self.assertEqual(hops_updated.id, self.hops.id)

    def test_save_hopsform_without_ares_data(self):
        form_education_group_year = HopsEducationGroupYearModelForm(
            data={},
            user=self.user,
            instance=self.hops
        )
        self.assertTrue(form_education_group_year.is_valid())
        hops_updated = form_education_group_year.save(education_group_year=self.parent_education_group_year)
        self.assertIsNone(hops_updated)


class TestPostponementEducationGroupYear(TestCase):
    @classmethod
    def setUpTestData(cls):
        start_year = AcademicYearFactory(year=get_current_year())
        end_year = AcademicYearFactory(year=get_current_year() + 40)
        cls.list_acs = GenerateAcademicYear(start_year, end_year).academic_years
        # Create user and attached it to management entity
        cls.person = PersonFactory()
        cls.user = cls.person.user
        cls.management_entity_version = MainEntityVersionFactory()
        cls.education_group_type = EducationGroupTypeFactory(
            category=education_group_categories.TRAINING,
            name=education_group_types.TrainingType.BACHELOR.name
        )

    def setUp(self):
        self.data = {
            'title': 'Métamorphose',
            'title_english': 'Transfiguration',
            'education_group_type': self.education_group_type.pk,
            'credits': 42,
            'acronym': 'CRSCHOIXDVLD',
            'partial_acronym': 'LDVLD101R',
            'management_entity': self.management_entity_version.pk,
            'administration_entity': MainEntityVersionFactory().pk,
            'main_teaching_campus': "",
            'academic_year': create_current_academic_year().pk,
            'active': ACTIVE,
            'schedule_type': DAILY,
            "internship": internship_presence.NO,
            "primary_language": LanguageFactory().pk,
            "start_year": 2010,
            "constraint_type": "",
            "diploma_printing_title": 'Diploma title'
        }
        self.administration_entity_version = MainEntityVersionFactory()
        self.education_group_year = TrainingFactory(
            academic_year=create_current_academic_year(),
            education_group_type__name=education_group_types.TrainingType.BACHELOR.name,
            management_entity=self.management_entity_version.entity,
            administration_entity=self.administration_entity_version.entity,
        )
        CentralManagerFactory(person=self.person, entity=self.education_group_year.management_entity)

    def test_init(self):
        # In case of creation
        form = TrainingForm({}, user=self.user, education_group_type=self.education_group_type)
        self.assertFalse(form.dict_initial_egy)
        self.assertEqual(form.initial_dicts, {'educationgrouporganization_set': {}})

        # In case of update
        coorg = EducationGroupOrganizationFactory(
            organization=OrganizationFactory(),
            education_group_year=self.education_group_year
        )
        form = TrainingForm(
            {},
            user=self.user,
            instance=self.education_group_year
        )
        dict_initial_egy = model_to_dict_fk(
            self.education_group_year, exclude=form.field_to_exclude
        )

        self.assertEqual(str(form.dict_initial_egy), str(dict_initial_egy))
        initial_dict_coorg = model_to_dict_fk(
            self.education_group_year.coorganizations.first(), exclude=FIELD_TO_EXCLUDE_IN_SET
        )
        self.assertEqual(
            form.initial_dicts,
            {'educationgrouporganization_set': {coorg.organization.id: initial_dict_coorg}}
        )

    def test_save_with_postponement(self):
        # Create postponed egy
        self._create_postponed_egys()

        # Update egys
        self.education_group_year.refresh_from_db()

        self.assertEqual(self.education_group_year.educationgrouporganization_set.all().count(), 0)
        EducationGroupOrganizationFactory(
            organization=OrganizationFactory(),
            education_group_year=self.education_group_year
        )
        self.assertEqual(self.education_group_year.educationgrouporganization_set.all().count(), 1)

        self.data["title"] = "Defence Against the Dark Arts"
        self._postpone_coorganization_and_check()

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

    def test_save_with_postponement_sets_inconsistents(self):
        # create postponed egy's
        self._create_postponed_egys()

        # update with inconsistant EducationGroupOrganization (organization present in the future not in present)
        self.education_group_year.refresh_from_db()
        unconsistent_egy = EducationGroupYear.objects.get(
            education_group=self.education_group_year.education_group,
            academic_year=self.list_acs[4]
        )
        EducationGroupOrganizationFactory(
            organization=OrganizationFactory(),
            education_group_year=unconsistent_egy
        )
        EducationGroupOrganizationFactory(
            organization=OrganizationFactory(),
            education_group_year=self.education_group_year
        )

        form = TrainingForm(self.data, instance=self.education_group_year, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.assertGreater(len(form.warnings), 0)
        self.assertEqual(
            form.warnings,
            [
                _("Consistency error in %(academic_year)s : %(error)s") % {
                    'academic_year': unconsistent_egy.academic_year,
                    'error': EducationGroupOrganization._meta.verbose_name.title()
                }
            ]
        )

    def test_save_with_postponement_coorganization_inconsistant(self):
        # create postponed egy's
        self._create_postponed_egys()

        # update with a coorganization to postpone
        self.education_group_year.refresh_from_db()

        good_organization = EducationGroupOrganizationFactory(
            organization=OrganizationFactory(),
            education_group_year=self.education_group_year
        )
        self._postpone_coorganization_and_check()

        # update with unconsistant EducationGroupOrganization (field different from a year to another one)
        self.education_group_year.refresh_from_db()
        unconsistent_egy = EducationGroupYear.objects.get(
            education_group=self.education_group_year.education_group,
            academic_year=self.list_acs[4]
        )
        unconsistent_orga = EducationGroupOrganization.objects.get(
            education_group_year=unconsistent_egy
        )
        unconsistent_orga.all_students = not good_organization.all_students
        unconsistent_orga.save()
        # have to invalidate cache
        del self.education_group_year.coorganizations
        form = TrainingForm(self.data, instance=self.education_group_year, user=self.user)

        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(len(form.warnings), 1)
        error_msg = _("%(col_name)s has been already modified.") % {
            "col_name": _(EducationGroupOrganization._meta.get_field('all_students').verbose_name).title(),
        }
        self.assertEqual(
            form.warnings,
            [
                _("Consistency error in %(academic_year)s with %(model)s: %(error)s") % {
                    'academic_year': unconsistent_egy.academic_year,
                    'model': EducationGroupOrganization._meta.verbose_name.title(),
                    'error': error_msg
                }
            ]
        )

    def _postpone_coorganization_and_check(self):
        form = TrainingForm(self.data, instance=self.education_group_year, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(len(form.warnings), 0, form.warnings)
        all_egys = EducationGroupYear.objects.filter(
            education_group=self.education_group_year.education_group
        )
        self.assertEqual(all_egys.count(), 7)
        for egy in all_egys:
            self.assertEqual(egy.educationgrouporganization_set.all().count(), 1)

    def _create_postponed_egys(self):
        form = TrainingForm(
            self.data,
            instance=self.education_group_year,
            user=self.user
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(len(form.education_group_year_postponed), 6)
        self.assertEqual(len(form.warnings), 0)
        self.assertEqual(
            EducationGroupYear.objects.filter(education_group=self.education_group_year.education_group).count(), 7
        )

    def test_save_with_postponement_m2m(self):
        domains = [DomainFactory(name="Alchemy"), DomainFactory(name="Muggle Studies")]
        self.data["secondary_domains"] = '|'.join([str(domain.pk) for domain in domains])

        certificate_aims = [CertificateAimFactory(code=100, section=1), CertificateAimFactory(code=101, section=2)]
        self.data["certificate_aims"] = [str(aim.pk) for aim in certificate_aims]

        self._create_postponed_egys()

        last = EducationGroupYear.objects.filter(education_group=self.education_group_year.education_group
                                                 ).order_by('academic_year').last()

        self.education_group_year.refresh_from_db()
        self.assertEqual(self.education_group_year.secondary_domains.count(), 2)
        self.assertEqual(last.secondary_domains.count(), 2)
        self.assertEqual(last.certificate_aims.count(), len(certificate_aims))

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


class TestPostponeTrainingProperty(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.current_academic_year = AcademicYearFactory(current=True)
        cls.generated_ac_years = AcademicYearFactory.produce(
            base_year=cls.current_academic_year.year,
            number_past=0,
            number_future=7
        )
        cls.entity_version = MainEntityVersionFactory(entity_type=entity_type.SECTOR)
        cls.person = PersonFactory()
        CentralManagerFactory(person=cls.person, entity=cls.entity_version.entity)
        cls.training = TrainingFactory(
            management_entity=cls.entity_version.entity,
            administration_entity=cls.entity_version.entity,
            academic_year=cls.current_academic_year
        )
        cls.form_data = model_to_dict_fk(cls.training, exclude=('secondary_domains',))
        cls.form_data.update({
            'primary_language': cls.form_data['primary_language_id'],
            'administration_entity': cls.entity_version.pk,
            'management_entity': cls.entity_version.pk
        })

    def test_save_with_postponement_certificate_aims_inconsistant(self):
        """
        This test ensure that the we haven't an error if the certificate aims is inconsistant in future because
        certificate aims is managed by program_manager (This form is only accessible on Central/Faculty manager)
        """
        # Save the training instance will create N+6 data...
        form = TrainingForm(self.form_data, instance=self.training, user=self.person.user)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        # Add certificate aims in future...
        training_future = EducationGroupYear.objects.filter(
            education_group=self.training.education_group,
            academic_year__year=self.training.academic_year.year + 2
        ).get()
        certificate_aims_in_future = EducationGroupCertificateAimFactory(education_group_year=training_future)

        # Re-save and ensure that there are not consitency errors and the modification is correctly postponed
        form = TrainingForm(
            {**self.form_data, "title": "Modification du titre"},
            instance=self.training,
            user=self.person.user,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertFalse(form.warnings, form.warnings)

        training_future.refresh_from_db()
        self.assertEqual(training_future.title, "Modification du titre")

        # Ensure that certificate aims has not be modified during postponement
        self.assertTrue(EducationGroupCertificateAim.objects.filter(pk=certificate_aims_in_future.pk).exists())


class TestPostponeCertificateAims(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.current_academic_year = AcademicYearFactory(current=True)
        cls.generated_ac_years = AcademicYearFactory.produce(
            base_year=cls.current_academic_year.year,
            number_past=0,
            number_future=7
        )
        cls.entity_version = MainEntityVersionFactory(entity_type=entity_type.SECTOR)
        cls.person = PersonFactory()
        CentralManagerFactory(person=cls.person, entity=cls.entity_version.entity)
        cls.training = TrainingFactory(
            management_entity=cls.entity_version.entity,
            administration_entity=cls.entity_version.entity,
            academic_year=cls.current_academic_year
        )
        # Save the training instance will create N+6 data...
        form_data = model_to_dict_fk(cls.training, exclude=('secondary_domains',))
        form_data.update({
            'primary_language': form_data['primary_language_id'],
            'administration_entity': cls.entity_version.pk,
            'management_entity': cls.entity_version.pk
        })
        training_form = TrainingForm(form_data, instance=cls.training, user=cls.person.user)
        training_form.is_valid()
        training_form.save()

        cls.certificate_aim_type_2 = CertificateAimFactory(section=2, code=200)
        cls.certificate_aim_type_4 = CertificateAimFactory(section=4, code=400)
        cls.form_data = {
            'certificate_aims': [cls.certificate_aim_type_2.pk, cls.certificate_aim_type_4.pk]
        }

    def setUp(self):
        self.qs_training_futures = EducationGroupYear.objects.filter(
            education_group=self.training.education_group,
            academic_year__year__gt=self.training.academic_year.year
        )

    def test_save_with_postponement_on_training_which_have_property_different_in_future(self):
        """
        This test ensure that the consistency check is OK even if one/multiple properties on training are
        different in futures
        """
        #  Update multiple property on training future
        self.qs_training_futures.update(
            title='Modification du titre dans le futur',
            professional_title='Modification du titre professionel'
        )

        form = CertificateAimsForm(self.form_data, instance=self.training)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertFalse(form.warnings, form.warnings)

        self.assertEqual(
            form.get_instances_valid(),
            [self.training] + list(self.qs_training_futures.order_by('academic_year__year')),
            msg="The instance must be ordered in order to be compare year by year in sliding way"
        )
        for education_group_year in self.qs_training_futures.all():
            error_test_msg = "Certificate aims not reported on year {}".format(education_group_year.academic_year.year)
            self.assertEqual(education_group_year.certificate_aims.count(), 2, msg=error_test_msg)

    def test_save_case_consistency_raised_because_property_different_in_future(self):
        """
        This test ensure that the consistency check is raised an exception because certificate aims
        is different in future
        """
        # Update in future
        training_in_future = self.qs_training_futures.last()
        certificate_aim_type_9 = CertificateAimFactory(section=9, code=900)
        form = CertificateAimsForm({'certificate_aims': [certificate_aim_type_9]}, instance=training_in_future)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertFalse(form.warnings, form.warnings)

        # Update current training...
        form = CertificateAimsForm(self.form_data, instance=self.training)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        error_expected = _("%(col_name)s has been already modified.") % {
            "col_name": _(EducationGroupYear._meta.get_field('certificate_aims').verbose_name).title(),
        }
        warnings_expected = [
            _("Consistency error in %(academic_year)s with %(model)s: %(error)s") % {
                'academic_year': training_in_future.academic_year,
                'model': EducationGroupYear._meta.verbose_name.title(),
                'error': error_expected
            }
        ]
        self.assertEqual(form.warnings, warnings_expected, form.warnings)

        edgy_postponed_expected = list(
            self.qs_training_futures.exclude(pk=training_in_future.pk)
                .order_by('academic_year__year')
        )
        self.assertEqual(form.education_group_year_postponed, edgy_postponed_expected)


class TestPermissionField(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_current_academic_year()
        cls.permissions = [PermissionFactory() for _ in range(10)]

        FieldReferenceFactory(
            content_type=ContentType.objects.get(app_label="base", model="educationgroupyear"),
            field_name="main_teaching_campus",
            context=TRAINING_DAILY_MANAGEMENT,
            permissions=cls.permissions,
        )

        FieldReferenceFactory(
            content_type=ContentType.objects.get(app_label="base", model="educationgroupyear"),
            field_name="partial_acronym",
            context="",
            permissions=cls.permissions,
        )

        person = PersonFactory()
        cls.user_with_perm = person.user
        cls.user_with_perm.user_permissions.add(cls.permissions[2])

        person = PersonFactory()
        cls.user_without_perm = person.user
        cls.user_without_perm.user_permissions.add(PermissionFactory())

        cls.education_group_type = EducationGroupTypeFactory(
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

    def test_ensure_diploma_tab_fields_property(self):
        form = TrainingForm(
            {},
            user=self.user_with_perm,
            education_group_type=self.education_group_type,
            context=TRAINING_DAILY_MANAGEMENT,
        )
        expected_fields = [
            'joint_diploma', 'diploma_printing_title', 'professional_title',
            'section', 'certificate_aims'
        ]
        self.assertEqual(form.diploma_tab_fields, expected_fields)

    def test_ensure_show_diploma_tab_is_hidden(self):
        """
        This test ensure that the show diploma property is False if all fields contains in tab are disabled
        """
        form = TrainingForm(
            {},
            user=self.user_without_perm,
            education_group_type=self.education_group_type,
            context=TRAINING_DAILY_MANAGEMENT,
        )
        for field_name_in_diploma in form.diploma_tab_fields:
            form.forms[forms.ModelForm].fields[field_name_in_diploma].disabled = True

        self.assertFalse(form.show_diploma_tab())
