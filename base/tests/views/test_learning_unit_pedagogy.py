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
from io import BytesIO
from unittest.mock import patch

from django.contrib import messages
from django.http import HttpResponseNotAllowed
from django.http.response import HttpResponseForbidden, HttpResponseRedirect, HttpResponse
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from openpyxl import load_workbook

from base.business.learning_unit import CMS_LABEL_PEDAGOGY_FR_ONLY
from base.models.enums import academic_calendar_type, entity_type
from base.models.enums import organization_type
from base.models.enums.learning_unit_year_subtypes import FULL
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.business.learning_units import GenerateAcademicYear
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import FacultyManagerFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from base.tests.factories.teaching_material import TeachingMaterialFactory
from base.tests.factories.user import UserFactory
from base.tests.factories.utils.get_messages import get_messages_from_response
from base.views.learning_units.pedagogy.update import learning_unit_pedagogy_edit
from base.views.learning_units.search.common import SearchTypes
from cms.enums import entity_name
from cms.enums.entity_name import LEARNING_UNIT_YEAR
from cms.tests.factories.text_label import TextLabelFactory
from cms.tests.factories.translated_text import TranslatedTextFactory


class LearningUnitPedagogyTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        now = datetime.datetime.now()

        cls.academic_year = create_current_academic_year()
        cls.old_academic_year = AcademicYearFactory(year=cls.academic_year.year - 1)
        cls.next_academic_year = AcademicYearFactory(year=cls.academic_year.year + 1)
        cls.previous_academic_year = GenerateAcademicYear(
            cls.old_academic_year,
            cls.old_academic_year
        ).academic_years[0]
        AcademicCalendarFactory(
            academic_year=cls.previous_academic_year,
            start_date=now - datetime.timedelta(days=5),
            end_date=now + datetime.timedelta(days=15),
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION
        )

        cls.requirement_entity_version = EntityVersionFactory(
            entity__organization__type=organization_type.MAIN,
            start_date=now,
            end_date=datetime.datetime(now.year + 1, 9, 15),
            entity_type=entity_type.INSTITUTE
        )
        cls.learning_unit_year = LearningUnitYearFactory(
            acronym="LBIR1100",
            academic_year=cls.academic_year,
            learning_container_year__academic_year=cls.academic_year,
            learning_container_year__acronym="LBIR1100",
            learning_container_year__requirement_entity=cls.requirement_entity_version.entity
        )
        cls.url = reverse('learning_units_summary')
        cls.faculty_person = FacultyManagerFactory('can_access_learningunit', 'can_edit_learningunit_pedagogy')
        PersonEntityFactory(person=cls.faculty_person, entity=cls.requirement_entity_version.entity)

    def setUp(self):
        self.client.force_login(self.faculty_person.user)

    def test_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_user_has_no_right_to_access_summary_learning_unit(self):
        user_with_no_rights = UserFactory()
        self.client.force_login(user_with_no_rights)

        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_learning_units_summary_list_filter_academic_year(self):
        response = self.client.get(self.url, data={'academic_year': self.learning_unit_year.academic_year.pk})

        self.assertTemplateUsed(response, 'learning_unit/search/description_fiche.html')
        self.assertTrue(response.context['is_faculty_manager'])
        self.assertEqual(response.context['search_type'], SearchTypes.SUMMARY_LIST.value)
        self.assertEqual(response.context['learning_units_count'], 1)

        self.assertEqual(response.context['object_list'].first(), self.learning_unit_year)

    def test_learning_units_summary_list_filter_on_requirement_entity(self):
        now = datetime.datetime.now()
        another_requirement_entity_version = EntityVersionFactory(
            entity__organization__type=organization_type.MAIN,
            start_date=now,
            end_date=datetime.datetime(now.year + 1, 9, 15),
            entity_type=entity_type.SCHOOL,
            parent=self.requirement_entity_version.entity
        )
        LearningUnitYearFactory(
            acronym="LDROI1500",
            academic_year=self.academic_year,
            learning_container_year__academic_year=self.academic_year,
            learning_container_year__acronym="LDROI1500",
            learning_container_year__requirement_entity=another_requirement_entity_version.entity
        )

        # Without ent. sub
        response = self.client.get(
            self.url,
            data={
                'academic_year': self.learning_unit_year.academic_year.pk,
                'requirement_entity': self.requirement_entity_version.acronym,
                'with_entity_subordinated': False
            }
        )
        self.assertEqual(response.context['learning_units_count'], 1)
        self.assertEqual(response.context['object_list'].first(), self.learning_unit_year)

        # With ent. sub
        response = self.client.get(
            self.url,
            data={
                'academic_year': self.learning_unit_year.academic_year.pk,
                'requirement_entity': self.requirement_entity_version.acronym,
                'with_entity_subordinated': True
            }
        )
        self.assertEqual(response.context['learning_units_count'], 2)

    @patch('base.business.learning_units.perms.can_edit_summary_locked_field')
    def test_tab_active_url(self, mock_can_edit_summary_locked):
        url = reverse("learning_unit_pedagogy", args=[self.learning_unit_year.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTrue("tab_active" in response.context)
        self.assertEqual(response.context["tab_active"], 'learning_unit_pedagogy')

        url_tab_active = reverse(response.context["tab_active"], args=[self.learning_unit_year.id])
        response = self.client.get(url_tab_active)
        self.assertEqual(response.status_code, HttpResponse.status_code)


class LearningUnitPedagogyExportXLSTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        now = datetime.datetime.now()
        cls.academic_years = AcademicYearFactory.produce(number_past=5, number_future=5)

        cls.academic_year = cls.academic_years[5]
        cls.old_academic_year = cls.academic_years[4]
        cls.next_academic_year = cls.academic_years[5]
        cls.previous_academic_year = cls.academic_years[4]
        AcademicCalendarFactory(
            academic_year=cls.previous_academic_year,
            start_date=now - datetime.timedelta(days=5),
            end_date=now + datetime.timedelta(days=15),
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION
        )

        cls.requirement_entity_version = EntityVersionFactory(
            entity__organization__type=organization_type.MAIN,
            start_date=now,
            end_date=datetime.datetime(now.year + 1, 9, 15),
            entity_type=entity_type.INSTITUTE
        )

        cls.url = reverse('learning_units_summary')
        cls.faculty_person = FacultyManagerFactory('can_access_learningunit', 'can_edit_learningunit_pedagogy')
        PersonEntityFactory(person=cls.faculty_person, entity=cls.requirement_entity_version.entity)

        # Generate data for XLS export
        cls.learning_unit_year_with_mandatory_teaching_materials = LearningUnitYearFactory(
            acronym="LBIR1100",
            academic_year=cls.academic_year,
            learning_container_year__academic_year=cls.academic_year,
            learning_container_year__acronym="LBIR1100",
            learning_container_year__requirement_entity=cls.requirement_entity_version.entity
        )
        TeachingMaterialFactory(
            learning_unit_year=cls.learning_unit_year_with_mandatory_teaching_materials,
            title="Magic wand",
            mandatory=True,
        )
        TeachingMaterialFactory(
            learning_unit_year=cls.learning_unit_year_with_mandatory_teaching_materials,
            title="Broomsticks",
            mandatory=False,
        )

        cls.learning_unit_year_without_mandatory_teaching_materials = LearningUnitYearFactory(
            acronym="LDROI1600",
            academic_year=cls.academic_year,
            learning_container_year__academic_year=cls.academic_year,
            learning_container_year__acronym="LDROI1600",
            learning_container_year__requirement_entity=cls.requirement_entity_version.entity
        )
        TeachingMaterialFactory(
            learning_unit_year=cls.learning_unit_year_without_mandatory_teaching_materials,
            title="cauldron",
            mandatory=False,
        )

    def setUp(self):
        self.client.force_login(self.faculty_person.user)

    def test_learning_units_summary_list_by_client_xls(self):
        TranslatedTextFactory(
            text_label=TextLabelFactory(label='bibliography'),
            entity=LEARNING_UNIT_YEAR,
            text="<ul><li>Test</li></ul>",
            reference=self.learning_unit_year_with_mandatory_teaching_materials.pk,
            language='fr-be'
        )
        TranslatedTextFactory(
            text_label=TextLabelFactory(label='online_resources'),
            entity=LEARNING_UNIT_YEAR,
            text="<a href='test_url'>TestURL</a>",
            reference=self.learning_unit_year_with_mandatory_teaching_materials.pk,
            language='fr-be'
        )
        TranslatedTextFactory(
            text_label=TextLabelFactory(label='online_resources'),
            entity=LEARNING_UNIT_YEAR,
            text="<a href='test_url'>TestURL EN</a>",
            reference=self.learning_unit_year_with_mandatory_teaching_materials.pk,
            language='en'
        )

        response = self.client.get(self.url, data={
            'academic_year': self.academic_year.pk,
            'xls_status': 'xls_teaching_material'
        })

        # The server returned the xls file
        self.assertEqual(response.status_code, HttpResponse.status_code)
        wb = load_workbook(BytesIO(response.content), read_only=True)

        sheet = wb.active
        data = sheet['A1': 'G3']

        # Check the first row content
        titles = next(data)
        title_values = list(t.value for t in titles)
        self.assertEqual(title_values, [
            str(_('code')).title(),
            str(_('Title')),
            str(_('Req. Entity')).title(),
            str(_('bibliography')).title(),
            str(_('teaching materials')).title(),
            str("{} - Fr-Be".format(_('online resources'))).title(),
            str("{} - En".format(_('online resources'))).title(),
        ])

        # Check data from the luy
        first_luy = next(data)
        first_luy_values = list(t.value for t in first_luy)
        self.assertEqual(first_luy_values, [
            self.learning_unit_year_with_mandatory_teaching_materials.acronym,
            self.learning_unit_year_with_mandatory_teaching_materials.complete_title,
            str(self.learning_unit_year_with_mandatory_teaching_materials.requirement_entity),
            "Test\n",
            "Magic wand",
            "TestURL - [test_url] \n",
            "TestURL EN - [test_url] \n"
        ])

        # The second luy has no mandatory teaching material
        with self.assertRaises(StopIteration):
            next(data)

    def test_learning_units_summary_list_by_client_xls_empty(self):
        response = self.client.get(self.url, data={
            'acronym': self.learning_unit_year_without_mandatory_teaching_materials.acronym,
            'academic_year': self.academic_year,
            'xls_status': 'xls_teaching_material'
        })

        self.assertEqual(response.status_code, HttpResponse.status_code)


class LearningUnitPedagogyEditTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        now = datetime.datetime.now()
        cls.academic_year = create_current_academic_year()
        cls.previous_academic_year = AcademicYearFactory(year=cls.academic_year.year - 1)
        cls.next_academic_year = AcademicYearFactory(year=cls.academic_year.year + 1)
        AcademicCalendarFactory(
            academic_year=cls.previous_academic_year,
            start_date=now - datetime.timedelta(days=5),
            end_date=now + datetime.timedelta(days=15),
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION
        )

        cls.requirement_entity_version = EntityVersionFactory(
            entity__organization__type=organization_type.MAIN,
            start_date=now,
            end_date=datetime.datetime(now.year + 1, 9, 15),
            entity_type=entity_type.INSTITUTE
        )
        cls.learning_unit_year = LearningUnitYearFactory(
            acronym="LBIR1100",
            academic_year=cls.academic_year,
            learning_container_year__academic_year=cls.academic_year,
            learning_container_year__acronym="LBIR1100",
            learning_container_year__requirement_entity=cls.requirement_entity_version.entity
        )
        cls.url = reverse(learning_unit_pedagogy_edit, kwargs={'learning_unit_year_id': cls.learning_unit_year.pk})
        cls.faculty_person = FacultyManagerFactory('can_access_learningunit', 'can_edit_learningunit_pedagogy')
        PersonEntityFactory(person=cls.faculty_person, entity=cls.requirement_entity_version.entity)

    def setUp(self):
        self.cms = TranslatedTextFactory(
            entity=entity_name.LEARNING_UNIT_YEAR,
            reference=self.learning_unit_year.pk,
            language='fr-be',
            text='Some random text',
            text_label__entity=entity_name.LEARNING_UNIT_YEAR,
            text_label__label='bibliography',
        )
        self.client.force_login(self.faculty_person.user)

    def test_learning_unit_pedagogy_edit(self):
        response = self.client.get(self.url, data={'label': 'bibliography', 'language': 'fr-be'})

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'learning_unit/pedagogy_edit.html')
        self.assertTemplateUsed(response, 'learning_unit/blocks/modal/modal_pedagogy_edit.html')
        self.assertEqual(response.context["cms_label_pedagogy_fr_only"], CMS_LABEL_PEDAGOGY_FR_ONLY)
        self.assertEqual(response.context["label_name"], 'bibliography')

    def test_learning_unit_pedagogy_edit_post(self):
        msg = self._post_learning_unit_pedagogy()
        self.assertEqual(msg[0].get('message'), "{}.".format(_("The learning unit has been updated")))
        self.assertEqual(msg[0].get('level'), messages.SUCCESS)

    def test_learning_unit_pedagogy_edit_post_with_postponement(self):
        LearningUnitYearFactory(
            acronym="LBIR1100",
            academic_year=self.next_academic_year,
            learning_container_year__academic_year=self.next_academic_year,
            learning_container_year__acronym="LBIR1100",
            learning_container_year__requirement_entity=self.requirement_entity_version.entity,
            learning_unit=self.learning_unit_year.learning_unit
        )
        msg = self._post_learning_unit_pedagogy()
        expected_message = "{} {}.".format(
            _("The learning unit has been updated"),
            _("and postponed until %(year)s") % {
                "year": self.next_academic_year
            }
        )
        self.assertEqual(msg[0].get('message'), expected_message)
        self.assertEqual(msg[0].get('level'), messages.SUCCESS)

    def test_learning_unit_pedagogy_edit_post_with_postponement_and_proposal(self):
        LearningUnitYearFactory(
            acronym="LBIR1100",
            academic_year=self.next_academic_year,
            learning_container_year__academic_year=self.next_academic_year,
            learning_container_year__acronym="LBIR1100",
            learning_container_year__requirement_entity=self.requirement_entity_version.entity,
            learning_unit=self.learning_unit_year.learning_unit
        )
        proposal = ProposalLearningUnitFactory(learning_unit_year=self.learning_unit_year)
        msg = self._post_learning_unit_pedagogy()
        expected_message = "{}. {}.".format(
            _("The learning unit has been updated"),
            _("The learning unit is in proposal, the report from %(proposal_year)s will be done at consolidation") % {
                'proposal_year': proposal.learning_unit_year.academic_year
            }
        )
        self.assertEqual(msg[0].get('message'), expected_message)
        self.assertEqual(msg[0].get('level'), messages.SUCCESS)

    def test_learning_unit_pedagogy_edit_post_with_proposal(self):
        proposal = ProposalLearningUnitFactory(learning_unit_year=self.learning_unit_year)
        msg = self._post_learning_unit_pedagogy()
        expected_message = "{}. {}.".format(
            _("The learning unit has been updated"),
            _("The learning unit is in proposal, the report from %(proposal_year)s will be done at consolidation") % {
                'proposal_year': proposal.learning_unit_year.academic_year
            }
        )
        self.assertEqual(msg[0].get('message'), expected_message)
        self.assertEqual(msg[0].get('level'), messages.SUCCESS)

    def test_learning_unit_pedagogy_edit_post_with_proposal_previous_year(self):
        previous_luy = LearningUnitYearFactory(
            acronym="LBIR1100",
            academic_year=self.previous_academic_year,
            learning_container_year__academic_year=self.previous_academic_year,
            learning_container_year__acronym="LBIR1100",
            learning_container_year__requirement_entity=self.requirement_entity_version.entity,
            learning_unit=self.learning_unit_year.learning_unit
        )
        ProposalLearningUnitFactory(learning_unit_year=previous_luy)
        msg = self._post_learning_unit_pedagogy()
        expected_message = "{}.".format(_("The learning unit has been updated"))
        self.assertEqual(msg[0].get('message'), expected_message)
        self.assertEqual(msg[0].get('level'), messages.SUCCESS)

    def test_learning_unit_pedagogy_edit_post_with_proposal_next_year(self):
        next_luy = LearningUnitYearFactory(
            acronym="LBIR1100",
            academic_year=self.next_academic_year,
            learning_container_year__academic_year=self.next_academic_year,
            learning_container_year__acronym="LBIR1100",
            learning_container_year__requirement_entity=self.requirement_entity_version.entity,
            learning_unit=self.learning_unit_year.learning_unit
        )
        proposal = ProposalLearningUnitFactory(learning_unit_year=next_luy)
        msg = self._post_learning_unit_pedagogy()
        expected_message = "{} ({}).".format(
            _("The learning unit has been updated"),
            _("the report has not been done from %(proposal_year)s because the LU is in proposal") % {
                'proposal_year': proposal.learning_unit_year.academic_year
            }
        )
        self.assertEqual(msg[0].get('message'), expected_message)
        self.assertEqual(msg[0].get('level'), messages.SUCCESS)

    def _post_learning_unit_pedagogy(self):
        response = self.client.post(self.url, data={
            'cms_id': self.cms.pk,
            'trans_text': 'test',
            'learning_unit_year': self.learning_unit_year
        })
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)
        msg = get_messages_from_response(response)
        return msg


class LearningUnitPedagogySummaryLockedTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        cls.faculty_person = FacultyManagerFactory('can_access_learningunit')
        cls.learning_unit_year = LearningUnitYearFactory(
            academic_year=cls.current_academic_year,
            learning_container_year__academic_year=cls.current_academic_year,
            subtype=FULL
        )
        cls.url = reverse('learning_unit_pedagogy_toggle_summary_locked',
                          kwargs={'learning_unit_year_id': cls.learning_unit_year.pk})

    def setUp(self):
        self.client.force_login(self.faculty_person.user)

    def test_toggle_summary_locked_case_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_toggle_summary_locked_case_method_not_allowed(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseNotAllowed.status_code)

    @patch('base.business.learning_units.perms.can_edit_summary_locked_field')
    def test_toggle_summary_locked_case_cannot_edit_summary_locked(self, mock_can_edit_summary_locked):
        mock_can_edit_summary_locked.return_value = False
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    @patch('base.views.learning_units.pedagogy.update.display_success_messages')
    @patch('base.business.learning_units.perms.can_edit_summary_locked_field')
    def test_toggle_summary_locked_case_success(self, mock_can_edit_summary_locked, mock_diplay_success_message):
        mock_can_edit_summary_locked.return_value = True
        self.learning_unit_year.summary_locked = True
        self.learning_unit_year.save()

        response = self.client.post(self.url, follow=False)
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)
        self.assertTrue(mock_diplay_success_message.called)
        expected_redirection = reverse("learning_unit_pedagogy",
                                       kwargs={'learning_unit_year_id': self.learning_unit_year.pk})
        self.assertRedirects(response, expected_redirection)
        self.learning_unit_year.refresh_from_db()
        self.assertFalse(self.learning_unit_year.summary_locked)
