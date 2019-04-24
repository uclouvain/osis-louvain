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
from unittest import mock

import factory.fuzzy
import reversion
from django.contrib.auth.models import Permission, Group
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseForbidden
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseRedirect
from django.test import TestCase, RequestFactory, Client
from django.test.utils import override_settings
from django.utils.translation import ugettext_lazy as _
from waffle.testutils import override_flag

import base.business.learning_unit
import base.business.xls
import reference.models.language
from attribution.tests.factories.attribution_charge_new import AttributionChargeNewFactory
from attribution.tests.factories.attribution_new import AttributionNewFactory
from base.business import learning_unit as learning_unit_business
from base.business.learning_unit import learning_unit_titles_part1, learning_unit_titles_part2
from base.forms.learning_unit.learning_unit_create import LearningUnitModelForm
from base.forms.learning_unit.search_form import LearningUnitYearForm
from base.forms.learning_unit_specifications import LearningUnitSpecificationsForm, LearningUnitSpecificationsEditForm
from base.models.academic_year import AcademicYear
from base.models.enums import entity_container_year_link_type, active_status, education_group_categories, \
    learning_component_year_type, proposal_type, proposal_state
from base.models.enums import entity_type
from base.models.enums import internship_subtypes
from base.models.enums import learning_container_year_types, organization_type
from base.models.enums import learning_unit_year_periodicity
from base.models.enums import learning_unit_year_session
from base.models.enums import learning_unit_year_subtypes
from base.models.enums.attribution_procedure import EXTERNAL
from base.models.enums.groups import FACULTY_MANAGER_GROUP
from base.models.enums.learning_container_year_types import LearningContainerYearType
from base.models.enums.vacant_declaration_type import DO_NOT_ASSIGN, VACANT_NOT_PUBLISH
from base.models.person import Person
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year
from base.tests.factories.business.learning_units import GenerateContainer, GenerateAcademicYear
from base.tests.factories.campus import CampusFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.external_learning_unit_year import ExternalLearningUnitYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_achievement import LearningAchievementFactory
from base.tests.factories.learning_class_year import LearningClassYearFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory, \
    LecturingLearningComponentYearFactory, PracticalLearningComponentYearFactory
from base.tests.factories.learning_container import LearningContainerFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory, LearningUnitYearPartimFactory, \
    LearningUnitYearFullFactory, LearningUnitYearFakerFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory, PersonWithPermissionsFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from base.tests.factories.user import SuperUserFactory, UserFactory
from base.views.learning_unit import learning_unit_components, learning_unit_specifications, \
    get_charge_repartition_warning_messages, learning_unit_attributions, learning_unit_comparison, \
    learning_unit_proposal_comparison
from base.views.learning_unit import learning_unit_specifications_edit
from base.views.learning_units.create import create_partim_form
from base.views.learning_units.pedagogy.read import learning_unit_pedagogy
from base.views.learning_units.search import learning_units_service_course
from cms.enums import entity_name
from cms.tests.factories.text_label import TextLabelFactory
from cms.tests.factories.translated_text import TranslatedTextFactory
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
        from django.utils.encoding import uri_to_iri
        self.assertEqual(uri_to_iri(uri_to_iri(response.url)), '/login/?next={}'.format(self.url))
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
    def setUp(self):
        self.current_academic_year = create_current_academic_year()
        self.learning_unit_year_full = LearningUnitYearFactory(
            academic_year=self.current_academic_year,
            learning_container_year__academic_year=self.current_academic_year,
            subtype=learning_unit_year_subtypes.FULL
        )
        self.url = reverse(create_partim_form, kwargs={'learning_unit_year_id': self.learning_unit_year_full.id})
        self.user = UserFactory()
        self.user.user_permissions.add(Permission.objects.get(codename="can_access_learningunit"))
        self.user.user_permissions.add(Permission.objects.get(codename="can_create_learningunit"))
        PersonFactory(user=self.user)
        self.client.force_login(self.user)

    def test_create_partim_form_when_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_create_partim_form_when_user_doesnt_have_perms(self):
        a_user_without_perms = UserFactory()
        self.client.force_login(a_user_without_perms)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_create_partim_form_invalid_http_methods(self):
        response = self.client.delete(self.url)
        self.assertTemplateUsed(response, "method_not_allowed.html")
        self.assertEqual(response.status_code, HttpResponseNotAllowed.status_code)

    @mock.patch('base.views.learning_units.perms.business_perms.is_person_linked_to_entity_in_charge_of_learning_unit',
                side_effect=lambda *args: False)
    def test_create_partim_when_user_not_linked_to_entity_charge(self, mock_is_pers_linked_to_entity_charge):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "access_denied.html")
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
        today = datetime.date.today()
        cls.current_academic_year, *cls.academic_years = AcademicYearFactory.produce_in_future(quantity=8)

        cls.learning_container_yr = LearningContainerYearFactory(academic_year=cls.current_academic_year)
        cls.luy = LearningUnitYearFactory(
            academic_year=cls.current_academic_year,
            learning_container_year=cls.learning_container_yr
        )
        cls.learning_component_yr = LearningComponentYearFactory(learning_unit_year=cls.luy,
                                                                 hourly_volume_total_annual=10,
                                                                 hourly_volume_partial_q1=5,
                                                                 hourly_volume_partial_q2=5)
        cls.organization = OrganizationFactory(type=organization_type.MAIN)
        cls.country = CountryFactory()

        cls.entities = EntityFactory.create_batch(3, country=cls.country, organization=cls.organization)

        cls.entity_container_yr = EntityContainerYearFactory(
            learning_container_year=cls.learning_container_yr,
            type=entity_container_year_link_type.REQUIREMENT_ENTITY,
            entity=cls.entities[0]
        )
        cls.entity_version = EntityVersionFactory(entity=cls.entities[0], entity_type=entity_type.SCHOOL,
                                                  start_date=today - datetime.timedelta(days=1),
                                                  end_date=today.replace(year=today.year + 1))
        cls.entity_version_2 = EntityVersionFactory(entity=cls.entities[1], entity_type=entity_type.INSTITUTE,
                                                    start_date=today - datetime.timedelta(days=20),
                                                    end_date=today.replace(year=today.year + 1))
        cls.entity_version_3 = EntityVersionFactory(entity=cls.entities[2], entity_type=entity_type.FACULTY,
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

    def test_learning_units_search(self):
        response = self.client.get(reverse('learning_units'))

        context = response.context
        self.assertTemplateUsed(response, 'learning_units.html')
        self.assertEqual(context['academic_years'].count(), len(self.academic_years) + 1)
        self.assertEqual(context['current_academic_year'], self.current_academic_year)
        self.assertEqual(len(context['types']),
                         len(learning_unit_year_subtypes.LEARNING_UNIT_YEAR_SUBTYPES))
        self.assertEqual(len(context['container_types']), len(LearningContainerYearType.choices()))
        self.assertTrue(context['experimental_phase'])
        self.assertEqual(context['learning_units_count'], 0)

    def test_learning_units_search_with_acronym_filtering(self):
        self._prepare_context_learning_units_search()

        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'acronym': 'LBIR',
            'status': active_status.ACTIVE
        }
        response = self.client.get(reverse('learning_units'), data=filter_data)

        self.assertTemplateUsed(response, 'learning_units.html')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_learning_units_search_by_acronym_with_valid_regex(self):
        self._prepare_context_learning_units_search()
        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'acronym': '^DRT.+A'
        }
        response = self.client.get(reverse('learning_units'), data=filter_data)

        self.assertTemplateUsed(response, 'learning_units.html')
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_learning_units_search_by_acronym_with_invalid_regex(self):
        self._prepare_context_learning_units_search()

        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'acronym': '^LB(+)2+',
            'status': active_status.ACTIVE
        }
        response = self.client.get(reverse('learning_units'), data=filter_data)

        self.assertTemplateUsed(response, 'learning_units.html')
        self.assertEqual(response.context['form'].errors['acronym'], [_('LU_ERRORS_INVALID_REGEX_SYNTAX')])

    def test_learning_units_search_with_requirement_entity(self):
        self._prepare_context_learning_units_search()

        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'requirement_entity_acronym': 'ENVI'
        }
        response = self.client.get(reverse('learning_units'), data=filter_data)

        self.assertTemplateUsed(response, 'learning_units.html')
        self.assertEqual(response.context['learning_units_count'], 1)

    def test_learning_units_search_with_requirement_entity_and_subord(self):
        self._prepare_context_learning_units_search()
        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'requirement_entity_acronym': 'AGRO',
            'with_entity_subordinated': True
        }
        response = self.client.get(reverse('learning_units'), data=filter_data)
        self.assertTemplateUsed(response, 'learning_units.html')

        self.assertEqual(response.context['learning_units_count'], 6)

    def test_learning_units_search_with_allocation_entity(self):
        self._prepare_context_learning_units_search()
        request_factory = RequestFactory()
        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'allocation_entity_acronym': 'AGES'
        }
        response = self.client.get(reverse('learning_units'), data=filter_data)

        self.assertTemplateUsed(response, 'learning_units.html')
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_learning_units_search_with_requirement_and_allocation_entity(self):
        self._prepare_context_learning_units_search()
        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'requirement_entity_acronym': 'ENVI',
            'allocation_entity_acronym': 'AGES'
        }
        response = self.client.get(reverse('learning_units'), data=filter_data)

        self.assertTemplateUsed(response, 'learning_units.html')
        self.assertEqual(response.context['learning_units_count'], 1)

    def test_learning_units_search_with_service_course_no_result(self):
        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'requirement_entity_acronym': 'AGRO',
            'with_entity_subordinated': True
        }
        number_of_results = 0
        self.service_course_search(filter_data, number_of_results)

    def test_learning_units_search_with_service_course_without_entity_subordinated(self):
        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'requirement_entity_acronym': 'ELOG',
            'with_entity_subordinated': False
        }
        number_of_results = 1
        self.service_course_search(filter_data, number_of_results)

    def test_learning_units_search_with_service_course_with_entity_subordinated(self):
        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'requirement_entity_acronym': 'PSP',
            'with_entity_subordinated': True
        }

        number_of_results = 1
        self.service_course_search(filter_data, number_of_results)

    def test_lu_search_with_service_course_with_entity_subordinated_requirement_and_wrong_allocation(self):
        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'requirement_entity_acronym': 'PSP',
            'allocation_entity_acronym': 'ELOG',
            'with_entity_subordinated': True
        }
        number_of_results = 0
        self.service_course_search(filter_data, number_of_results)

    def service_course_search(self, filter_data, number_of_results):
        self._prepare_context_learning_units_search()
        response = self.client.get(reverse(learning_units_service_course), data=filter_data)

        self.assertTemplateUsed(response, 'learning_units.html')
        self.assertEqual(response.context['learning_units_count'], number_of_results)

    def test_learning_unit_read(self):
        learning_container_year = LearningContainerYearFactory(academic_year=self.current_academic_year)
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=learning_container_year,
                                                     subtype=learning_unit_year_subtypes.FULL)

        response = self.client.get(reverse('learning_unit', args=[learning_unit_year.pk]))

        self.assertTemplateUsed(response, 'learning_unit/identification.html')
        self.assertEqual(response.context['learning_unit_year'], learning_unit_year)

    def test_learning_unit_read_versions(self):
        learning_unit_year = LearningUnitYearFullFactory(
            academic_year=self.current_academic_year,
        )
        LearningComponentYearFactory(learning_unit_year=learning_unit_year)

        response = self.client.get(reverse('learning_unit', args=[learning_unit_year.pk]))
        self.assertEqual(len(response.context['versions']), 0)

        with reversion.create_revision():
            learning_unit_year.learning_container_year.save()

        response = self.client.get(reverse('learning_unit', args=[learning_unit_year.pk]))
        self.assertEqual(len(response.context['versions']), 1)

        with reversion.create_revision():
            learning_unit_year.learningcomponentyear_set.first().save()

        response = self.client.get(reverse('learning_unit', args=[learning_unit_year.pk]))
        self.assertEqual(len(response.context['versions']), 2)

    def test_external_learning_unit_read(self):
        external_learning_unit_year = ExternalLearningUnitYearFactory(
            learning_unit_year__subtype=learning_unit_year_subtypes.FULL,
        )
        learning_unit_year = external_learning_unit_year.learning_unit_year

        response = self.client.get(reverse('learning_unit', args=[learning_unit_year.pk]))

        self.assertTemplateUsed(response, 'learning_unit/external/read.html')
        self.assertEqual(response.context['learning_unit_year'], learning_unit_year)

    def test_external_learning_unit_read_permission_denied(self):
        learning_container_year = LearningContainerYearFactory(academic_year=self.current_academic_year)
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=learning_container_year,
                                                     subtype=learning_unit_year_subtypes.FULL)
        external_learning_unit_year = ExternalLearningUnitYearFactory(learning_unit_year=learning_unit_year)
        learning_unit_year = external_learning_unit_year.learning_unit_year

        a_user_without_perms = PersonFactory().user
        client = Client()
        client.force_login(a_user_without_perms)

        response = client.get(reverse("learning_unit", args=[learning_unit_year.id]))
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

        a_user_without_perms.user_permissions.add(
            Permission.objects.get(codename='can_access_externallearningunityear'))

        response = client.get(reverse("learning_unit", args=[learning_unit_year.id]))
        self.assertEqual(response.status_code, 200)

    def test_warnings_learning_unit_read(self):
        learning_container_year = LearningContainerYearFactory(academic_year=self.current_academic_year,
                                                               container_type=learning_container_year_types.INTERNSHIP)
        LearningUnitYearFactory(academic_year=self.current_academic_year,
                                learning_container_year=learning_container_year,
                                internship_subtype=internship_subtypes.TEACHING_INTERNSHIP,
                                subtype=learning_unit_year_subtypes.FULL,
                                periodicity=learning_unit_year_periodicity.BIENNIAL_ODD,
                                status=False)
        partim_without_internship = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                            learning_container_year=learning_container_year,
                                                            internship_subtype=None,
                                                            subtype=learning_unit_year_subtypes.PARTIM,
                                                            periodicity=learning_unit_year_periodicity.ANNUAL,
                                                            status=True)

        response = self.client.get(reverse('learning_unit', args=[partim_without_internship.pk]))

        self.assertTemplateUsed(response, 'learning_unit/identification.html')
        self.assertEqual(len(response.context['warnings']), 3)

    def test_learning_unit__with_faculty_manager_when_can_edit_end_date(self):
        learning_container_year = LearningContainerYearFactory(
            academic_year=self.current_academic_year, container_type=learning_container_year_types.OTHER_COLLECTIVE)
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=learning_container_year,
                                                     subtype=learning_unit_year_subtypes.FULL)
        entity_container = EntityContainerYearFactory(learning_container_year=learning_container_year,
                                                      type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        EntityVersionFactory(entity=entity_container.entity)

        learning_unit_year.learning_unit.end_year = None
        learning_unit_year.learning_unit.save()

        person_entity = PersonEntityFactory(entity=entity_container.entity)
        person_entity.person.user.groups.add(Group.objects.get(name=FACULTY_MANAGER_GROUP))
        url = reverse("learning_unit", args=[learning_unit_year.id])
        self.client.force_login(person_entity.person.user)

        response = self.client.get(url)
        self.assertEqual(response.context["can_edit_date"], True)

    def test_learning_unit_of_type_partim_with_faculty_manager(self):
        learning_container_year = LearningContainerYearFactory(
            academic_year=self.current_academic_year, container_type=learning_container_year_types.COURSE)
        LearningUnitYearFactory(academic_year=self.current_academic_year,
                                learning_container_year=learning_container_year,
                                subtype=learning_unit_year_subtypes.FULL)
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=learning_container_year,
                                                     subtype=learning_unit_year_subtypes.PARTIM)
        entity_container = EntityContainerYearFactory(learning_container_year=learning_container_year,
                                                      type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        EntityVersionFactory(entity=entity_container.entity)
        learning_unit_year.learning_unit.end_year = None
        learning_unit_year.learning_unit.save()

        person_entity = PersonEntityFactory(entity=entity_container.entity)
        group, created = Group.objects.get_or_create(name=FACULTY_MANAGER_GROUP)
        person_entity.person.user.groups.add(group)
        url = reverse("learning_unit", args=[learning_unit_year.id])
        self.client.force_login(person_entity.person.user)

        response = self.client.get(url)
        self.assertEqual(response.context["can_edit_date"], True)

    def test_learning_unit_with_faculty_manager_when_cannot_edit_end_date(self):
        learning_container_year = \
            LearningContainerYearFactory(academic_year=self.current_academic_year,
                                         container_type=learning_container_year_types.COURSE)
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=learning_container_year,
                                                     subtype=learning_unit_year_subtypes.FULL)
        entity_container = EntityContainerYearFactory(learning_container_year=learning_container_year,
                                                      type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        EntityVersionFactory(entity=entity_container.entity)
        learning_unit_year.learning_unit.end_year = None
        learning_unit_year.learning_unit.save()

        person_entity = PersonEntityFactory(entity=entity_container.entity)
        group, created = Group.objects.get_or_create(name=FACULTY_MANAGER_GROUP)
        person_entity.person.user.groups.add(group)
        url = reverse("learning_unit", args=[learning_unit_year.id])
        self.client.force_login(person_entity.person.user)

        response = self.client.get(url)
        self.assertEqual(response.context["can_edit_date"], False)

    def test_get_components_no_learning_container_yr(self):
        luy_without_components = LearningUnitYearFactory(academic_year=self.current_academic_year)
        components_dict = learning_unit_business.get_same_container_year_components(luy_without_components)
        self.assertEqual(len(components_dict.get('components')), 0)

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

    def test_get_partims_identification_tabs(self):
        learning_unit_container_year = LearningContainerYearFactory(
            academic_year=self.current_academic_year
        )
        learning_unit_year = LearningUnitYearFactory(
            acronym="LCHIM1210",
            learning_container_year=learning_unit_container_year,
            subtype=learning_unit_year_subtypes.FULL,
            academic_year=self.current_academic_year
        )
        LearningUnitYearFactory(
            acronym="LCHIM1210A",
            learning_container_year=learning_unit_container_year,
            subtype=learning_unit_year_subtypes.PARTIM,
            academic_year=self.current_academic_year
        )
        LearningUnitYearFactory(
            acronym="LCHIM1210B",
            learning_container_year=learning_unit_container_year,
            subtype=learning_unit_year_subtypes.PARTIM,
            academic_year=self.current_academic_year
        )
        LearningUnitYearFactory(
            acronym="LCHIM1210F",
            learning_container_year=learning_unit_container_year,
            subtype=learning_unit_year_subtypes.PARTIM,
            academic_year=self.current_academic_year
        )

        response = self.client.get(reverse('learning_unit', args=[learning_unit_year.pk]))

        self.assertTemplateUsed(response, 'learning_unit/identification.html')
        self.assertEqual(len(response.context['learning_container_year_partims']), 3)

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
        l_container_yr = LearningContainerYearFactory(acronym="LBIR1100", academic_year=self.current_academic_year,
                                                      container_type=learning_container_year_types.COURSE)
        EntityContainerYearFactory(learning_container_year=l_container_yr, entity=agro_entity_v.entity,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        LearningUnitYearFactory(acronym="LBIR1100", learning_container_year=l_container_yr,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)
        LearningUnitYearFactory(acronym="LBIR1100A", learning_container_year=l_container_yr,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.PARTIM)
        LearningUnitYearFactory(acronym="LBIR1100B", learning_container_year=l_container_yr,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.PARTIM)
        LearningUnitYearFactory(acronym="LBIR1100C", learning_container_year=l_container_yr,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.PARTIM,
                                status=False)

        # Create another UE and put entity charge [ENV]
        l_container_yr_2 = LearningContainerYearFactory(acronym="CHIM1200", academic_year=self.current_academic_year,
                                                        container_type=learning_container_year_types.COURSE)
        EntityContainerYearFactory(learning_container_year=l_container_yr_2, entity=envi_entity_v.entity,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        EntityContainerYearFactory(learning_container_year=l_container_yr_2, entity=ages_entity_v.entity,
                                   type=entity_container_year_link_type.ALLOCATION_ENTITY)
        LearningUnitYearFactory(acronym="CHIM1200", learning_container_year=l_container_yr_2,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)

        # Create another UE and put entity charge [DRT]
        l_container_yr_3 = LearningContainerYearFactory(acronym="DRT1500", academic_year=self.current_academic_year,
                                                        container_type=learning_container_year_types.COURSE)
        EntityContainerYearFactory(learning_container_year=l_container_yr_3, entity=drt_entity_v.entity,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        LearningUnitYearFactory(acronym="DRT1500", learning_container_year=l_container_yr_3,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)
        LearningUnitYearFactory(acronym="DRT1500A", learning_container_year=l_container_yr_3,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.PARTIM)

        # Create another UE and put entity charge [ESPO]
        l_container_yr_4 = LearningContainerYearFactory(acronym="ESPO1500", academic_year=self.current_academic_year,
                                                        container_type=learning_container_year_types.DISSERTATION)
        EntityContainerYearFactory(learning_container_year=l_container_yr_4, entity=espo_entity_v.entity,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        LearningUnitYearFactory(acronym="ESPO1500", learning_container_year=l_container_yr_4,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)

        # Create another UE and put entity charge [AGES]
        l_container_yr_4 = LearningContainerYearFactory(acronym="AGES1500", academic_year=self.current_academic_year,
                                                        container_type=learning_container_year_types.MASTER_THESIS)
        EntityContainerYearFactory(learning_container_year=l_container_yr_4, entity=ages_entity_v.entity,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        LearningUnitYearFactory(acronym="AGES1500", learning_container_year=l_container_yr_4,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)

        # Create another UE and put entity charge [ELOG] and allocation charge [LOGO]
        l_container_yr_5 = LearningContainerYearFactory(acronym="LOGO1200", academic_year=self.current_academic_year,
                                                        container_type=learning_container_year_types.COURSE)
        EntityContainerYearFactory(learning_container_year=l_container_yr_5, entity=elog_entity_v.entity,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        EntityContainerYearFactory(learning_container_year=l_container_yr_5, entity=logo_entity_v.entity,
                                   type=entity_container_year_link_type.ALLOCATION_ENTITY)
        LearningUnitYearFactory(acronym="LOGO1200", learning_container_year=l_container_yr_5,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)

    def get_base_form_data(self):
        data = self.get_common_data()
        data.update(self.get_learning_unit_data())
        data['internship_subtype'] = internship_subtypes.TEACHING_INTERNSHIP
        return data

    def get_base_partim_form_data(self, original_learning_unit_year):
        data = self.get_common_data()
        data.update(self.get_partim_data(original_learning_unit_year))
        data['specific_title'] = "Partim partial title"
        data['status'] = original_learning_unit_year.status
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

    def get_faulty_acronym(self):
        faulty_dict = dict(self.get_valid_data())
        faulty_dict["acronym"] = "TA200"
        return faulty_dict

    def get_existing_acronym(self):
        faulty_dict = dict(self.get_valid_data())
        faulty_dict["acronym_1"] = "DRT2018"
        return faulty_dict

    def get_empty_internship_subtype(self):
        faulty_dict = dict(self.get_valid_data())
        faulty_dict["container_type"] = learning_container_year_types.INTERNSHIP
        faulty_dict["internship_subtype"] = ""
        return faulty_dict

    def get_empty_acronym(self):
        faulty_dict = dict(self.get_valid_data())
        faulty_dict["acronym"] = ""
        return faulty_dict

    def get_faulty_requirement_entity(self):
        """We will create an entity + entity version that user cannot create on it"""
        entity = EntityFactory(country=self.country, organization=self.organization)
        entity_version = EntityVersionFactory(entity=entity, entity_type=entity_type.SCHOOL, end_date=None,
                                              start_date=datetime.date.today())
        faulty_dict = dict(self.get_valid_data())
        faulty_dict['requirement_entity'] = entity_version.id
        return faulty_dict

    def _get_volumes_data(self, learning_units_year):
        if not isinstance(learning_units_year, list):
            learning_units_year = [learning_units_year]
        data = {}
        for learning_unit_year in learning_units_year:
            data['VOLUME_TOTAL_REQUIREMENT_ENTITIES_{}_{}'.format(learning_unit_year.id,
                                                                  self.learning_component_yr.id)] = [60]
            data['VOLUME_Q1_{}_{}'.format(learning_unit_year.id, self.learning_component_yr.id)] = [10]
            data['VOLUME_Q2_{}_{}'.format(learning_unit_year.id, self.learning_component_yr.id)] = [20]
            data['VOLUME_TOTAL_{}_{}'.format(learning_unit_year.id, self.learning_component_yr.id)] = [30]
            data['PLANNED_CLASSES_{}_{}'.format(learning_unit_year.id, self.learning_component_yr.id)] = [2]
        return data

    @staticmethod
    def _get_volumes_wrong_data(learning_unit_year, learning_component_year):
        return {
            'VOLUME_TOTAL_REQUIREMENT_ENTITIES_{}_{}'.format(learning_unit_year.id, learning_component_year.id): [60],
            'VOLUME_Q1_{}_{}'.format(learning_unit_year.id, learning_component_year.id): [15],
            'VOLUME_Q2_{}_{}'.format(learning_unit_year.id, learning_component_year.id): [20],
            'VOLUME_TOTAL_{}_{}'.format(learning_unit_year.id, learning_component_year.id): [30],
            'PLANNED_CLASSES_{}_{}'.format(learning_unit_year.id, learning_component_year.id): [2]
        }

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
        self.assertEqual(base.business.learning_unit.prepare_xls_content([]), [])

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

        response = self.client.get(reverse(learning_unit_pedagogy, args=[learning_unit_year.pk]))

        self.assertTemplateUsed(response, 'learning_unit/pedagogy.html')

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

    def test_learning_unit_attributions(self):
        learning_unit_yr = LearningUnitYearFactory()

        response = self.client.get(reverse(learning_unit_attributions, args=[learning_unit_yr.id]))

        self.assertTemplateUsed(response, 'learning_unit/attributions.html')

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
        response = self.client.post(reverse('learning_unit_specifications_edit',
                                            kwargs={'learning_unit_year_id': learning_unit_year.id}))

        expected_redirection = reverse("learning_unit_specifications",
                                       kwargs={'learning_unit_year_id': learning_unit_year.id})
        self.assertRedirects(response, expected_redirection, fetch_redirect_response=False)


class TestCreateXls(TestCase):
    def setUp(self):
        self.learning_unit_year = LearningUnitYearFactory(learning_container_year=LearningContainerYearFactory(),
                                                          acronym="LOSI1452")
        self.requirement_entity_container = EntityContainerYearFactory(
            learning_container_year=self.learning_unit_year.learning_container_year,
            type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        self.allocation_entity_container = EntityContainerYearFactory(
            learning_container_year=self.learning_unit_year.learning_container_year,
            type=entity_container_year_link_type.ALLOCATION_ENTITY)

        self.user = UserFactory()

    @mock.patch("osis_common.document.xls_build.generate_xls")
    def test_generate_xls_data_with_no_data(self, mock_generate_xls):
        learning_unit_business.create_xls(self.user, [], None)
        expected_argument = _generate_xls_build_parameter([], self.user)
        mock_generate_xls.assert_called_with(expected_argument, None)

    @mock.patch("osis_common.document.xls_build.generate_xls")
    def test_generate_xls_data_with_a_learning_unit(self, mock_generate_xls):
        a_form = LearningUnitYearForm({"acronym": self.learning_unit_year.acronym}, service_course_search=False)
        self.assertTrue(a_form.is_valid())
        found_learning_units = a_form.get_activity_learning_units()
        learning_unit_business.create_xls(self.user, found_learning_units, None)
        xls_data = [[self.learning_unit_year.academic_year.name, self.learning_unit_year.acronym,
                     self.learning_unit_year.complete_title,
                     xls_build.translate(self.learning_unit_year.learning_container_year.container_type),
                     xls_build.translate(self.learning_unit_year.subtype), None, None, self.learning_unit_year.credits,
                     xls_build.translate(self.learning_unit_year.status)]]
        expected_argument = _generate_xls_build_parameter(xls_data, self.user)
        mock_generate_xls.assert_called_with(expected_argument, None)


def _generate_xls_build_parameter(xls_data, user):
    titles = learning_unit_titles_part1()
    titles.extend(learning_unit_titles_part2())
    return {
        xls_build.LIST_DESCRIPTION_KEY: _(learning_unit_business.XLS_DESCRIPTION),
        xls_build.FILENAME_KEY: _(learning_unit_business.XLS_FILENAME),
        xls_build.USER_KEY: user.username,
        xls_build.WORKSHEETS_DATA: [{
            xls_build.CONTENT_KEY: xls_data,
            xls_build.HEADER_TITLES_KEY: titles,
            xls_build.WORKSHEET_TITLE_KEY: _(learning_unit_business.WORKSHEET_TITLE),
            xls_build.STYLED_CELLS: None,
            xls_build.COLORED_ROWS: None,
        }]
    }


class TestLearningUnitComponents(TestCase):
    def setUp(self):
        self.academic_years = GenerateAcademicYear(start_year=2010, end_year=2020).academic_years
        self.generated_container = GenerateContainer(start_year=2010, end_year=2020)
        self.a_superuser = SuperUserFactory()
        self.client.force_login(self.a_superuser)
        self.person = PersonFactory(user=self.a_superuser)

    @mock.patch('base.models.program_manager.is_program_manager')
    def test_learning_unit_components(self, mock_program_manager):
        mock_program_manager.return_value = True

        learning_unit_year = self.generated_container.generated_container_years[0].learning_unit_year_full

        response = self.client.get(reverse(learning_unit_components, args=[learning_unit_year.id]))

        self.assertTemplateUsed(response, 'learning_unit/components.html')
        components = response.context['components']
        self.assertEqual(len(components), 4)

        for component in components:
            self.assertIn(component['learning_component_year'],
                          self.generated_container.generated_container_years[0].list_components)

            volumes = component['volumes']
            self.assertEqual(volumes['VOLUME_Q1'], None)
            self.assertEqual(volumes['VOLUME_Q2'], None)


class TestLearningAchievements(TestCase):
    def setUp(self):
        self.academic_year = create_current_academic_year()
        self.learning_unit_year = LearningUnitYearFactory(
            academic_year=self.academic_year,
            subtype=learning_unit_year_subtypes.FULL
        )

        self.code_languages = ["FR", "EN", "IT"]
        for code_language in self.code_languages:
            language = LanguageFactory(code=code_language)
            LearningAchievementFactory(language=language, learning_unit_year=self.learning_unit_year)

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


class TestGetChargeRepartitionWarningMessage(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.full_luy = LearningUnitYearFullFactory()
        cls.partim_luy_1 = LearningUnitYearPartimFactory(academic_year=cls.full_luy.academic_year,
                                                         learning_container_year=cls.full_luy.learning_container_year)
        cls.partim_luy_2 = LearningUnitYearPartimFactory(academic_year=cls.full_luy.academic_year,
                                                         learning_container_year=cls.full_luy.learning_container_year)
        cls.attribution_full = AttributionNewFactory(
            learning_container_year=cls.full_luy.learning_container_year
        )
        cls.full_lecturing_component = LecturingLearningComponentYearFactory(learning_unit_year=cls.full_luy)
        cls.full_practical_component = PracticalLearningComponentYearFactory(learning_unit_year=cls.full_luy)

        cls.partim_1_lecturing_component = \
            LecturingLearningComponentYearFactory(learning_unit_year=cls.partim_luy_1)
        cls.partim_1_practical_component = \
            PracticalLearningComponentYearFactory(learning_unit_year=cls.partim_luy_1)

        cls.partim_2_lecturing_component = \
            LecturingLearningComponentYearFactory(learning_unit_year=cls.partim_luy_2)
        cls.partim_2_practical_component = \
            PracticalLearningComponentYearFactory(learning_unit_year=cls.partim_luy_2)

        cls.charge_lecturing = AttributionChargeNewFactory(
            attribution=cls.attribution_full,
            learning_component_year=cls.full_lecturing_component,
            allocation_charge=20
        )
        cls.charge_practical = AttributionChargeNewFactory(
            attribution=cls.attribution_full,
            learning_component_year=cls.full_practical_component,
            allocation_charge=20
        )

        cls.attribution_partim_1 = cls.attribution_full
        cls.attribution_partim_1.id = None
        cls.attribution_partim_1.save()

        cls.attribution_partim_2 = cls.attribution_full
        cls.attribution_partim_2.id = None
        cls.attribution_partim_2.save()

    def setUp(self):
        self.charge_lecturing_1 = AttributionChargeNewFactory(
            attribution=self.attribution_partim_1,
            learning_component_year=self.partim_1_lecturing_component,
            allocation_charge=10
        )
        self.charge_practical_1 = AttributionChargeNewFactory(
            attribution=self.attribution_partim_1,
            learning_component_year=self.partim_1_practical_component,
            allocation_charge=10
        )

        self.charge_lecturing_2 = AttributionChargeNewFactory(
            attribution=self.attribution_partim_2,
            learning_component_year=self.partim_2_lecturing_component,
            allocation_charge=10
        )
        self.charge_practical_2 = AttributionChargeNewFactory(
            attribution=self.attribution_partim_2,
            learning_component_year=self.partim_2_practical_component,
            allocation_charge=10
        )

    def test_should_not_give_warning_messages_when_volume_partim_inferior_or_equal_to_volume_parent(self):
        msgs = get_charge_repartition_warning_messages(self.full_luy.learning_container_year)

        self.assertEqual(msgs,
                         [])

    def test_should_not_fail_when_no_charges(self):
        self.charge_lecturing_1.allocation_charge = None
        self.charge_lecturing_1.save()
        self.charge_lecturing_2.allocation_charge = None
        self.charge_lecturing_2.save()
        self.charge_practical_1.allocation_charge = None
        self.charge_practical_1.save()
        self.charge_practical_2.allocation_charge = None
        self.charge_practical_2.save()

        msgs = get_charge_repartition_warning_messages(self.full_luy.learning_container_year)

        self.assertEqual(msgs,
                         [])

    def test_should_give_warning_messages_when_volume_partim_superior_to_volume_parent(self):
        self.charge_lecturing_1.allocation_charge = 50
        self.charge_lecturing_1.save()

        msgs = get_charge_repartition_warning_messages(self.full_luy.learning_container_year)
        tutor_name = Person.get_str(self.attribution_full.tutor.person.first_name,
                                    self.attribution_full.tutor.person.middle_name,
                                    self.attribution_full.tutor.person.last_name)
        tutor_name_with_function = "{} ({})".format(tutor_name, _(self.attribution_full.get_function_display()))
        self.assertListEqual(msgs, [_("The sum of volumes for the partims for professor %(tutor)s is superior to the "
                                      "volume of parent learning unit for this professor") % {
                                        "tutor": tutor_name_with_function}])


class TestLearningUnitProposalComparison(TestCase):
    def setUp(self):
        self.user = SuperUserFactory()
        PersonFactory(user=self.user)
        self.client.force_login(self.user)
        self.current_academic_year = create_current_academic_year()
        an_organization = OrganizationFactory(type=organization_type.MAIN)
        learning_container_year = LearningContainerYearFactory(
            academic_year=self.current_academic_year,
            container_type=learning_container_year_types.COURSE,
            common_title="common_title",
            type_declaration_vacant=DO_NOT_ASSIGN
        )
        self.learning_unit_year = LearningUnitYearFakerFactory(
            credits=5,
            subtype=learning_unit_year_subtypes.FULL,
            academic_year=self.current_academic_year,
            learning_container_year=learning_container_year,
            campus=CampusFactory(organization=an_organization, is_administration=True),
            periodicity=learning_unit_year_periodicity.BIENNIAL_ODD
        )

        self.previous_academic_year = AcademicYearFactory(year=self.current_academic_year.year - 1)
        self.previous_learning_container_year = LearningContainerYearFactory(
            academic_year=self.previous_academic_year,
            container_type=learning_container_year_types.COURSE,
            common_title="previous_common_title",
            type_declaration_vacant=DO_NOT_ASSIGN,
            learning_container=self.learning_unit_year.learning_container_year.learning_container
        )
        self.previous_learning_unit_year = LearningUnitYearFakerFactory(
            credits=5,
            subtype=learning_unit_year_subtypes.FULL,
            academic_year=self.previous_academic_year,
            learning_container_year=self.previous_learning_container_year,
            periodicity=learning_unit_year_periodicity.BIENNIAL_ODD,
            learning_unit=self.learning_unit_year.learning_unit
        )
        self.next_academic_year = AcademicYearFactory(year=self.current_academic_year.year + 1)
        self.next_learning_container_year = LearningContainerYearFactory(
            academic_year=self.next_academic_year,
            container_type=learning_container_year_types.COURSE,
            common_title="next_common_title",
            type_declaration_vacant=DO_NOT_ASSIGN,
            learning_container=self.learning_unit_year.learning_container_year.learning_container
        )
        self.next_learning_unit_year = LearningUnitYearFakerFactory(
            credits=5,
            subtype=learning_unit_year_subtypes.FULL,
            academic_year=self.next_academic_year,
            learning_container_year=self.next_learning_container_year,
            periodicity=learning_unit_year_periodicity.BIENNIAL_ODD,
            learning_unit=self.learning_unit_year.learning_unit
        )
        today = datetime.date.today()

        an_entity = EntityFactory(organization=an_organization)
        self.entity_version = EntityVersionFactory(entity=an_entity, entity_type=entity_type.SCHOOL, start_date=today,
                                                   end_date=today.replace(year=today.year + 1))
        self.learning_component_year_lecturing = LearningComponentYearFactory(
            type=learning_component_year_type.LECTURING,
            acronym="TP",
            learning_unit_year=self.learning_unit_year
        )
        self.learning_component_year_practical = LearningComponentYearFactory(
            type=learning_component_year_type.PRACTICAL_EXERCISES,
            acronym="PP",
            learning_unit_year=self.learning_unit_year
        )
        self.entity_container_year = EntityContainerYearFactory(
            learning_container_year=self.learning_unit_year.learning_container_year,
            type=entity_container_year_link_type.REQUIREMENT_ENTITY
        )

        initial_data_expected = {
            "learning_container_year": {
                "id": self.learning_unit_year.learning_container_year.id,
                "acronym": self.learning_unit_year.acronym,
                "common_title": self.learning_unit_year.learning_container_year.common_title,
                "common_title_english": self.learning_unit_year.learning_container_year.common_title_english,
                "container_type": self.learning_unit_year.learning_container_year.container_type,
                "in_charge": self.learning_unit_year.learning_container_year.in_charge,
                "type_declaration_vacant": self.learning_unit_year.learning_container_year.type_declaration_vacant
            },
            "learning_unit_year": {
                "id": self.learning_unit_year.id,
                "acronym": self.learning_unit_year.acronym,
                "specific_title": self.learning_unit_year.specific_title,
                "specific_title_english": self.learning_unit_year.specific_title_english,
                "internship_subtype": self.learning_unit_year.internship_subtype,
                "credits": self.learning_unit_year.credits,
                "quadrimester": self.learning_unit_year.quadrimester,
                "status": self.learning_unit_year.status,
                "language": self.learning_unit_year.language.pk,
                "campus": self.learning_unit_year.campus.id,
                "periodicity": self.learning_unit_year.periodicity,
                "attribution_procedure": self.learning_unit_year.attribution_procedure
            },
            "learning_unit": {
                "id": self.learning_unit_year.learning_unit.id
            },
            "entities": {
                entity_container_year_link_type.REQUIREMENT_ENTITY: self.entity_container_year.id,
                entity_container_year_link_type.ALLOCATION_ENTITY: None,
                entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1: None,
                entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_2: None
            },
            "learning_component_years": [
                {"id": self.learning_component_year_lecturing.id,
                 "type": "LECTURING",
                 "planned_classes": self.learning_component_year_lecturing.planned_classes,
                 "hourly_volume_partial_q1": self.learning_component_year_lecturing.hourly_volume_partial_q1,
                 "hourly_volume_partial_q2": self.learning_component_year_lecturing.hourly_volume_partial_q2,
                 "hourly_volume_total_annual": self.learning_component_year_lecturing.hourly_volume_total_annual
                 },
                {"id": self.learning_component_year_practical.id,
                 "type": "PRACTICAL_EXERCISES",
                 "planned_classes": self.learning_component_year_practical.planned_classes,
                 "hourly_volume_partial_q1": self.learning_component_year_practical.hourly_volume_partial_q1,
                 "hourly_volume_partial_q2": self.learning_component_year_practical.hourly_volume_partial_q2,
                 "hourly_volume_total_annual": self.learning_component_year_practical.hourly_volume_total_annual
                 }
            ],
            "volumes": {
                'LECTURING': {
                    'VOLUME_Q1': self.learning_component_year_lecturing.hourly_volume_partial_q1,
                    'VOLUME_Q2': self.learning_component_year_lecturing.hourly_volume_partial_q2,
                    'REAL_CLASSES': 1,
                    'VOLUME_TOTAL': self.learning_component_year_practical.hourly_volume_total_annual,
                    'PLANNED_CLASSES': self.learning_component_year_lecturing.planned_classes,
                    'VOLUME_REQUIREMENT_ENTITY': 120.0,
                    'VOLUME_TOTAL_REQUIREMENT_ENTITIES': 120.0,
                    'VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1': 0,
                    'VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2': 0
                },
                'PRACTICAL_EXERCISES': {
                    'VOLUME_Q1': 10, 'VOLUME_Q2': 10, 'REAL_CLASSES': 0, 'VOLUME_TOTAL': 20,
                    'PLANNED_CLASSES': 0, 'VOLUME_REQUIREMENT_ENTITY': 0,
                    'VOLUME_TOTAL_REQUIREMENT_ENTITIES': 0,
                    'VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1': 0,
                    'VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2': 0
                }
            }
        }
        self.learning_unit_proposal = ProposalLearningUnitFactory(learning_unit_year=self.learning_unit_year,
                                                                  initial_data=initial_data_expected,
                                                                  type=proposal_type.ProposalType.MODIFICATION.name,
                                                                  state=proposal_state.ProposalState.FACULTY.name)

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
        EntityContainerYearFactory(
            learning_container_year=self.learning_unit_year.learning_container_year,
            type=entity_container_year_link_type.ALLOCATION_ENTITY
        )
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
