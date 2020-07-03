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
import json
import random
from unittest import mock

from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from django.http import HttpResponseForbidden, HttpResponseRedirect, HttpResponse
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext as _
from waffle.testutils import override_flag

from base.forms.education_group.group import GroupYearModelForm
from base.forms.education_group.training import CertificateAimsForm
from base.models.enums import education_group_categories, internship_presence
from base.models.enums.active_status import ACTIVE
from base.models.enums.diploma_coorganization import DiplomaCoorganizationTypes
from base.models.enums.education_group_types import TrainingType, MiniTrainingType
from base.models.enums.link_type import LinkTypes
from base.models.enums.schedule_type import DAILY
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.business.learning_units import GenerateAcademicYear
from base.tests.factories.certificate_aim import CertificateAimFactory
from base.tests.factories.education_group_organization import EducationGroupOrganizationFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory, MiniTrainingFactory
from base.tests.factories.education_group_year import GroupFactory, TrainingFactory
from base.tests.factories.education_group_year_domain import EducationGroupYearDomainFactory
from base.tests.factories.entity_version import EntityVersionFactory, MainEntityVersionFactory
from base.tests.factories.group import FacultyManagerGroupFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.organization_address import OrganizationAddressFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.user import SuperUserFactory
from base.views.education_groups.update import _get_success_redirect_url, update_education_group
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from program_management.tests.factories.education_group_version import StandardEducationGroupVersionFactory
from program_management.tests.factories.element import ElementFactory
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.domain import DomainFactory
from reference.tests.factories.domain_isced import DomainIscedFactory
from reference.tests.factories.language import LanguageFactory


@override_flag('education_group_update', active=True)
class TestUpdate(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.start_academic_year = AcademicYearFactory(year=1968)
        cls.academic_year_2010 = AcademicYearFactory(year=2012)
        cls.academic_year_2019 = AcademicYearFactory(year=2018)
        cls.current_academic_year = create_current_academic_year()
        FacultyManagerGroupFactory()
        cls.start_date_ay_1 = cls.current_academic_year.start_date.replace(year=cls.current_academic_year.year + 1)
        cls.end_date_ay_1 = cls.current_academic_year.end_date.replace(year=cls.current_academic_year.year + 2)
        cls.previous_academic_year = AcademicYearFactory(year=cls.current_academic_year.year - 1)
        cls.academic_year_1 = AcademicYearFactory(start_date=cls.start_date_ay_1,
                                                  end_date=cls.end_date_ay_1,
                                                  year=cls.current_academic_year.year + 1)
        cls.start_date_ay_2 = cls.current_academic_year.start_date.replace(year=cls.current_academic_year.year + 2)
        cls.end_date_ay_2 = cls.current_academic_year.end_date.replace(year=cls.current_academic_year.year + 3)
        academic_year_2 = AcademicYearFactory(start_date=cls.start_date_ay_2,
                                              end_date=cls.end_date_ay_2,
                                              year=cls.current_academic_year.year + 2)

        cls.education_group_year = GroupFactory()

        EntityVersionFactory(entity=cls.education_group_year.management_entity,
                             start_date=cls.education_group_year.academic_year.start_date)

        EntityVersionFactory(entity=cls.education_group_year.administration_entity,
                             start_date=cls.education_group_year.academic_year.start_date)

        AuthorizedRelationshipFactory(
            parent_type=cls.education_group_year.education_group_type,
            child_type=cls.education_group_year.education_group_type
        )
        version = StandardEducationGroupVersionFactory(
            offer=cls.education_group_year,
            root_group__education_group_type=cls.education_group_year.education_group_type,
            root_group__academic_year=cls.education_group_year.academic_year,
            root_group__partial_acronym=cls.education_group_year.partial_acronym
        )
        ElementFactory(group_year=version.root_group)
        cls.url = reverse(
            update_education_group,
            kwargs={"offer_id": cls.education_group_year.pk, "education_group_year_id": cls.education_group_year.id}
        )
        cls.person = PersonFactory()
        CentralManagerFactory(person=cls.person, entity=cls.education_group_year.management_entity)

        cls.an_training_education_group_type = EducationGroupTypeFactory(category=education_group_categories.TRAINING)
        cls.education_group_type_pgrm_master_120 = EducationGroupTypeFactory(
            category=education_group_categories.TRAINING, name=TrainingType.PGRM_MASTER_120.name)

        cls.previous_training_education_group_year = TrainingFactory(
            academic_year=cls.previous_academic_year,
            education_group_type=cls.an_training_education_group_type,
            education_group__start_year=cls.start_academic_year
        )

        EntityVersionFactory(entity=cls.previous_training_education_group_year.management_entity,
                             start_date=cls.previous_training_education_group_year.academic_year.start_date)

        EntityVersionFactory(entity=cls.previous_training_education_group_year.administration_entity,
                             start_date=cls.previous_training_education_group_year.academic_year.start_date)

        cls.training_education_group_year = TrainingFactory(
            academic_year=cls.current_academic_year,
            education_group_type=cls.an_training_education_group_type,
            education_group__start_year=cls.start_academic_year
        )

        cls.training_education_group_year_1 = TrainingFactory(
            academic_year=cls.academic_year_1,
            education_group_type=cls.an_training_education_group_type,
            education_group=cls.training_education_group_year.education_group
        )

        cls.training_education_group_year_2 = TrainingFactory(
            academic_year=academic_year_2,
            education_group_type=cls.an_training_education_group_type,
            education_group=cls.training_education_group_year.education_group
        )

        AuthorizedRelationshipFactory(
            parent_type=cls.an_training_education_group_type,
            child_type=cls.an_training_education_group_type,
        )

        EntityVersionFactory(
            entity=cls.training_education_group_year.management_entity,
            start_date=cls.education_group_year.academic_year.start_date
        )

        EntityVersionFactory(
            entity=cls.training_education_group_year.administration_entity,
            start_date=cls.education_group_year.academic_year.start_date
        )

        cls.training_url = reverse(
            update_education_group,
            args=[cls.training_education_group_year.pk, cls.training_education_group_year.pk]
        )
        CentralManagerFactory(person=cls.person, entity=cls.training_education_group_year.management_entity)

        cls.domains = [DomainFactory() for _ in range(10)]

        cls.a_mini_training_education_group_type = EducationGroupTypeFactory(
            category=education_group_categories.MINI_TRAINING,
            name=MiniTrainingType.DEEPENING.name
        )

        cls.mini_training_education_group_year = MiniTrainingFactory(
            academic_year=cls.current_academic_year,
            education_group_type=cls.a_mini_training_education_group_type
        )

        cls.mini_training_url = reverse(
            update_education_group,
            args=[cls.mini_training_education_group_year.pk, cls.mini_training_education_group_year.pk]
        )
        CentralManagerFactory(person=cls.person, entity=cls.mini_training_education_group_year.management_entity)

        EntityVersionFactory(
            entity=cls.mini_training_education_group_year.management_entity,
            start_date=cls.education_group_year.academic_year.start_date
        )
        cls.country_be = CountryFactory(iso_code='BE', name='Belgium')
        cls.organization_address = OrganizationAddressFactory(country=cls.country_be)

    def setUp(self):
        self.client.force_login(self.person.user)
        permission = Permission.objects.get(codename='change_educationgroup')
        self.person.user.user_permissions.add(permission)

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_template_used(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "education_group/update_groups.html")

    def test_response_context(self):
        response = self.client.get(self.url)

        form_education_group_year = response.context["form_education_group_year"]

        self.assertIsInstance(form_education_group_year, GroupYearModelForm)

    def test_post(self):
        new_entity_version = MainEntityVersionFactory()
        CentralManagerFactory(person=self.person, entity=new_entity_version.entity)
        self.education_group_year.management_entity = new_entity_version.entity
        self.education_group_year.save()

        data = {
            'title': 'Cours au choix',
            'title_english': 'deaze',
            'education_group_type': self.education_group_year.education_group_type.id,
            'credits': 42,
            'acronym': 'CRSCHOIXDVLD',
            'partial_acronym': 'LDVLD101R',
            'management_entity': new_entity_version.pk,
            'main_teaching_campus': "",
            'academic_year': self.education_group_year.academic_year.pk,
            "constraint_type": "",
            'group_element_year_formset-TOTAL_FORMS': 0,
            'group_element_year_formset-INITIAL_FORMS': 0,
        }
        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 302)
        self.education_group_year.refresh_from_db()
        self.assertEqual(self.education_group_year.title, 'Cours au choix')
        self.assertEqual(self.education_group_year.title_english, 'deaze')
        self.assertEqual(self.education_group_year.credits, 42)
        self.assertEqual(self.education_group_year.acronym, 'CRSCHOIXDVLD')
        self.assertEqual(self.education_group_year.partial_acronym, 'LDVLD101R')
        self.assertEqual(self.education_group_year.management_entity, new_entity_version.entity)

    def test_post_with_group_not_content(self):
        new_entity_version = MainEntityVersionFactory()
        CentralManagerFactory(person=self.person, entity=new_entity_version.entity)
        self.education_group_year.management_entity = new_entity_version.entity
        self.education_group_year.save()

        data = {
            'title': 'Cours au choix',
            'title_english': 'deaze',
            'education_group_type': self.education_group_year.education_group_type.id,
            'credits': 42,
            'acronym': 'CRSCHOIXDVLD',
            'partial_acronym': 'LDVLD101R',
            'management_entity': new_entity_version.pk,
            'main_teaching_campus': "",
            'academic_year': self.education_group_year.academic_year.pk,
            "constraint_type": "",
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 302)
        self.education_group_year.refresh_from_db()
        self.assertEqual(self.education_group_year.title, 'Cours au choix')
        self.assertEqual(self.education_group_year.title_english, 'deaze')
        self.assertEqual(self.education_group_year.credits, 42)
        self.assertEqual(self.education_group_year.acronym, 'CRSCHOIXDVLD')
        self.assertEqual(self.education_group_year.partial_acronym, 'LDVLD101R')
        self.assertEqual(self.education_group_year.management_entity, new_entity_version.entity)

    def test_invalid_post_group(self):
        new_entity_version = MainEntityVersionFactory()
        CentralManagerFactory(person=self.person, entity=new_entity_version.entity)
        self.education_group_year.management_entity = new_entity_version.entity
        self.education_group_year.save()

        data = {
            'title': 'Cours au choix',
            'title_english': 'deaze',
            'education_group_type': self.education_group_year.education_group_type.id,
            'acronym': 'CRSCHOIXDVLD',
            'management_entity': new_entity_version.pk,
            'main_teaching_campus': "",
            'academic_year': self.education_group_year.academic_year.pk,
            "constraint_type": "",
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(self.url, response.request['PATH_INFO'])

    def test_template_used_for_training(self):
        response = self.client.get(self.training_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "education_group/update_trainings.html")

    def test_post_training(self):
        old_domain = DomainFactory()

        egy = TrainingFactory(
            education_group_type=self.education_group_type_pgrm_master_120,
            management_entity=self.training_education_group_year.management_entity,
            administration_entity=self.training_education_group_year.administration_entity,
            academic_year=self.current_academic_year,
            education_group__start_year=self.start_academic_year
        )
        EducationGroupYearDomainFactory(
            education_group_year=egy,
            domain=old_domain
        )

        training_url = reverse(update_education_group, args=[egy.pk, egy.pk])

        new_entity_version = MainEntityVersionFactory()
        CentralManagerFactory(person=self.person, entity=new_entity_version.entity)
        list_domains = [domain.pk for domain in self.domains]
        isced_domain = DomainIscedFactory()
        data = {
            'title': 'Cours au choix',
            'title_english': 'deaze',
            'education_group_type': self.education_group_type_pgrm_master_120.pk,
            'credits': 42,
            'acronym': 'CRSCHOIXDVLD',
            'partial_acronym': 'LDVLD101R',
            'management_entity': new_entity_version.pk,
            'administration_entity': new_entity_version.pk,
            'main_teaching_campus': "",
            'academic_year': self.training_education_group_year.academic_year.pk,
            'secondary_domains': ['|' + ('|'.join([str(domain.pk) for domain in self.domains])) + '|'],
            'isced_domain': isced_domain.pk,
            'active': ACTIVE,
            'schedule_type': DAILY,
            "internship": internship_presence.NO,
            "primary_language": LanguageFactory().pk,
            "start_year": self.academic_year_2010,
            "constraint_type": "",
            "diploma_printing_title": "Diploma Title",
            'form-TOTAL_FORMS': 0,
            'form-INITIAL_FORMS': 0,
            'group_element_year_formset-TOTAL_FORMS': 0,
            'group_element_year_formset-INITIAL_FORMS': 0,
        }
        response = self.client.post(training_url, data=data)
        self.assertEqual(response.status_code, 302)

        egy.refresh_from_db()
        self.assertEqual(egy.title, 'Cours au choix')
        self.assertEqual(egy.title_english, 'deaze')
        self.assertEqual(egy.credits, 42)
        self.assertEqual(egy.acronym, 'CRSCHOIXDVLD')
        self.assertEqual(egy.partial_acronym, 'LDVLD101R')
        self.assertEqual(egy.management_entity, new_entity_version.entity)
        self.assertEqual(egy.administration_entity, new_entity_version.entity)
        self.assertEqual(egy.isced_domain, isced_domain)
        self.assertCountEqual(
            list(egy.secondary_domains.values_list('id', flat=True)),
            list_domains
        )
        self.assertNotIn(old_domain, egy.secondary_domains.all())

    def test_post_invalid_training(self):
        old_domain = DomainFactory()

        egy = TrainingFactory(
            education_group_type=self.education_group_type_pgrm_master_120,
            management_entity=self.training_education_group_year.management_entity,
            administration_entity=self.training_education_group_year.administration_entity,
            academic_year=self.current_academic_year,
            education_group__start_year=self.start_academic_year
        )
        EducationGroupYearDomainFactory(
            education_group_year=egy,
            domain=old_domain
        )

        training_url = reverse(update_education_group, args=[egy.pk, egy.pk])

        new_entity_version = MainEntityVersionFactory()
        CentralManagerFactory(person=self.person, entity=new_entity_version.entity)
        isced_domain = DomainIscedFactory()
        data = {
            'title': 'Cours au choix',
            'title_english': 'deaze',
            'education_group_type': self.education_group_type_pgrm_master_120.pk,
            'acronym': 'CRSCHOIXDVLD',
            'management_entity': new_entity_version.pk,
            'administration_entity': new_entity_version.pk,
            'main_teaching_campus': "",
            'academic_year': self.training_education_group_year.academic_year.pk,
            'secondary_domains': ['|' + ('|'.join([str(domain.pk) for domain in self.domains])) + '|'],
            'isced_domain': isced_domain.pk,
            'active': ACTIVE,
            'schedule_type': DAILY,
            "internship": internship_presence.NO,
            "primary_language": LanguageFactory().pk,
            "start_year": 2010,
            "constraint_type": "",
            "diploma_printing_title": "Diploma Title",
            'form-TOTAL_FORMS': 0,
            'form-INITIAL_FORMS': 0,
            'group_element_year_formset-TOTAL_FORMS': 0,
            'group_element_year_formset-INITIAL_FORMS': 0,
        }
        response = self.client.post(training_url, data=data)
        self.assertEqual(training_url, response.request['PATH_INFO'])

    def test_post_training_with_a_coorganization(self):
        egy, new_entity_version, organization = self._prepare_training_and_organization()
        self.assertEqual(egy.coorganizations.count(), 0)
        diploma_choice = random.choice(DiplomaCoorganizationTypes.get_names())
        data = {
            'title': 'Cours au choix',
            'education_group_type': egy.education_group_type.pk,
            'acronym': 'CRSCHOIXDVLD',
            'partial_acronym': 'LDVLD101R',
            'management_entity': new_entity_version.pk,
            'administration_entity': new_entity_version.pk,
            'academic_year': egy.academic_year.pk,
            'active': ACTIVE,
            'schedule_type': DAILY,
            "internship": internship_presence.NO,
            "primary_language": LanguageFactory().pk,
            "constraint_type": "",
            "diploma_printing_title": "Diploma Title",
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-0-country': OrganizationAddressFactory(organization=organization, is_main=True).country.pk,
            'form-0-organization': organization.pk,
            'form-0-diploma': diploma_choice,
            'group_element_year_formset-TOTAL_FORMS': 0,
            'group_element_year_formset-INITIAL_FORMS': 0,
        }

        url = reverse(update_education_group, args=[egy.pk, egy.pk])
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

        egy.refresh_from_db()
        coorganizations = egy.coorganizations
        self.assertEqual(coorganizations.count(), 1)
        self.assertEqual(coorganizations.first().organization, organization)
        self.assertEqual(coorganizations.first().diploma, diploma_choice)

    def test_post_invalid_training_with_a_coorganization(self):
        new_entity_version = MainEntityVersionFactory()
        egy = TrainingFactory(
            education_group_type__name=TrainingType.AGGREGATION.name,
            management_entity=new_entity_version.entity,
            administration_entity=new_entity_version.entity
        )
        CentralManagerFactory(person=self.person, entity=new_entity_version.entity)
        organization = OrganizationFactory()
        address = OrganizationAddressFactory(organization=organization, is_main=True)
        diploma_choice = random.choice(DiplomaCoorganizationTypes.get_names())

        data = {
            'title': 'Cours au choix',
            'education_group_type': egy.education_group_type.pk,
            'management_entity': new_entity_version.pk,
            'administration_entity': new_entity_version.pk,
            'academic_year': egy.academic_year.pk,
            'active': ACTIVE,
            'schedule_type': DAILY,
            "internship": internship_presence.NO,
            "primary_language": LanguageFactory().pk,
            "constraint_type": "",
            "diploma_printing_title": "Diploma Title",
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-0-country': address.country,
            'form-0-organization': organization.pk,
            'form-0-diploma': diploma_choice,
            'group_element_year_formset-TOTAL_FORMS': 0,
            'group_element_year_formset-INITIAL_FORMS': 0,
        }

        url = reverse(update_education_group, args=[egy.pk, egy.pk])
        response = self.client.post(url, data=data)
        self.assertEqual(url, response.request['PATH_INFO'])

    def test_post_training_removing_coorganization(self):
        egy, new_entity_version, organization = self._prepare_training_and_organization()
        diploma_choice = random.choice(DiplomaCoorganizationTypes.get_names())
        egy_organization = EducationGroupOrganizationFactory(
            organization=organization,
            education_group_year=egy,
            diploma=diploma_choice
        )

        self.assertEqual(egy.coorganizations.count(), 1)
        data = {
            'title': 'Cours au choix',
            'education_group_type': egy.education_group_type.pk,
            'acronym': 'CRSCHOIXDVLD',
            'partial_acronym': 'LDVLD101R',
            'management_entity': new_entity_version.pk,
            'administration_entity': new_entity_version.pk,
            'academic_year': egy.academic_year.pk,
            'active': ACTIVE,
            'schedule_type': DAILY,
            "internship": internship_presence.NO,
            "primary_language": LanguageFactory().pk,
            "constraint_type": "",
            "diploma_printing_title": "Diploma Title",
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-0-country': OrganizationAddressFactory(organization=organization, is_main=True).country.pk,
            'form-0-organization': organization.pk,
            'form-0-diploma': diploma_choice,
            'form-0-DELETE': 'on',
            'form-0-id': egy_organization.pk,
            'group_element_year_formset-TOTAL_FORMS': 0,
            'group_element_year_formset-INITIAL_FORMS': 0,
        }

        url = reverse(update_education_group, args=[egy.pk, egy.pk])
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

        egy.refresh_from_db()
        coorganizations = egy.coorganizations
        self.assertEqual(coorganizations.count(), 0)

    def _prepare_training_and_organization(self):
        new_entity_version = MainEntityVersionFactory()
        egy = TrainingFactory(
            education_group_type__name=TrainingType.AGGREGATION.name,
            management_entity=new_entity_version.entity,
            administration_entity=new_entity_version.entity
        )
        CentralManagerFactory(person=self.person, entity=new_entity_version.entity)
        organization = OrganizationFactory()
        return egy, new_entity_version, organization

    def test_post_mini_training(self):
        old_domain = DomainFactory()
        EducationGroupYearDomainFactory(
            education_group_year=self.mini_training_education_group_year,
            domain=old_domain
        )

        new_entity_version = MainEntityVersionFactory()
        CentralManagerFactory(person=self.person, entity=new_entity_version.entity)
        data = {
            'title': 'Cours au choix',
            'title_english': 'deaze',
            'education_group_type': self.a_mini_training_education_group_type.pk,
            'credits': 42,
            'acronym': 'CRSCHOIXDVLD',
            'partial_acronym': 'LDVLD101R',
            'management_entity': new_entity_version.pk,
            'main_teaching_campus': "",
            'academic_year': self.mini_training_education_group_year.academic_year.pk,
            'active': ACTIVE,
            'schedule_type': DAILY,
            "primary_language": LanguageFactory().pk,
            "start_year": self.academic_year_2010,
            "constraint_type": "",
            "diploma_printing_title": "Diploma Title",
            'group_element_year_formset-TOTAL_FORMS': 0,
            'group_element_year_formset-INITIAL_FORMS': 0,
        }
        response = self.client.post(self.mini_training_url, data=data)
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

        self.mini_training_education_group_year.refresh_from_db()
        self.assertEqual(self.mini_training_education_group_year.title, 'Cours au choix')
        self.assertEqual(self.mini_training_education_group_year.title_english, 'deaze')
        self.assertEqual(self.mini_training_education_group_year.credits, 42)
        self.assertEqual(self.mini_training_education_group_year.acronym, 'CRSCHOIXDVLD')
        self.assertEqual(self.mini_training_education_group_year.partial_acronym, 'LDVLD101R')
        self.assertEqual(self.mini_training_education_group_year.management_entity, new_entity_version.entity)

    def test_post_invalid_mini_training(self):
        old_domain = DomainFactory()
        EducationGroupYearDomainFactory(
            education_group_year=self.mini_training_education_group_year,
            domain=old_domain
        )

        new_entity_version = MainEntityVersionFactory()
        CentralManagerFactory(person=self.person, entity=new_entity_version.entity)
        data = {
            'title': 'Cours au choix',
            'title_english': 'deaze',
            'education_group_type': self.a_mini_training_education_group_type.pk,
            'acronym': 'CRSCHOIXDVLD',
            'management_entity': new_entity_version.pk,
            'main_teaching_campus': "",
            'academic_year': self.mini_training_education_group_year.academic_year.pk,
            'active': ACTIVE,
            'schedule_type': DAILY,
            "primary_language": LanguageFactory().pk,
            "start_year": 2010,
            "constraint_type": "",
            "diploma_printing_title": "Diploma Title",
        }
        response = self.client.post(self.mini_training_url, data=data)
        self.assertEqual(self.mini_training_url, response.request['PATH_INFO'])

    def test_post_training_with_end_year(self):
        new_entity_version = MainEntityVersionFactory()
        CentralManagerFactory(person=self.person, entity=new_entity_version.entity)
        data = {
            'title': 'Cours au choix',
            'title_english': 'deaze',
            'education_group_type': self.an_training_education_group_type.pk,
            'credits': 42,
            'acronym': 'CRSCHOIXDVLD',
            'partial_acronym': 'LDVLD101R',
            'management_entity': new_entity_version.pk,
            'administration_entity': new_entity_version.pk,
            'main_teaching_campus': "",
            'academic_year': self.training_education_group_year.academic_year.pk,
            'secondary_domains': ['|' + ('|'.join([str(domain.pk) for domain in self.domains])) + '|'],
            'active': ACTIVE,
            'schedule_type': DAILY,
            "internship": internship_presence.NO,
            "primary_language": LanguageFactory().pk,
            "start_year": self.academic_year_2010.pk,
            "end_year": self.current_academic_year.pk,
            "constraint_type": "",
            "diploma_printing_title": "Diploma Title",
            'form-TOTAL_FORMS': 0,
            'form-INITIAL_FORMS': 0,
            'group_element_year_formset-TOTAL_FORMS': 0,
            'group_element_year_formset-INITIAL_FORMS': 0,
        }
        response = self.client.post(self.training_url, data=data)
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(
            messages[1], _("Education group year %(acronym)s (%(academic_year)s) successfuly deleted.") % {
                "acronym": self.training_education_group_year_1.acronym,
                "academic_year": self.training_education_group_year_1.academic_year,
            }
        )
        self.assertEqual(
            messages[2], _("Education group year %(acronym)s (%(academic_year)s) successfuly deleted.") % {
                "acronym": self.training_education_group_year_2.acronym,
                "academic_year": self.training_education_group_year_2.academic_year,
            }
        )

    def test_post_with_edited_content(self):
        new_entity_version = MainEntityVersionFactory()
        egy = TrainingFactory(
            academic_year=self.current_academic_year,
            education_group_type__name=TrainingType.PGRM_MASTER_120.name,
            management_entity=new_entity_version.entity,
            administration_entity=new_entity_version.entity
        )
        CentralManagerFactory(person=self.person, entity=new_entity_version.entity)
        sub_egy = TrainingFactory(
            academic_year=self.current_academic_year,
            education_group_type__name=TrainingType.AGGREGATION.name,
            management_entity=new_entity_version.entity,
            administration_entity=new_entity_version.entity
        )
        group = GroupElementYearFactory(
            parent=egy,
            child_branch=sub_egy
        )
        data = {
            'title': 'Cours au choix',
            'title_english': 'deaze',
            'education_group_type': egy.education_group_type.pk,
            'credits': 42,
            'acronym': 'CRSCHOIXDVLD',
            'partial_acronym': 'LDVLD101R',
            'administration_entity': new_entity_version.pk,
            'management_entity': new_entity_version.pk,
            'main_teaching_campus': "",
            'academic_year': egy.academic_year.pk,
            'active': ACTIVE,
            'schedule_type': DAILY,
            "primary_language": LanguageFactory().pk,
            "start_year": self.academic_year_2010,
            "constraint_type": "",
            "internship": internship_presence.NO,
            "diploma_printing_title": "Diploma Title",
            'group_element_year_formset-TOTAL_FORMS': 1,
            'group_element_year_formset-INITIAL_FORMS': 1,
            'group_element_year_formset-0-block': 1,
            'group_element_year_formset-0-is_mandatory': True,
            'group_element_year_formset-0-comment': "COMMENT_TEST",
            'group_element_year_formset-0-link_type': LinkTypes.REFERENCE.name,
            'group_element_year_formset-0-id': group.pk,
        }
        url = reverse(update_education_group, args=[egy.pk, egy.pk])
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

        group.refresh_from_db()
        self.assertEqual(group.block, 1)
        self.assertTrue(group.is_mandatory)
        self.assertEqual(group.comment, 'COMMENT_TEST')
        self.assertEqual(group.link_type, LinkTypes.REFERENCE.name)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(
            messages[3],
            _("The link of %(acronym)s has been updated") % {
                'acronym': " - ".join([
                    group.child_branch.partial_acronym, group.child_branch.acronym, str(group.parent.academic_year)
                ])
            }
        )


class TestGetSuccessRedirectUrl(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        cls.education_group_year = EducationGroupYearFactory(
            academic_year=cls.current_academic_year
        )
        start_year = AcademicYearFactory(year=cls.current_academic_year.year + 1)
        end_year = AcademicYearFactory(year=cls.current_academic_year.year + 5)
        cls.ac_year_in_future = GenerateAcademicYear(start_year=start_year, end_year=end_year)

        cls.education_group_year_in_future = []
        for ac_in_future in cls.ac_year_in_future.academic_years:
            cls.education_group_year_in_future.append(EducationGroupYearFactory(
                education_group=cls.education_group_year.education_group,
                academic_year=ac_in_future
            ))

    def test_get_redirect_success_url_when_exist(self):
        expected_url = reverse(
            "element_identification",
            kwargs={
                "year": self.education_group_year.academic_year.year,
                "code": self.education_group_year.partial_acronym
            }
        )
        result = _get_success_redirect_url(self.education_group_year, self.education_group_year)
        self.assertEqual(result, expected_url)

    def test_get_redirect_success_url_when_current_viewed_has_been_deleted(self):
        current_viewed = self.education_group_year_in_future[-1]
        current_viewed.delete()
        # Expected URL is the latest existing [-2]
        expected_url = reverse(
            "element_identification",
            kwargs={
                "year": self.education_group_year_in_future[-2].academic_year.year,
                "code": self.education_group_year_in_future[-2].partial_acronym
            }
        )
        result = _get_success_redirect_url(current_viewed, current_viewed)
        self.assertEqual(result, expected_url)


class TestCertificateAimAutocomplete(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.super_user = SuperUserFactory()
        cls.url = reverse("certificate_aim_autocomplete")
        cls.certificate_aim = CertificateAimFactory(
            code=1234,
            section=5,
            description="description",
        )

    def test_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url, data={'q': '1234'})
        json_response = str(response.content, encoding='utf8')
        results = json.loads(json_response)['results']
        self.assertEqual(results, [])

    def test_when_param_is_digit_assert_searching_on_code(self):
        # When searching on "code"
        self.client.force_login(user=self.super_user)
        response = self.client.get(self.url, data={'q': '1234'})
        self._assert_result_is_correct(response)

    def test_assert_searching_on_description(self):
        # When searching on "description"
        self.client.force_login(user=self.super_user)
        response = self.client.get(self.url, data={'q': 'descr'})
        self._assert_result_is_correct(response)

    def test_with_filter_by_section(self):
        self.client.force_login(user=self.super_user)
        response = self.client.get(self.url, data={'forward': '{"section": "5"}'})
        self._assert_result_is_correct(response)

    def _assert_result_is_correct(self, response):
        self.assertEqual(response.status_code, 200)
        json_response = str(response.content, encoding='utf8')
        results = json.loads(json_response)['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], str(self.certificate_aim.id))


@override_flag('education_group_update', active=True)
class TestCertificateAimView(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.academic_year = AcademicYearFactory(year=2019)
        cls.training = TrainingFactory(academic_year=cls.academic_year)

        cls.program_manager = ProgramManagerFactory(education_group=cls.training.education_group)
        read_permission = Permission.objects.get(codename='view_educationgroup')
        write_permission = Permission.objects.get(codename='change_educationgroupcertificateaim')
        cls.program_manager.person.user.user_permissions.add(read_permission, write_permission)

    def setUp(self):
        super().setUp()
        self.url = reverse("update_education_group", kwargs={
            "offer_id": self.training.pk,
            "education_group_year_id": self.training.pk
        })
        self.client.force_login(user=self.program_manager.person.user)

    def test_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_user_is_not_program_manager_of_training(self):
        training_without_pgrm_manager = TrainingFactory(academic_year=self.academic_year)
        url = reverse("update_education_group", kwargs={
            "offer_id": training_without_pgrm_manager.pk,
            "education_group_year_id": training_without_pgrm_manager.pk
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_use_certificate_aims_template(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "education_group/blocks/form/training_certificate.html")

    def test_ensure_context_kwargs(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertEqual(response.context['education_group_year'], self.training)
        self.assertIsInstance(response.context['form_certificate_aims'], CertificateAimsForm)

    @mock.patch('base.views.education_groups.update.CertificateAimsForm')
    def test_post_method_ensure_data_is_correctly_save(self, mock_form):
        mock_form.return_value.is_valid.return_value = True
        mock_form.return_value.save.return_value = self.training

        response = self.client.post(self.url, data={'dummy_key': 'dummy'})
        excepted_url = reverse(
            "element_identification",
            kwargs={
                "year": self.training.academic_year.year,
                "code": self.training.partial_acronym
            }
        )
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'success_url': excepted_url}
        )
