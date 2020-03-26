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
import datetime
import itertools
import json
import random
from decimal import Decimal
from unittest import mock

import factory.fuzzy
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseRedirect
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from waffle.testutils import override_flag

import base.business.learning_unit
import base.business.xls
import reference.models.language
from base.business import learning_unit as learning_unit_business
from base.business.learning_unit_xls import learning_unit_titles_part2, learning_unit_titles_part_1, create_xls
from base.enums.component_detail import VOLUME_TOTAL, VOLUME_Q1, VOLUME_Q2, PLANNED_CLASSES, \
    VOLUME_REQUIREMENT_ENTITY, VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1, VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2, \
    VOLUME_TOTAL_REQUIREMENT_ENTITIES, REAL_CLASSES
from base.forms.learning_unit.learning_unit_create import LearningUnitModelForm
from base.forms.learning_unit_specifications import LearningUnitSpecificationsForm, LearningUnitSpecificationsEditForm
from base.models.academic_year import AcademicYear
from base.models.enums import active_status, education_group_categories, \
    learning_component_year_type, proposal_type, proposal_state, quadrimesters
from base.models.enums import entity_type
from base.models.enums import internship_subtypes
from base.models.enums import learning_container_year_types, organization_type
from base.models.enums import learning_unit_year_periodicity
from base.models.enums import learning_unit_year_session
from base.models.enums import learning_unit_year_subtypes
from base.models.enums.academic_calendar_type import LEARNING_UNIT_EDITION_FACULTY_MANAGERS
from base.models.enums.attribution_procedure import EXTERNAL
from base.models.enums.learning_unit_year_subtypes import FULL
from base.models.enums.vacant_declaration_type import DO_NOT_ASSIGN, VACANT_NOT_PUBLISH
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year, get_current_year
from base.tests.factories.business.learning_units import GenerateContainer, GenerateAcademicYear
from base.tests.factories.campus import CampusFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_achievement import LearningAchievementFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_container import LearningContainerFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_enrollment import LearningUnitEnrollmentFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory, LearningUnitYearFakerFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory, PersonWithPermissionsFactory, FacultyManagerFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from base.tests.factories.user import SuperUserFactory, UserFactory
from base.tests.factories.utils.get_messages import get_messages_from_response
from base.views.learning_unit import learning_unit_components, learning_unit_specifications, \
    learning_unit_comparison, \
    learning_unit_proposal_comparison, learning_unit_formations
from base.views.learning_unit import learning_unit_specifications_edit
from base.views.learning_units.create import create_partim_form
from base.views.learning_units.detail import SEARCH_URL_PART
from base.views.learning_units.pedagogy.read import learning_unit_pedagogy
from cms.enums import entity_name
from cms.models.translated_text import TranslatedText
from cms.tests.factories.text_label import TextLabelFactory
from cms.tests.factories.translated_text import TranslatedTextFactory
from cms.tests.factories.translated_text_label import TranslatedTextLabelFactory
from learning_unit.api.views.learning_unit import LearningUnitFilter
from learning_unit.tests.factories.learning_class_year import LearningClassYearFactory
from osis_common.document import xls_build
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.language import LanguageFactory


@override_flag('learning_unit_create', active=True)
class LearningUnitViewCreateFullTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        LanguageFactory(code='FR')
        cls.current_academic_year = create_current_academic_year()
        cls.url = reverse('learning_unit_create', kwargs={'academic_year_id': cls.current_academic_year.id})
        cls.user = PersonWithPermissionsFactory("can_access_learningunit", "can_create_learningunit").user

    def setUp(self):
        self.client.force_login(self.user)

    def test_create_full_form_when_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

    def test_create_full_form_when_user_doesnt_have_perms(self):
        a_user_without_perms = UserFactory()
        self.client.force_login(a_user_without_perms)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_create_full_get_form(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "learning_unit/simple/creation.html")
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertIsInstance(response.context['learning_unit_form'], LearningUnitModelForm)

    @mock.patch('base.forms.learning_unit.learning_unit_create_2.FullForm.is_valid', side_effect=lambda *args: False)
    def test_create_full_when_invalid_form_no_redirection(self, mock_is_valid):
        response = self.client.post(self.url, data={})
        self.assertTemplateUsed(response, "learning_unit/simple/creation.html")
        self.assertEqual(response.status_code, HttpResponse.status_code)

    @mock.patch('base.forms.learning_unit.learning_unit_create_2.FullForm.is_valid', side_effect=lambda *args: True)
    @mock.patch('base.forms.learning_unit.learning_unit_create_2.FullForm.save')
    @mock.patch('base.forms.learning_unit.learning_unit_postponement.LearningUnitPostponementForm.__init__',
                side_effect=lambda *args, **kwargs: None)
    @mock.patch('base.forms.learning_unit.learning_unit_postponement.LearningUnitPostponementForm.is_valid',
                side_effect=lambda *args: True)
    @mock.patch('base.forms.learning_unit.learning_unit_postponement.LearningUnitPostponementForm.save')
    def test_create_full_success_with_redirection(self, mock_postponement_save, mock_postponement_is_valid,
                                                  mock_postponement_init, mock_full_form_save, mock_full_form_valid):
        a_full_learning_unit_year = LearningUnitYearFactory(
            academic_year=self.current_academic_year,
            learning_container_year__academic_year=self.current_academic_year,
            subtype=learning_unit_year_subtypes.FULL
        )
        mock_postponement_save.return_value = [a_full_learning_unit_year]
        mock_full_form_save.return_value = a_full_learning_unit_year
        response = self.client.post(self.url, data={})
        url_to_redirect = reverse("learning_unit", kwargs={'learning_unit_year_id': a_full_learning_unit_year.id})
        self.assertRedirects(response, url_to_redirect)

    def test_when_valid_form_data(self):
        today = datetime.date.today()
        academic_year_1 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 1),
                                                    end_date=today.replace(year=today.year + 2),
                                                    year=today.year + 1)
        academic_year_2 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 2),
                                                    end_date=today.replace(year=today.year + 3),
                                                    year=today.year + 2)
        academic_year_3 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 3),
                                                    end_date=today.replace(year=today.year + 4),
                                                    year=today.year + 3)
        academic_year_4 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 4),
                                                    end_date=today.replace(year=today.year + 5),
                                                    year=today.year + 4)
        academic_year_5 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 5),
                                                    end_date=today.replace(year=today.year + 6),
                                                    year=today.year + 5)
        academic_year_6 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 6),
                                                    end_date=today.replace(year=today.year + 7),
                                                    year=today.year + 6)
        current_academic_year = AcademicYearFactory(start_date=today,
                                                    end_date=today.replace(year=today.year + 1),
                                                    year=today.year)
        super(AcademicYear, academic_year_1).save()
        super(AcademicYear, academic_year_2).save()
        super(AcademicYear, academic_year_3).save()
        super(AcademicYear, academic_year_4).save()
        super(AcademicYear, academic_year_5).save()
        super(AcademicYear, academic_year_6).save()

        organization = OrganizationFactory(type=organization_type.MAIN)
        campus = CampusFactory(organization=organization)
        entity = EntityFactory(organization=organization)
        entity_version = EntityVersionFactory(entity=entity, entity_type=entity_type.SCHOOL, start_date=today,
                                              end_date=today.replace(year=today.year + 1))
        language = LanguageFactory()

        form_data = {
            "acronym_0": "L",
            "acronym_1": "TAU2000",
            "container_type": learning_container_year_types.COURSE,
            "academic_year": current_academic_year.id,
            "status": True,
            "periodicity": learning_unit_year_periodicity.ANNUAL,
            "credits": "5",
            "campus": campus.id,
            "internship_subtype": internship_subtypes.TEACHING_INTERNSHIP,
            "title": "LAW",
            "title_english": "LAW",
            "requirement_entity-entity": entity_version.id,
            "subtype": learning_unit_year_subtypes.FULL,
            "language": language.pk,
            "session": learning_unit_year_session.SESSION_P23,
            "faculty_remark": "faculty remark",
            "other_remark": "other remark",

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

        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)


@override_flag('learning_unit_create', active=True)
class LearningUnitViewCreatePartimTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()

        AcademicCalendarFactory(
            data_year=cls.current_academic_year,
            start_date=datetime.datetime(cls.current_academic_year.year - 2, 9, 15),
            end_date=datetime.datetime(cls.current_academic_year.year + 1, 9, 14),
            reference=LEARNING_UNIT_EDITION_FACULTY_MANAGERS
        )

        cls.learning_unit_year_full = LearningUnitYearFactory(
            academic_year=cls.current_academic_year,
            learning_container_year__academic_year=cls.current_academic_year,
            subtype=learning_unit_year_subtypes.FULL
        )
        cls.url = reverse(create_partim_form, kwargs={'learning_unit_year_id': cls.learning_unit_year_full.id})
        faculty_manager = FacultyManagerFactory("can_access_learningunit", "can_create_learningunit")
        cls.user = faculty_manager.user
        cls.access_denied = "access_denied.html"

    def setUp(self):
        self.client.force_login(self.user)

    def test_create_partim_form_when_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_create_partim_form_when_user_doesnt_have_perms(self):
        a_user_without_perms = UserFactory()
        self.client.force_login(a_user_without_perms)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, self.access_denied)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_create_partim_form_invalid_http_methods(self):
        response = self.client.delete(self.url)
        self.assertTemplateUsed(response, "method_not_allowed.html")
        self.assertEqual(response.status_code, HttpResponseNotAllowed.status_code)

    @mock.patch('base.views.learning_units.perms.business_perms.is_person_linked_to_entity_in_charge_of_learning_unit',
                side_effect=lambda *args: False)
    def test_create_partim_when_user_not_linked_to_entity_charge(self, mock_is_pers_linked_to_entity_charge):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, self.access_denied)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    @mock.patch('base.views.learning_units.perms.business_perms.is_person_linked_to_entity_in_charge_of_learning_unit',
                side_effect=lambda *args: True)
    def test_create_partim_get_form(self, mock_is_pers_linked_to_entity_charge):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "learning_unit/simple/creation_partim.html")
        self.assertEqual(response.status_code, HttpResponse.status_code)

    @mock.patch('base.views.learning_units.perms.business_perms.is_person_linked_to_entity_in_charge_of_learning_unit',
                side_effect=lambda *args: True)
    @mock.patch('base.forms.learning_unit.learning_unit_partim.PartimForm.is_valid', side_effect=lambda *args: False)
    def test_create_partim_when_invalid_form_no_redirection(self, mock_is_valid, mock_is_pers_linked_to_entity_charge):
        response = self.client.post(self.url, data={})
        self.assertTemplateUsed(response, "learning_unit/simple/creation_partim.html")
        self.assertEqual(response.status_code, HttpResponse.status_code)

    @mock.patch('base.views.learning_units.perms.business_perms.is_person_linked_to_entity_in_charge_of_learning_unit',
                side_effect=lambda *args: True)
    @mock.patch('base.forms.learning_unit.learning_unit_partim.PartimForm.is_valid', side_effect=lambda *args: True)
    @mock.patch('base.forms.learning_unit.learning_unit_partim.PartimForm.save')
    @mock.patch('base.forms.learning_unit.learning_unit_postponement.LearningUnitPostponementForm.__init__',
                side_effect=lambda *args, **kwargs: None)
    @mock.patch('base.forms.learning_unit.learning_unit_postponement.LearningUnitPostponementForm.is_valid',
                side_effect=lambda *args: True)
    @mock.patch('base.forms.learning_unit.learning_unit_postponement.LearningUnitPostponementForm.save')
    def test_create_partim_success_with_redirection(self, mock_postponement_save, mock_postponement_is_valid,
                                                    mock_postponement_init, mock_partim_form_save,
                                                    mock_partim_form_is_valid, mock_is_pers_linked_to_entity_charge):
        learning_container_year = LearningContainerYearFactory(academic_year=self.current_academic_year)
        LearningUnitYearFactory(
            academic_year=self.current_academic_year,
            learning_container_year=learning_container_year,
            subtype=learning_unit_year_subtypes.FULL
        )
        a_partim_learning_unit_year = LearningUnitYearFactory(
            academic_year=self.current_academic_year,
            learning_container_year=learning_container_year,
            subtype=learning_unit_year_subtypes.PARTIM
        )
        mock_postponement_save.return_value = [a_partim_learning_unit_year]
        mock_partim_form_save.return_value = a_partim_learning_unit_year
        response = self.client.post(self.url, data={})
        url_to_redirect = reverse("learning_unit", kwargs={'learning_unit_year_id': a_partim_learning_unit_year.id})
        self.assertRedirects(response, url_to_redirect)


# TODO Split this test based on functionality
class LearningUnitViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organization = OrganizationFactory(type=organization_type.MAIN)
        cls.country = CountryFactory()

        cls.entities = EntityFactory.create_batch(3, country=cls.country, organization=cls.organization)

        today = datetime.date.today()
        cls.current_academic_year, *cls.academic_years = AcademicYearFactory.produce_in_future(quantity=8)

        AcademicCalendarFactory(
            data_year=cls.current_academic_year,
            start_date=datetime.datetime(cls.current_academic_year.year - 2, 9, 15),
            end_date=datetime.datetime(cls.current_academic_year.year + 1, 9, 14),
            reference=LEARNING_UNIT_EDITION_FACULTY_MANAGERS
        )

        cls.learning_unit = LearningUnitFactory(start_year=cls.current_academic_year)

        cls.learning_container_yr = LearningContainerYearFactory(
            academic_year=cls.current_academic_year,
            requirement_entity=cls.entities[0],
        )
        cls.luy = LearningUnitYearFactory(
            academic_year=cls.current_academic_year,
            learning_container_year=cls.learning_container_yr,
            learning_unit=cls.learning_unit
        )
        cls.learning_component_yr = LearningComponentYearFactory(learning_unit_year=cls.luy,
                                                                 hourly_volume_total_annual=10,
                                                                 hourly_volume_partial_q1=5,
                                                                 hourly_volume_partial_q2=5)

        cls.entity_version = EntityVersionFactory(acronym="1 acronym", entity=cls.entities[0],
                                                  entity_type=entity_type.SCHOOL,
                                                  start_date=today - datetime.timedelta(days=1),
                                                  end_date=today.replace(year=today.year + 1))
        cls.entity_version_2 = EntityVersionFactory(acronym="2 acronym", entity=cls.entities[1],
                                                    entity_type=entity_type.INSTITUTE,
                                                    start_date=today - datetime.timedelta(days=20),
                                                    end_date=today.replace(year=today.year + 1))
        cls.entity_version_3 = EntityVersionFactory(acronym="3 acronym", entity=cls.entities[2],
                                                    entity_type=entity_type.FACULTY,
                                                    start_date=today - datetime.timedelta(days=50),
                                                    end_date=today.replace(year=today.year + 1))

        cls.campus = CampusFactory(organization=cls.organization, is_administration=True)
        cls.language = LanguageFactory(code='FR')
        cls.a_superuser = SuperUserFactory()
        cls.person = PersonFactory(user=cls.a_superuser)

        for entity in cls.entities:
            PersonEntityFactory(person=cls.person, entity=entity)

    def setUp(self):
        self.client.force_login(self.a_superuser)

    def test_entity_requirement_autocomplete(self):
        self.client.force_login(self.person.user)
        url = reverse("entity_requirement_autocomplete", args=[])
        response = self.client.get(
            url, data={}
        )
        self.assertEqual(response.status_code, 200)
        json_response = str(response.content, encoding='utf8')
        results = json.loads(json_response)['results']
        self.assertEqual(results[0]['text'], self.entity_version.verbose_title)
        self.assertEqual(results[1]['text'], self.entity_version_3.verbose_title)

    def test_entity_requirement_autocomplete_with_q(self):
        self.client.force_login(self.person.user)
        url = reverse("entity_requirement_autocomplete", args=[])
        response = self.client.get(url, data={"q": "1"})
        self.assertEqual(response.status_code, 200)
        json_response = str(response.content, encoding='utf8')
        results = json.loads(json_response)['results']
        self.assertEqual(results[0]['text'], self.entity_version.verbose_title)

    def test_entity_autocomplete(self):
        self.client.force_login(self.person.user)
        url = reverse("entity_autocomplete", args=[])
        response = self.client.get(
            url, data={}
        )
        self.assertEqual(response.status_code, 200)
        json_response = str(response.content, encoding='utf8')
        results = json.loads(json_response)['results']
        self.assertEqual(results[0]['text'], self.entity_version.verbose_title)
        self.assertEqual(results[1]['text'], self.entity_version_3.verbose_title)

    def test_entity_autocomplete_with_q(self):
        self.client.force_login(self.person.user)
        url = reverse("entity_autocomplete", args=[])
        response = self.client.get(url, data={"q": "1"})
        self.assertEqual(response.status_code, 200)
        json_response = str(response.content, encoding='utf8')
        results = json.loads(json_response)['results']
        self.assertEqual(results[0]['text'], self.entity_version.verbose_title)

    def test_learning_units_search(self):
        response = self.client.get(reverse('learning_units'))

        context = response.context
        self.assertTemplateUsed(response, 'learning_unit/search/base.html')
        self.assertEqual(context['current_academic_year'], self.current_academic_year)
        self.assertEqual(context['learning_units_count'], 0)

    def test_learning_units_search_with_acronym_filtering(self):
        self._prepare_context_learning_units_search()

        filter_data = {
            'academic_year': self.current_academic_year.id,
            'acronym': 'LBIR',
            'status': True
        }
        response = self.client.get(reverse('learning_units'), data=filter_data)

        self.assertTemplateUsed(response, 'learning_unit/search/base.html')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_learning_units_search_with_type_filtering(self):
        lcy_type = random.choice(learning_container_year_types.LearningContainerYearType.get_names())
        self._prepare_context_learning_units_search()
        filter_data = {
            'container_type': lcy_type,
        }
        response = self.client.get(reverse('learning_units'), data=filter_data)

        self.assertTemplateUsed(response, 'learning_unit/search/base.html')
        expected_count = LearningUnitYear.objects.filter(learning_container_year__container_type=lcy_type).count()
        self.assertEqual(len(response.context['page_obj']), expected_count)

    def test_learning_units_search_by_acronym_with_valid_regex(self):
        self._prepare_context_learning_units_search()
        filter_data = {
            'academic_year': self.current_academic_year.id,
            'acronym': '^DRT.+A'
        }
        response = self.client.get(reverse('learning_units'), data=filter_data)

        self.assertTemplateUsed(response, 'learning_unit/search/base.html')
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_learning_units_search_by_acronym_with_invalid_regex(self):
        self._prepare_context_learning_units_search()

        filter_data = {
            'academic_year': self.current_academic_year.id,
            'acronym': '^LB(+)2+',
            'status': active_status.ACTIVE
        }
        response = self.client.get(reverse('learning_units'), data=filter_data)

        self.assertTemplateUsed(response, 'learning_unit/search/base.html')

    def test_learning_units_search_with_requirement_entity(self):
        self._prepare_context_learning_units_search()

        filter_data = {
            'academic_year': self.current_academic_year.id,
            'requirement_entity': 'ENVI'
        }
        response = self.client.get(reverse('learning_units'), data=filter_data)

        self.assertTemplateUsed(response, 'learning_unit/search/base.html')
        self.assertEqual(response.context['learning_units_count'], 1)

    def test_learning_units_search_with_requirement_entity_and_subord(self):
        self._prepare_context_learning_units_search()
        filter_data = {
            'academic_year': self.current_academic_year.id,
            'requirement_entity': 'AGRO',
            'with_entity_subordinated': True
        }
        response = self.client.get(reverse('learning_units'), data=filter_data)
        self.assertTemplateUsed(response, 'learning_unit/search/base.html')

        self.assertEqual(response.context['learning_units_count'], 6)

    def test_learning_units_search_with_allocation_entity(self):
        self._prepare_context_learning_units_search()
        filter_data = {
            'academic_year': self.current_academic_year.id,
            'allocation_entity': 'AGES'
        }
        response = self.client.get(reverse('learning_units'), data=filter_data)

        self.assertTemplateUsed(response, 'learning_unit/search/base.html')
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_learning_units_search_with_requirement_and_allocation_entity(self):
        self._prepare_context_learning_units_search()
        filter_data = {
            'academic_year': self.current_academic_year.id,
            'requirement_entity': 'ENVI',
            'allocation_entity': 'AGES'
        }
        response = self.client.get(reverse('learning_units'), data=filter_data)

        self.assertTemplateUsed(response, 'learning_unit/search/base.html')
        self.assertEqual(response.context['learning_units_count'], 1)

    def test_learning_units_search_with_service_course_no_result(self):
        filter_data = {
            'academic_year': self.current_academic_year.id,
            'requirement_entity': 'AGRO',
            'with_entity_subordinated': True
        }
        number_of_results = 0
        self.service_course_search(filter_data, number_of_results)

    def test_learning_units_search_with_service_course_without_entity_subordinated(self):
        filter_data = {
            'academic_year': self.current_academic_year.id,
            'requirement_entity': 'ELOG',
            'with_entity_subordinated': False
        }
        number_of_results = 1
        self.service_course_search(filter_data, number_of_results)

    def test_learning_units_search_with_service_course_with_entity_subordinated(self):
        filter_data = {
            'academic_year': self.current_academic_year.id,
            'requirement_entity': 'PSP',
            'with_entity_subordinated': True
        }

        number_of_results = 1
        self.service_course_search(filter_data, number_of_results)

    def test_lu_search_with_service_course_with_entity_subordinated_requirement_and_wrong_allocation(self):
        filter_data = {
            'academic_year': self.current_academic_year.id,
            'requirement_entity': 'PSP',
            'allocation_entity': 'ELOG',
            'with_entity_subordinated': True
        }
        number_of_results = 0
        self.service_course_search(filter_data, number_of_results)

    def service_course_search(self, filter_data, number_of_results):
        self._prepare_context_learning_units_search()
        response = self.client.get(reverse("learning_units_service_course"), data=filter_data)

        self.assertTemplateUsed(response, 'learning_unit/search/base.html')
        self.assertEqual(response.context['learning_units_count'], number_of_results)

    def test_learning_units_search_quadrimester(self):
        self._prepare_context_learning_units_search()
        self.luy_LBIR1100C.quadrimester = quadrimesters.LearningUnitYearQuadrimester.Q1and2.name
        self.luy_LBIR1100C.save()
        filter_data = {
            'academic_year': self.current_academic_year.id,
            'quadrimester': quadrimesters.LearningUnitYearQuadrimester.Q1and2.name,
            'acronym': 'LBIR1100C',
        }
        response = self.client.get(reverse('learning_units'), data=filter_data)

        self.assertTemplateUsed(response, 'learning_unit/search/base.html')
        self.assertEqual(response.context['learning_units_count'], 1)

    def test_get_components_with_classes(self):
        l_container = LearningContainerFactory()
        l_container_year = LearningContainerYearFactory(academic_year=self.current_academic_year,
                                                        common_title="LC-98998", learning_container=l_container)
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=l_container_year)
        l_component_year = LearningComponentYearFactory(learning_unit_year=learning_unit_year)
        LearningClassYearFactory(learning_component_year=l_component_year)
        LearningClassYearFactory(learning_component_year=l_component_year)

        components_dict = learning_unit_business.get_same_container_year_components(learning_unit_year)
        self.assertEqual(len(components_dict.get('components')), 1)
        self.assertEqual(len(components_dict.get('components')[0]['learning_component_year'].classes), 2)

    def test_learning_unit_formation(self):
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=self.learning_container_yr)
        educ_group_type_matching_filters = EducationGroupTypeFactory(category=education_group_categories.TRAINING)
        group_element1 = GroupElementYearFactory(
            child_leaf=learning_unit_year,
            child_branch=None,
            parent=EducationGroupYearFactory(partial_acronym='LMATH600R', academic_year=self.current_academic_year,
                                             education_group_type=educ_group_type_matching_filters))
        group_element2 = GroupElementYearFactory(
            child_leaf=learning_unit_year,
            child_branch=None,
            parent=EducationGroupYearFactory(partial_acronym='LBIOL601R', academic_year=self.current_academic_year,
                                             education_group_type=educ_group_type_matching_filters))
        group_element3 = GroupElementYearFactory(
            child_leaf=learning_unit_year,
            child_branch=None,
            parent=EducationGroupYearFactory(partial_acronym='TMATH600R', academic_year=self.current_academic_year,
                                             education_group_type=educ_group_type_matching_filters))

        response = self.client.get(reverse('learning_unit_formations', args=[learning_unit_year.id]))
        context = response.context

        self.assertTemplateUsed(response, 'learning_unit/formations.html')
        self.assertEqual(context['current_academic_year'], self.current_academic_year)
        self.assertEqual(context['learning_unit_year'], learning_unit_year)
        expected_order = [group_element2, group_element1, group_element3]
        self._assert_group_elements_ordered_by_partial_acronym(context, expected_order)
        self.assertIn('root_formations', context)

    def _assert_group_elements_ordered_by_partial_acronym(self, context, expected_order):
        self.assertListEqual(list(context['group_elements_years']), expected_order)

    def test_learning_unit_usage_with_complete_LU(self):
        learning_container_yr = LearningContainerYearFactory(academic_year=self.current_academic_year,
                                                             acronym='LBIOL')

        learning_unit_yr_1 = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     acronym='LBIOL', quadrimester='Q1&2',
                                                     learning_container_year=learning_container_yr)

        learning_component_yr = LearningComponentYearFactory(learning_unit_year=learning_unit_yr_1)

        result = learning_unit_business._learning_unit_usage(learning_component_yr.learning_unit_year)
        self.assertEqual(result, 'LBIOL (Q1&2)')

    def _prepare_context_learning_units_search(self):
        # Create a structure [Entity / Entity version]
        ssh_entity = EntityFactory(country=self.country)
        ssh_entity_v = EntityVersionFactory(acronym="SSH", end_date=None, entity=ssh_entity)

        agro_entity = EntityFactory(country=self.country)
        envi_entity = EntityFactory(country=self.country)
        ages_entity = EntityFactory(country=self.country)
        psp_entity = EntityFactory(country=self.country)
        elog_entity = EntityFactory(country=self.country)
        logo_entity = EntityFactory(country=self.country)
        fsm_entity = EntityFactory(country=self.country)
        agro_entity_v = EntityVersionFactory(entity=agro_entity, parent=ssh_entity_v.entity, acronym="AGRO",
                                             end_date=None)
        envi_entity_v = EntityVersionFactory(entity=envi_entity, parent=agro_entity_v.entity, acronym="ENVI",
                                             end_date=None)
        ages_entity_v = EntityVersionFactory(entity=ages_entity, parent=agro_entity_v.entity, acronym="AGES",
                                             end_date=None)
        psp_entity_v = EntityVersionFactory(entity=psp_entity, parent=ssh_entity_v.entity, acronym="PSP",
                                            end_date=None, entity_type=entity_type.FACULTY)
        fsm_entity_v = EntityVersionFactory(entity=fsm_entity, parent=ssh_entity_v.entity, acronym="FSM",
                                            end_date=None, entity_type=entity_type.FACULTY)
        elog_entity_v = EntityVersionFactory(entity=elog_entity, parent=psp_entity_v.entity, acronym="ELOG",
                                             end_date=None, entity_type=entity_type.INSTITUTE)
        logo_entity_v = EntityVersionFactory(entity=logo_entity, parent=fsm_entity_v.entity, acronym="LOGO",
                                             end_date=None, entity_type=entity_type.INSTITUTE)
        espo_entity = EntityFactory(country=self.country)
        drt_entity = EntityFactory(country=self.country)
        espo_entity_v = EntityVersionFactory(entity=espo_entity, parent=ssh_entity_v.entity, acronym="ESPO",
                                             end_date=None)
        drt_entity_v = EntityVersionFactory(entity=drt_entity, parent=ssh_entity_v.entity, acronym="DRT",
                                            end_date=None)

        # Create UE and put entity charge [AGRO]
        l_container_yr = LearningContainerYearFactory(
            acronym="LBIR1100",
            academic_year=self.current_academic_year,
            container_type=learning_container_year_types.COURSE,
            requirement_entity=agro_entity_v.entity,
        )
        LearningUnitYearFactory(acronym="LBIR1100", learning_container_year=l_container_yr,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)
        LearningUnitYearFactory(acronym="LBIR1100A", learning_container_year=l_container_yr,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.PARTIM)
        LearningUnitYearFactory(acronym="LBIR1100B", learning_container_year=l_container_yr,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.PARTIM)
        self.luy_LBIR1100C = LearningUnitYearFactory(
            acronym="LBIR1100C", learning_container_year=l_container_yr, academic_year=self.current_academic_year,
            subtype=learning_unit_year_subtypes.PARTIM, status=False)

        # Create another UE and put entity charge [ENV]
        l_container_yr_2 = LearningContainerYearFactory(
            acronym="CHIM1200",
            academic_year=self.current_academic_year,
            container_type=learning_container_year_types.COURSE,
            requirement_entity=envi_entity_v.entity,
            allocation_entity=ages_entity_v.entity,
        )
        LearningUnitYearFactory(acronym="CHIM1200", learning_container_year=l_container_yr_2,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)

        # Create another UE and put entity charge [DRT]
        l_container_yr_3 = LearningContainerYearFactory(
            acronym="DRT1500",
            academic_year=self.current_academic_year,
            container_type=learning_container_year_types.COURSE,
            requirement_entity=drt_entity_v.entity,
        )
        LearningUnitYearFactory(acronym="DRT1500", learning_container_year=l_container_yr_3,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)
        LearningUnitYearFactory(acronym="DRT1500A", learning_container_year=l_container_yr_3,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.PARTIM)

        # Create another UE and put entity charge [ESPO]
        l_container_yr_4 = LearningContainerYearFactory(
            acronym="ESPO1500",
            academic_year=self.current_academic_year,
            container_type=learning_container_year_types.DISSERTATION,
            requirement_entity=espo_entity_v.entity,
        )
        LearningUnitYearFactory(acronym="ESPO1500", learning_container_year=l_container_yr_4,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)

        # Create another UE and put entity charge [AGES]
        l_container_yr_4 = LearningContainerYearFactory(
            acronym="AGES1500",
            academic_year=self.current_academic_year,
            container_type=learning_container_year_types.MASTER_THESIS,
            requirement_entity=ages_entity_v.entity,
        )
        LearningUnitYearFactory(acronym="AGES1500", learning_container_year=l_container_yr_4,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)

        # Create another UE and put entity charge [ELOG] and allocation charge [LOGO]
        l_container_yr_5 = LearningContainerYearFactory(
            acronym="LOGO1200",
            academic_year=self.current_academic_year,
            container_type=learning_container_year_types.COURSE,
            requirement_entity=elog_entity_v.entity,
            allocation_entity=logo_entity_v.entity,
        )
        LearningUnitYearFactory(acronym="LOGO1200", learning_container_year=l_container_yr_5,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)

    def get_base_form_data(self):
        data = self.get_common_data()
        data.update(self.get_learning_unit_data())
        data['internship_subtype'] = internship_subtypes.TEACHING_INTERNSHIP
        return data

    def get_common_data(self):
        return {
            "container_type": learning_container_year_types.COURSE,
            "academic_year": self.current_academic_year.id,
            "status": True,
            "periodicity": learning_unit_year_periodicity.ANNUAL,
            "credits": "5",
            "campus": self.campus.id,
            "specific_title": "Specific UE title",
            "specific_title_english": "Specific English UUE title",
            "requirement_entity-entity": self.entity_version.id,
            "allocation_entity-entity": self.entity_version.id,
            "language": self.language.pk,
            "session": learning_unit_year_session.SESSION_P23,
            "faculty_remark": "faculty remark",
            "other_remark": "other remark",
        }

    def get_learning_unit_data(self):
        return {'acronym_0': 'L',
                'acronym_1': 'TAU2000',
                "subtype": learning_unit_year_subtypes.FULL}

    def get_partim_data(self, original_learning_unit_year):
        return {
            'acronym_0': original_learning_unit_year.acronym[1],
            'acronym_1': original_learning_unit_year.acronym[1:],
            'acronym_2': factory.fuzzy.FuzzyText(length=1).fuzz(),
            "subtype": learning_unit_year_subtypes.PARTIM
        }

    def get_valid_data(self):
        return self.get_base_form_data()

    def test_get_username_with_no_person(self):
        a_username = 'dupontm'
        a_user = UserFactory(username=a_username)
        self.assertEqual(base.business.xls.get_name_or_username(a_user), a_username)

    def test_get_username_with_person(self):
        a_user = UserFactory(username='dupontm')
        last_name = 'dupont'
        first_name = 'marcel'
        self.person = PersonFactory(user=a_user, last_name=last_name, first_name=first_name)
        self.assertEqual(base.business.xls.get_name_or_username(a_user),
                         '{}, {}'.format(last_name, first_name))

    def test_prepare_xls_content_no_data(self):
        self.assertEqual(base.business.learning_unit_xls.prepare_ue_xls_content([]), [])

    @override_settings(LANGUAGES=[('fr-be', 'French'), ('en', 'English'), ])
    def test_find_inexisting_language_in_settings(self):
        wrong_language_code = 'pt'
        self.assertIsNone(reference.models.language.find_language_in_settings(wrong_language_code))

    @override_settings(LANGUAGES=[('fr-be', 'French'), ('en', 'English'), ])
    def test_find_language_in_settings(self):
        existing_language_code = 'en'
        self.assertEqual(reference.models.language.find_language_in_settings(existing_language_code), ('en', 'English'))

    def test_learning_unit_pedagogy(self):
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=self.learning_container_yr,
                                                     subtype=learning_unit_year_subtypes.FULL)
        header = {'HTTP_REFERER': SEARCH_URL_PART}
        response = self.client.get(reverse(learning_unit_pedagogy, args=[learning_unit_year.pk]), **header)

        self.assertTemplateUsed(response, 'learning_unit/pedagogy.html')
        self.assertEqual(self.client.session['search_url'], SEARCH_URL_PART)

    def test_learning_unit_specification(self):
        learning_unit_year = LearningUnitYearFactory()
        fr = LanguageFactory(code='FR')
        en = LanguageFactory(code='EN')
        learning_unit_achievements_fr = LearningAchievementFactory(language=fr, learning_unit_year=learning_unit_year)
        learning_unit_achievements_en = LearningAchievementFactory(language=en, learning_unit_year=learning_unit_year)

        response = self.client.get(reverse(learning_unit_specifications, args=[learning_unit_year.pk]))

        self.assertTemplateUsed(response, 'learning_unit/specifications.html')
        self.assertIsInstance(response.context['form_french'], LearningUnitSpecificationsForm)
        self.assertIsInstance(response.context['form_english'], LearningUnitSpecificationsForm)
        self.assertCountEqual(response.context['achievements_FR'], [learning_unit_achievements_fr])
        self.assertCountEqual(response.context['achievements_EN'], [learning_unit_achievements_en])
        self.assertCountEqual(
            response.context['achievements'],
            list(itertools.zip_longest([learning_unit_achievements_fr], [learning_unit_achievements_en]))
        )

    def test_learning_unit_specifications_edit(self):
        a_label = 'label'
        learning_unit_year = LearningUnitYearFactory()
        text_label_lu = TextLabelFactory(order=1, label=a_label, entity=entity_name.LEARNING_UNIT_YEAR)
        TranslatedTextFactory(text_label=text_label_lu, entity=entity_name.LEARNING_UNIT_YEAR)

        response = self.client.get(
            reverse(learning_unit_specifications_edit,
                    args=[learning_unit_year.id]), data={
                'label': a_label,
                'language': 'en'
            })

        self.assertTemplateUsed(response, 'learning_unit/specifications_edit.html')
        self.assertIsInstance(response.context['form'], LearningUnitSpecificationsEditForm)

    def test_learning_unit_specifications_save(self):
        learning_unit_year = LearningUnitYearFactory()
        response = self.client.post(
            reverse('learning_unit_specifications_edit', kwargs={'learning_unit_year_id': learning_unit_year.id}),
            data={'postpone': 0}
        )
        self.assertEqual(response.status_code, 200)

    def test_learning_unit_specifications_save_with_postponement_without_proposal(self):
        year_range = 5
        academic_years = [AcademicYearFactory(year=get_current_year() + i) for i in range(0, year_range)]
        learning_unit_years = self._generate_learning_unit_years(academic_years)
        msg = self._test_learning_unit_specifications_save_with_postponement(learning_unit_years)
        expected_message = "{} {}.".format(
            _("The learning unit has been updated"), _("and postponed until %(year)s") % {
                'year': academic_years[-1]
            }
        )
        self.assertEqual(msg[0].get('message'), expected_message)
        self.assertEqual(msg[0].get('level'), messages.SUCCESS)

    def test_learning_unit_specifications_save_with_postponement_and_proposal_on_same_year(self):
        year_range = 5
        academic_years = [AcademicYearFactory(year=get_current_year() + i) for i in range(0, year_range)]
        learning_unit_years = self._generate_learning_unit_years(academic_years)
        proposal = ProposalLearningUnitFactory(learning_unit_year=learning_unit_years[0])
        msg = self._test_learning_unit_specifications_save_with_postponement(learning_unit_years)
        expected_message = "{}. {}.".format(
            _("The learning unit has been updated"),
            _("The learning unit is in proposal, the report from %(proposal_year)s will be done at consolidation") % {
                'proposal_year': proposal.learning_unit_year.academic_year
            }
        )
        self.assertEqual(msg[0].get('message'), expected_message)
        self.assertEqual(msg[0].get('level'), messages.SUCCESS)

    def test_learning_unit_specifications_save_with_postponement_and_proposal_on_future_year(self):
        year_range = 5
        academic_years = [AcademicYearFactory(year=get_current_year() + i) for i in range(0, year_range)]
        learning_unit_years = self._generate_learning_unit_years(academic_years)
        proposal = ProposalLearningUnitFactory(learning_unit_year=learning_unit_years[1])
        msg = self._test_learning_unit_specifications_save_with_postponement(learning_unit_years)
        expected_message = _("The learning unit has been updated (the report has not been done from %(year)s because "
                             "the learning unit is in proposal).") % {
            'year': proposal.learning_unit_year.academic_year
        }
        self.assertEqual(msg[0].get('message'), expected_message)
        self.assertEqual(msg[0].get('level'), messages.SUCCESS)

    def test_learning_unit_specifications_save_without_postponement_and_proposal_on_future_year(self):
        year_range = 5
        academic_years = [AcademicYearFactory(year=get_current_year() + i) for i in range(0, year_range)]
        learning_unit_years = self._generate_learning_unit_years(academic_years)
        ProposalLearningUnitFactory(learning_unit_year=learning_unit_years[1])
        msg = self._test_learning_unit_specifications_save_with_postponement(learning_unit_years, postpone=False)
        expected_message = "{} ({}).".format(
            _("The learning unit has been updated"),
            _("without postponement")
        )
        self.assertEqual(msg[0].get('message'), expected_message)
        self.assertEqual(msg[0].get('level'), messages.SUCCESS)

    def _generate_learning_unit_years(self, academic_years):
        learning_unit = LearningUnitFactory(start_year=academic_years[0], end_year=academic_years[-1])
        learning_unit_years = [LearningUnitYearFactory(
            academic_year=ac,
            learning_unit=learning_unit,
            acronym=learning_unit.acronym,
            subtype=FULL,
        ) for ac in academic_years]
        return learning_unit_years

    def _test_learning_unit_specifications_save_with_postponement(self, learning_unit_years, postpone=True):
        # delete last learning unit year to ensure luy is not created
        learning_unit_years.pop().delete()
        label = TextLabelFactory(label='label', entity=entity_name.LEARNING_UNIT_YEAR)
        for language in ['fr-be', 'en']:
            TranslatedTextLabelFactory(text_label=label, language=language)
        trans_fr_be = [TranslatedTextFactory(
            entity=entity_name.LEARNING_UNIT_YEAR,
            reference=luy.id,
            language='fr-be',
            text_label=label
        ) for luy in learning_unit_years]
        trans_en = [TranslatedTextFactory(
            entity=entity_name.LEARNING_UNIT_YEAR,
            reference=luy.id,
            language='en',
            text_label=label
        ) for luy in learning_unit_years]
        response = self.client.post(
            reverse('learning_unit_specifications_edit', kwargs={'learning_unit_year_id': learning_unit_years[0].id}),
            data={
                'trans_text_fr': 'textFR',
                'trans_text_en': 'textEN',
                'postpone': 1 if postpone else 0,
                'cms_fr_id': trans_fr_be[0].id,
                'cms_en_id': trans_en[0].id,
            }
        )
        self.assertEqual(response.status_code, 200)
        if postpone:
            for translated_text in TranslatedText.objects.filter(language='fr-be'):
                self.assertEqual(translated_text.text, 'textFR')
            for translated_text in TranslatedText.objects.filter(language='en'):
                self.assertEqual(translated_text.text, 'textEN')
        msg = get_messages_from_response(response)
        return msg

    def test_learning_unit(self):
        learning_unit_year = LearningUnitYearFactory()
        education_group_year_1 = EducationGroupYearFactory()
        education_group_year_2 = EducationGroupYearFactory()
        LearningUnitEnrollmentFactory(offer_enrollment__education_group_year=education_group_year_1,
                                      learning_unit_year=learning_unit_year)
        LearningUnitEnrollmentFactory(offer_enrollment__education_group_year=education_group_year_1,
                                      learning_unit_year=learning_unit_year)
        LearningUnitEnrollmentFactory(offer_enrollment__education_group_year=education_group_year_2,
                                      learning_unit_year=learning_unit_year)
        LearningUnitEnrollmentFactory(offer_enrollment__education_group_year=education_group_year_2,
                                      learning_unit_year=learning_unit_year)
        response = self.client.get(reverse(learning_unit_formations, args=[learning_unit_year.pk]))
        self.assertTemplateUsed(response, 'learning_unit/formations.html')
        # Count Education Group Year link to Learning Unit Year
        self.assertEqual(len(response.context["root_formations"]), 2)
        # Count Student link to Formation
        self.assertEqual(response.context["total_formation_enrollments"], 4)


class TestCreateXls(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.learning_unit_year = LearningUnitYearFactory(
            learning_container_year__requirement_entity=EntityFactory(),
            learning_container_year__allocation_entity=EntityFactory(),
            acronym="LOSI1452"
        )

        cls.user = UserFactory()

    @mock.patch("osis_common.document.xls_build.generate_xls")
    def test_generate_xls_data_with_no_data(self, mock_generate_xls):
        create_xls(self.user, [], None)
        expected_argument = _generate_xls_build_parameter([], self.user)
        mock_generate_xls.assert_called_with(expected_argument, None)

    @mock.patch("osis_common.document.xls_build.generate_xls")
    def test_generate_xls_data_with_a_learning_unit(self, mock_generate_xls):
        learning_unit_filter = LearningUnitFilter({"acronym": self.learning_unit_year.acronym})
        self.assertTrue(learning_unit_filter.is_valid())
        found_learning_units = learning_unit_filter.qs
        create_xls(self.user, found_learning_units, None)
        xls_data = [[self.learning_unit_year.academic_year.name, self.learning_unit_year.acronym,
                     self.learning_unit_year.complete_title,
                     xls_build.translate(self.learning_unit_year.learning_container_year.container_type),
                     xls_build.translate(self.learning_unit_year.subtype),
                     self.learning_unit_year.learning_container_year.allocation_entity,
                     self.learning_unit_year.learning_container_year.requirement_entity,
                     self.learning_unit_year.credits,
                     xls_build.translate(self.learning_unit_year.status)]]
        expected_argument = _generate_xls_build_parameter(xls_data, self.user)
        mock_generate_xls.assert_called_with(expected_argument, None)


def _generate_xls_build_parameter(xls_data, user):
    titles = learning_unit_titles_part_1()
    titles.extend(learning_unit_titles_part2())
    return {
        xls_build.LIST_DESCRIPTION_KEY: _(base.business.learning_unit_xls.XLS_DESCRIPTION),
        xls_build.FILENAME_KEY: _(base.business.learning_unit_xls.XLS_FILENAME),
        xls_build.USER_KEY: user.username,
        xls_build.WORKSHEETS_DATA: [{
            xls_build.CONTENT_KEY: xls_data,
            xls_build.HEADER_TITLES_KEY: titles,
            xls_build.WORKSHEET_TITLE_KEY: _(base.business.learning_unit_xls.WORKSHEET_TITLE),
            xls_build.STYLED_CELLS: None,
            xls_build.COLORED_ROWS: None,
            xls_build.ROW_HEIGHT: None,
        }]
    }


class TestLearningUnitComponents(TestCase):
    @classmethod
    def setUpTestData(cls):
        start_year = AcademicYearFactory(year=2010)
        end_year = AcademicYearFactory(year=2020)
        cls.academic_years = GenerateAcademicYear(start_year=start_year, end_year=end_year).academic_years
        cls.generated_container = GenerateContainer(start_year=start_year, end_year=end_year)
        cls.a_superuser = SuperUserFactory()
        cls.person = PersonFactory(user=cls.a_superuser)
        cls.learning_unit_year = cls.generated_container.generated_container_years[0].learning_unit_year_full

    def setUp(self):
        self.client.force_login(self.a_superuser)

    @mock.patch('base.models.program_manager.is_program_manager')
    def test_learning_unit_components(self, mock_program_manager):
        mock_program_manager.return_value = True

        response = self.client.get(reverse(learning_unit_components, args=[self.learning_unit_year.id]))

        self.assertTemplateUsed(response, 'learning_unit/components.html')
        components = response.context['components']
        self.assertEqual(len(components), 4)

        for component in components:
            self.assertIn(component['learning_component_year'],
                          self.generated_container.generated_container_years[0].list_components)

            volumes = component['volumes']
            self.assertEqual(volumes[VOLUME_Q1], None)
            self.assertEqual(volumes[VOLUME_Q2], None)

    def test_tab_active_url(self):
        url = reverse("learning_unit_components", args=[self.learning_unit_year.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTrue("tab_active" in response.context)
        self.assertEqual(response.context["tab_active"], 'learning_unit_components')

        url_tab_active = reverse(response.context["tab_active"], args=[self.learning_unit_year.id])
        response = self.client.get(url_tab_active)
        self.assertEqual(response.status_code, HttpResponse.status_code)


class TestLearningAchievements(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = create_current_academic_year()
        cls.learning_unit_year = LearningUnitYearFactory(
            academic_year=cls.academic_year,
            subtype=learning_unit_year_subtypes.FULL
        )

        cls.code_languages = ["FR", "EN", "IT"]
        for code_language in cls.code_languages:
            language = LanguageFactory(code=code_language)
            LearningAchievementFactory(language=language, learning_unit_year=cls.learning_unit_year)

    def test_get_achievements_group_by_language_no_achievement(self):
        a_luy_without_achievements = LearningUnitYearFactory(
            academic_year=self.academic_year,
            subtype=learning_unit_year_subtypes.FULL
        )
        result = learning_unit_business.get_achievements_group_by_language(a_luy_without_achievements)
        self.assertIsInstance(result, dict)
        self.assertFalse(result)

    def test_get_achievements_group_by_language(self):
        result = learning_unit_business.get_achievements_group_by_language(self.learning_unit_year)
        self.assertIsInstance(result, dict)
        for code_language in self.code_languages:
            key = "achievements_{}".format(code_language)
            self.assertTrue(result[key])


class TestLearningUnitProposalComparison(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = SuperUserFactory()
        PersonFactory(user=cls.user)
        cls.current_academic_year = create_current_academic_year()
        an_organization = OrganizationFactory(type=organization_type.MAIN)
        learning_container_year = LearningContainerYearFactory(
            academic_year=cls.current_academic_year,
            container_type=learning_container_year_types.COURSE,
            common_title="common_title",
            type_declaration_vacant=DO_NOT_ASSIGN,
            requirement_entity=EntityVersionFactory().entity
        )
        cls.learning_unit_year = LearningUnitYearFakerFactory(
            credits=5,
            subtype=learning_unit_year_subtypes.FULL,
            academic_year=cls.current_academic_year,
            learning_container_year=learning_container_year,
            campus=CampusFactory(organization=an_organization, is_administration=True),
            periodicity=learning_unit_year_periodicity.BIENNIAL_ODD
        )

        cls.previous_academic_year = AcademicYearFactory(year=cls.current_academic_year.year - 1)
        cls.previous_learning_container_year = LearningContainerYearFactory(
            academic_year=cls.previous_academic_year,
            container_type=learning_container_year_types.COURSE,
            common_title="previous_common_title",
            type_declaration_vacant=DO_NOT_ASSIGN,
            learning_container=cls.learning_unit_year.learning_container_year.learning_container
        )
        cls.previous_learning_unit_year = LearningUnitYearFakerFactory(
            credits=5,
            subtype=learning_unit_year_subtypes.FULL,
            academic_year=cls.previous_academic_year,
            learning_container_year=cls.previous_learning_container_year,
            periodicity=learning_unit_year_periodicity.BIENNIAL_ODD,
            learning_unit=cls.learning_unit_year.learning_unit
        )
        cls.next_academic_year = AcademicYearFactory(year=cls.current_academic_year.year + 1)
        cls.next_learning_container_year = LearningContainerYearFactory(
            academic_year=cls.next_academic_year,
            container_type=learning_container_year_types.COURSE,
            common_title="next_common_title",
            type_declaration_vacant=DO_NOT_ASSIGN,
            learning_container=cls.learning_unit_year.learning_container_year.learning_container
        )
        cls.next_learning_unit_year = LearningUnitYearFakerFactory(
            credits=5,
            subtype=learning_unit_year_subtypes.FULL,
            academic_year=cls.next_academic_year,
            learning_container_year=cls.next_learning_container_year,
            periodicity=learning_unit_year_periodicity.BIENNIAL_ODD,
            learning_unit=cls.learning_unit_year.learning_unit
        )
        today = datetime.date.today()

        an_entity = EntityFactory(organization=an_organization)
        cls.entity_version = EntityVersionFactory(entity=an_entity, entity_type=entity_type.SCHOOL, start_date=today,
                                                  end_date=today.replace(year=today.year + 1))
        cls.learning_component_year_lecturing = LearningComponentYearFactory(
            type=learning_component_year_type.LECTURING,
            acronym="PM",
            learning_unit_year=cls.learning_unit_year,
            repartition_volume_requirement_entity=Decimal(10),
            repartition_volume_additional_entity_1=Decimal(10),
            repartition_volume_additional_entity_2=Decimal(10)
        )
        cls.learning_component_year_practical = LearningComponentYearFactory(
            type=learning_component_year_type.PRACTICAL_EXERCISES,
            acronym="PP",
            learning_unit_year=cls.learning_unit_year,
            repartition_volume_requirement_entity=Decimal(10),
            repartition_volume_additional_entity_1=Decimal(10),
            repartition_volume_additional_entity_2=Decimal(10)
        )

        requirement_entity = cls.learning_unit_year.learning_container_year.requirement_entity
        initial_data_expected = {
            "learning_container_year": {
                "id": cls.learning_unit_year.learning_container_year.id,
                "acronym": cls.learning_unit_year.acronym,
                "common_title": cls.learning_unit_year.learning_container_year.common_title,
                "common_title_english": cls.learning_unit_year.learning_container_year.common_title_english,
                "container_type": cls.learning_unit_year.learning_container_year.container_type,
                "in_charge": cls.learning_unit_year.learning_container_year.in_charge,
                "type_declaration_vacant": cls.learning_unit_year.learning_container_year.type_declaration_vacant,
                "requirement_entity": requirement_entity.id,
                "allocation_entity": None,
                "additional_entity_1": requirement_entity.id,
                "additional_entity_2": requirement_entity.id,
            },
            "learning_unit_year": {
                "id": cls.learning_unit_year.id,
                "acronym": cls.learning_unit_year.acronym,
                "specific_title": cls.learning_unit_year.specific_title,
                "specific_title_english": cls.learning_unit_year.specific_title_english,
                "internship_subtype": cls.learning_unit_year.internship_subtype,
                "credits": cls.learning_unit_year.credits,
                "quadrimester": cls.learning_unit_year.quadrimester,
                "status": cls.learning_unit_year.status,
                "language": cls.learning_unit_year.language.pk,
                "campus": cls.learning_unit_year.campus.id,
                "periodicity": cls.learning_unit_year.periodicity,
                "attribution_procedure": cls.learning_unit_year.attribution_procedure
            },
            "learning_unit": {
                "id": cls.learning_unit_year.learning_unit.id
            },
            "learning_component_years": [
                {"id": cls.learning_component_year_lecturing.id,
                 "type": "LECTURING",
                 "planned_classes": cls.learning_component_year_lecturing.planned_classes,
                 "hourly_volume_partial_q1": cls.learning_component_year_lecturing.hourly_volume_partial_q1,
                 "hourly_volume_partial_q2": cls.learning_component_year_lecturing.hourly_volume_partial_q2,
                 "hourly_volume_total_annual": cls.learning_component_year_lecturing.hourly_volume_total_annual,
                 "repartition_volume_requirement_entity":
                     cls.learning_component_year_lecturing.repartition_volume_requirement_entity,
                 "repartition_volume_additional_entity_1":
                     cls.learning_component_year_lecturing.repartition_volume_additional_entity_1,
                 "repartition_volume_additional_entity_2":
                     cls.learning_component_year_lecturing.repartition_volume_additional_entity_2
                 },
                {"id": cls.learning_component_year_practical.id,
                 "type": "PRACTICAL_EXERCISES",
                 "planned_classes": cls.learning_component_year_practical.planned_classes,
                 "hourly_volume_partial_q1": cls.learning_component_year_practical.hourly_volume_partial_q1,
                 "hourly_volume_partial_q2": cls.learning_component_year_practical.hourly_volume_partial_q2,
                 "hourly_volume_total_annual": cls.learning_component_year_practical.hourly_volume_total_annual,
                 "repartition_volume_requirement_entity": cls.learning_component_year_practical.
                     repartition_volume_requirement_entity,
                 "repartition_volume_additional_entity_1": cls.learning_component_year_practical.
                     repartition_volume_additional_entity_1,
                 "repartition_volume_additional_entity_2": cls.learning_component_year_practical.
                     repartition_volume_additional_entity_2
                 }
            ],
            "volumes": {
                'PM': {
                    VOLUME_Q1: cls.learning_component_year_lecturing.hourly_volume_partial_q1,
                    VOLUME_Q2: cls.learning_component_year_lecturing.hourly_volume_partial_q2,
                    REAL_CLASSES: 1,
                    VOLUME_TOTAL: cls.learning_component_year_practical.hourly_volume_total_annual,
                    PLANNED_CLASSES: cls.learning_component_year_lecturing.planned_classes,
                    VOLUME_REQUIREMENT_ENTITY: Decimal(120),
                    VOLUME_TOTAL_REQUIREMENT_ENTITIES: Decimal(120),
                    VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1: Decimal(0),
                    VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2: Decimal(0)
                },
                'PP': {
                    VOLUME_Q1: Decimal(10), VOLUME_Q2: Decimal(10), REAL_CLASSES: 0, VOLUME_TOTAL: Decimal(20),
                    PLANNED_CLASSES: 0, VOLUME_REQUIREMENT_ENTITY: Decimal(0),
                    VOLUME_TOTAL_REQUIREMENT_ENTITIES: Decimal(0),
                    VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1: Decimal(0),
                    VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2: Decimal(0)
                }
            }
        }
        cls.learning_unit_proposal = ProposalLearningUnitFactory(learning_unit_year=cls.learning_unit_year,
                                                                 initial_data=initial_data_expected,
                                                                 type=proposal_type.ProposalType.MODIFICATION.name,
                                                                 state=proposal_state.ProposalState.FACULTY.name)

    def setUp(self):
        self.client.force_login(self.user)

    def test_learning_unit_proposal_comparison_without_data_modified(self):
        response = self.client.get(reverse(learning_unit_proposal_comparison, args=[self.learning_unit_year.pk]))
        self.assertTemplateUsed(response, 'learning_unit/proposal_comparison.html')
        self.assertEqual(response.context['learning_unit_year_fields'], [])

    def test_learning_unit_proposal_comparison_with_learning_unit_year_data_modified(self):
        self.learning_unit_year.credits = 6
        self.learning_unit_year.periodicity = learning_unit_year_periodicity.BIENNIAL_EVEN
        self.learning_unit_year.attribution_procedure = EXTERNAL
        self.learning_unit_year.save()
        response = self.client.get(reverse(learning_unit_proposal_comparison, args=[self.learning_unit_year.pk]))
        self.assertListEqual(response.context['learning_unit_year_fields'],
                             [
                                 [_('Credits'), 5, 6.00],
                                 [_('Periodicity'), _("biennial odd"), _("biennial even")],
                                 [_('Procedure'), "-", _("External")]
                             ])

    def test_learning_unit_proposal_comparison_with_learning_container_year_data_modified(self):
        self.learning_unit_year.learning_container_year.common_title = "common title modified"
        self.learning_unit_year.learning_container_year.type_declaration_vacant = VACANT_NOT_PUBLISH
        self.learning_unit_year.learning_container_year.save()
        response = self.client.get(reverse(learning_unit_proposal_comparison, args=[self.learning_unit_year.pk]))
        self.assertEqual(
            response.context['learning_container_year_fields'],
            [
                [_('Decision'), _("Do not assign"), _("Vacant not publish")],
                [_('Common title'), "common_title", "common title modified"]
            ]
        )

    def test_learning_unit_proposal_comparison_with_volumes_data_modified(self):
        self.learning_unit_year.learning_container_year.allocation_entity = EntityVersionFactory().entity
        self.learning_unit_year.learning_container_year.save()
        response = self.client.get(reverse(learning_unit_proposal_comparison, args=[self.learning_unit_year.pk]))
        self.assertEqual(response.context['components'][1][0], _("Practical exercises"))
        self.assertEqual(response.context['components'][1][1][_('Volume total annual')], [20, 0])
        self.assertEqual(response.context['components'][1][1][_('Planned classes')], [0, 1])
        self.assertEqual(response.context['components'][1][1][_('Volume Q1')], [10, 0])
        self.assertEqual(response.context['components'][1][1][_('Volume Q2')], [10, 0])

    def test_learning_unit_comparison_whitout_previous_and_next(self):
        self.previous_learning_unit_year.delete()
        response = self.client.get(reverse(learning_unit_comparison, args=[self.learning_unit_year.pk]))
        self.assertTemplateUsed(response, 'learning_unit/comparison.html')
        self.assertEqual(response.context['previous'], {})
        self.assertNotEqual(response.context['next'], {})
        self.next_learning_unit_year.delete()
        response = self.client.get(reverse(learning_unit_comparison, args=[self.learning_unit_year.pk]))
        self.assertTemplateUsed(response, 'learning_unit/comparison.html')
        self.assertEqual(response.context['previous'], {})
        self.assertEqual(response.context['next'], {})

    def test_learning_unit_comparison(self):
        response = self.client.get(reverse(learning_unit_comparison, args=[self.learning_unit_year.pk]))
        self.assertTemplateUsed(response, 'learning_unit/comparison.html')
        self.assertNotEqual(response.context['previous'], {})
        self.assertNotEqual(response.context['next'], {})
