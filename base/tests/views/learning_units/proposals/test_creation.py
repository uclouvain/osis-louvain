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
import datetime

from django.contrib.auth.models import Permission
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from waffle.testutils import override_flag

from base.forms.learning_unit.learning_unit_create import LearningUnitModelForm, LearningUnitYearModelForm, \
    LearningContainerYearModelForm
from base.forms.learning_unit_proposal import ProposalLearningUnitForm, CreationProposalBaseForm
from base.models.academic_year import AcademicYear
from base.models.enums import learning_unit_year_subtypes, learning_container_year_types, organization_type, \
    entity_type, learning_unit_year_periodicity
from base.models.enums.proposal_state import ProposalState
from base.models.learning_unit_year import LearningUnitYear
from base.models.proposal_learning_unit import ProposalLearningUnit
from base.tests.factories import campus as campus_factory, \
    organization as organization_factory, person as factory_person, user as factory_user
from base.tests.factories.academic_calendar import generate_creation_or_end_date_proposal_calendars
from base.tests.factories.academic_year import get_current_year, AcademicYearFactory
from base.tests.factories.business.learning_units import GenerateAcademicYear
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.group import FacultyManagerGroupFactory
from base.tests.factories.person import CentralManagerForUEFactory
from base.tests.factories.person import FacultyManagerForUEFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.views.learning_units.proposal.create import get_proposal_learning_unit_creation_form
from reference.tests.factories.language import LanguageFactory, FrenchLanguageFactory


@override_flag('learning_unit_proposal_create', active=True)
class LearningUnitViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        today = datetime.date.today()
        FacultyManagerGroupFactory()
        cls.faculty_user = factory_user.UserFactory()
        cls.faculty_person = FacultyManagerForUEFactory(
            'can_propose_learningunit', 'can_create_learningunit',
            user=cls.faculty_user
        )
        cls.super_user = factory_user.SuperUserFactory()
        cls.person = factory_person.CentralManagerForUEFactory(user=cls.super_user)
        start_year = AcademicYearFactory(year=get_current_year())
        end_year = AcademicYearFactory(year=get_current_year() + 7)
        cls.academic_years = GenerateAcademicYear(start_year, end_year).academic_years
        cls.current_academic_year = cls.academic_years[0]
        cls.next_academic_year = cls.academic_years[1]
        generate_creation_or_end_date_proposal_calendars(cls.academic_years)

        cls.language = FrenchLanguageFactory()
        cls.organization = organization_factory.OrganizationFactory(type=organization_type.MAIN)
        cls.campus = campus_factory.CampusFactory(organization=cls.organization, is_administration=True)
        cls.entity = EntityFactory(organization=cls.organization)
        cls.entity_version = EntityVersionFactory(entity=cls.entity, entity_type=entity_type.FACULTY,
                                                  start_date=today.replace(year=1900),
                                                  end_date=None)

        PersonEntityFactory(person=cls.faculty_person, entity=cls.entity)
        PersonEntityFactory(person=cls.person, entity=cls.entity)

    def setUp(self):
        self.client.force_login(self.person.user)

    def get_valid_data(self):
        return {
            'acronym_0': 'L',
            'acronym_1': 'TAU2000',
            "subtype": learning_unit_year_subtypes.FULL,
            "container_type": learning_container_year_types.COURSE,
            "academic_year": self.academic_years[3].id,
            "status": True,
            "credits": "5",
            "campus": self.campus.id,
            "common_title": "Common UE title",
            "language": self.language.pk,
            "periodicity": learning_unit_year_periodicity.ANNUAL,
            "entity": self.entity_version.id,
            "folder_id": 1,
            "state": ProposalState.FACULTY.name,
            'requirement_entity': self.entity_version.id,
            'allocation_entity': self.entity_version.id,
            'additional_entity_1': '',

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
        }

    def test_get_proposal_learning_unit_creation_form(self):
        url = reverse(get_proposal_learning_unit_creation_form, args=[self.next_academic_year.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'learning_unit/proposal/creation.html')
        self.assertIsInstance(response.context['learning_unit_form'], LearningUnitModelForm)
        self.assertIsInstance(response.context['form_proposal'], ProposalLearningUnitForm)

    def test_get_proposal_learning_unit_creation_form_with_central_user(self):
        central_manager_person = CentralManagerForUEFactory()
        central_manager_person.user.user_permissions.add(Permission.objects.get(codename='can_propose_learningunit'))
        central_manager_person.user.user_permissions.add(Permission.objects.get(codename='can_create_learningunit'))
        self.client.force_login(central_manager_person.user)
        url = reverse(get_proposal_learning_unit_creation_form, args=[self.next_academic_year.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'learning_unit/proposal/creation.html')
        self.assertIsInstance(response.context['learning_unit_form'], LearningUnitModelForm)
        self.assertIsInstance(response.context['form_proposal'], ProposalLearningUnitForm)
        self.assertCountEqual(
            list(response.context['learning_unit_year_form'].fields['academic_year'].queryset),
            self.academic_years[:-1]  # Exclude last one because central manager cannot propose luy in n+7
        )

    def test_get_proposal_learning_unit_creation_form_with_faculty_user(self):
        self.client.force_login(self.faculty_person.user)
        url = reverse(get_proposal_learning_unit_creation_form, args=[self.next_academic_year.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'learning_unit/proposal/creation.html')
        self.assertIsInstance(response.context['learning_unit_form'], LearningUnitModelForm)
        self.assertIsInstance(response.context['form_proposal'], ProposalLearningUnitForm)
        self.assertCountEqual(
            list(response.context['learning_unit_year_form'].fields['academic_year'].queryset),
            self.academic_years[1:-1]  # Exclude first and last one because fac manager cannot propose luy in n and n+7
        )

    def test_post_proposal_learning_unit_creation_form(self):
        url = reverse(get_proposal_learning_unit_creation_form, args=[self.current_academic_year.id])
        response = self.client.post(url, data=self.get_valid_data())
        self.assertEqual(response.status_code, 302)
        count_learning_unit_year = LearningUnitYear.objects.all().count()
        self.assertEqual(count_learning_unit_year, 1)
        count_proposition_by_author = ProposalLearningUnit.objects.filter(author=self.person).count()
        self.assertEqual(count_proposition_by_author, 1)

    def test_post_proposal_learning_unit_creation_form_with_faculty_user(self):
        self.client.force_login(self.faculty_person.user)
        url = reverse(get_proposal_learning_unit_creation_form, args=[self.next_academic_year.id])
        response = self.client.post(url, data=self.get_valid_data())
        self.assertEqual(response.status_code, 302)
        count_learning_unit_year = LearningUnitYear.objects.all().count()
        self.assertEqual(count_learning_unit_year, 1)
        count_proposition_by_author = ProposalLearningUnit.objects.filter(author=self.faculty_person).count()
        self.assertEqual(count_proposition_by_author, 1)

    def get_invalid_data(self):
        faultydict = dict(self.get_valid_data())
        faultydict["acronym_1"] = "T2"
        faultydict["acronym_0"] = "A"
        return faultydict

    def test_proposal_learning_unit_add_with_invalid_data(self):
        url = reverse(get_proposal_learning_unit_creation_form, args=[self.current_academic_year.id])
        response = self.client.post(url, data=self.get_invalid_data())
        self.assertEqual(response.status_code, 200)
        count_learning_unit_year = LearningUnitYear.objects.all().count()
        self.assertEqual(count_learning_unit_year, 0)
        count_proposition_by_author = ProposalLearningUnit.objects.filter(author=self.person).count()
        self.assertEqual(count_proposition_by_author, 0)

    def get_empty_required_fields(self):
        faculty_dict = dict(self.get_valid_data())
        faculty_dict["acronym_0"] = ""
        faculty_dict["container_type"] = ""
        faculty_dict["campus"] = ""
        faculty_dict["periodicity"] = ""
        faculty_dict["language"] = ""
        return faculty_dict

    def get_empty_title_fields(self):
        faculty_dict = dict(self.get_valid_data())
        faculty_dict["specific_title"] = None
        faculty_dict["common_title"] = None
        return faculty_dict

    def test_proposal_learning_unit_form_with_empty_fields(self):
        learning_unit_form = CreationProposalBaseForm(self.get_empty_required_fields(), person=self.person)
        self.assertFalse(learning_unit_form.is_valid(), learning_unit_form.errors)
        luy_errors = learning_unit_form.learning_unit_form_container.forms[LearningUnitYearModelForm].errors
        lcy_errors = learning_unit_form.learning_unit_form_container.forms[LearningContainerYearModelForm].errors

        self.assertEqual(luy_errors['acronym'], [_('This field is required.')])
        self.assertEqual(lcy_errors['container_type'], [_('This field is required.')])
        self.assertEqual(luy_errors['periodicity'], [_('This field is required.')])
        self.assertEqual(luy_errors['language'], [_('This field is required.')])
        self.assertEqual(luy_errors['campus'], [_('This field is required.')])

    def test_proposal_learning_unit_form_with_empty_title_fields(self):
        learning_unit_form = CreationProposalBaseForm(self.get_empty_title_fields(), person=self.person)
        self.assertFalse(learning_unit_form.is_valid(), learning_unit_form.errors)
        lcy_errors = learning_unit_form.learning_unit_form_container.forms[LearningContainerYearModelForm].errors
        self.assertEqual(lcy_errors['common_title'], [_('You must either set the common title or the specific title')])

    def test_proposal_learning_unit_add_with_valid_data_for_faculty_manager(self):
        learning_unit_form = CreationProposalBaseForm(self.get_valid_data(), person=self.faculty_person)
        self.assertTrue(learning_unit_form.is_valid(), learning_unit_form.errors)
        self.client.force_login(self.faculty_person.user)
        url = reverse(get_proposal_learning_unit_creation_form, args=[self.current_academic_year.id])
        response = self.client.post(url, data=self.get_valid_data())
        self.assertEqual(response.status_code, 302)
        count_learning_unit_year = LearningUnitYear.objects.all().count()
        self.assertEqual(count_learning_unit_year, 1)
        count_proposition_by_author = ProposalLearningUnit.objects.filter(author=self.faculty_person).count()
        self.assertEqual(count_proposition_by_author, 1)

    def test_restrict_type_choice_for_proposal_creation(self):
        full_form = CreationProposalBaseForm(self.get_valid_data(), person=self.faculty_person)

        self.assertEqual(full_form.fields['container_type'].choices,
                         [(None, '---------'),
                          ('COURSE', 'Cours'),
                          ('DISSERTATION', 'Mémoire'),
                          ('INTERNSHIP', 'Stage')]
                         )

    def test_academic_year_from_form_equal_to_data(self):
        full_form = CreationProposalBaseForm(self.get_valid_data(),
                                             person=self.faculty_person,
                                             default_ac_year=AcademicYear.objects.get(
                                                 pk=self.get_valid_data()['academic_year']))

        self.assertEqual(self.get_valid_data()['academic_year'],
                         full_form.learning_unit_form_container.academic_year.id)

    def test_academic_year_default_from_form_equal(self):
        full_form = CreationProposalBaseForm(self.get_valid_data(),
                                             person=self.faculty_person)

        self.assertEqual(self.next_academic_year.id,
                         full_form.learning_unit_form_container.academic_year.id)
