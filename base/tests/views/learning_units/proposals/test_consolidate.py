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
import random
from unittest import mock
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.http import HttpResponseNotAllowed, HttpResponseForbidden, HttpResponseNotFound
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.reverse import reverse
from waffle.testutils import override_flag

import base.models as mdl_base
from base.business.learning_unit import CMS_LABEL_PEDAGOGY_FR_AND_EN, CMS_LABEL_PEDAGOGY_FR_ONLY, \
    CMS_LABEL_SPECIFICATIONS, CMS_LABEL_SUMMARY
from base.business.learning_units.edition import _descriptive_fiche_and_achievements_update
from base.models.enums import proposal_state, learning_unit_year_subtypes, \
    proposal_type, learning_container_year_types
from base.tests.factories.academic_year import AcademicYearFactory, get_current_year
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_achievement import LearningAchievementFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from cms.models.translated_text import TranslatedText
from cms.tests.factories.text_label import TextLabelFactory
from cms.tests.factories.translated_text import TranslatedTextFactory
from reference.tests.factories.language import LanguageFactory

NEW_TEXT = "new text begins in  {}"
EN_CODE_LANGUAGE = 'EN'
FR_CODE_LANGUAGE = 'FR'


@override_flag('learning_unit_proposal_delete', active=True)
class TestConsolidate(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = AcademicYearFactory.produce_in_future(quantity=5)
        cls.current_academic_year = cls.academic_years[0]

        cls.proposal = ProposalLearningUnitFactory(
            type=proposal_type.ProposalType.MODIFICATION.name,
            state=proposal_state.ProposalState.ACCEPTED.name,
            learning_unit_year__subtype=learning_unit_year_subtypes.FULL,
            learning_unit_year__academic_year=cls.current_academic_year,
            learning_unit_year__learning_unit__start_year=cls.current_academic_year,
            learning_unit_year__learning_container_year__academic_year=cls.current_academic_year,
            learning_unit_year__learning_container_year__requirement_entity=EntityVersionFactory().entity,
        )
        cls.learning_unit_year = cls.proposal.learning_unit_year

        cls.person = PersonFactory()
        cls.person.user.user_permissions.add(Permission.objects.get(codename="can_access_learningunit"))
        cls.person.user.user_permissions.add(Permission.objects.get(codename="can_consolidate_learningunit_proposal"))

        person_entity = PersonEntityFactory(person=cls.person,
                                            entity=cls.learning_unit_year.learning_container_year.requirement_entity)
        EntityVersionFactory(entity=person_entity.entity)
        cls.url = reverse("learning_unit_consolidate_proposal",
                          kwargs={'learning_unit_year_id': cls.learning_unit_year.id})
        cls.post_data = {"learning_unit_year_id": cls.learning_unit_year.id}

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_login_required(self):
        self.client.logout()

        response = self.client.post(self.url, data=self.post_data)

        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_accepts_only_post_request(self):
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "method_not_allowed.html")
        self.assertEqual(response.status_code, HttpResponseNotAllowed.status_code)

    def test_when_no_permission_to_consolidate(self):
        person_with_no_rights = PersonFactory()
        self.client.force_login(person_with_no_rights.user)
        response = self.client.post(self.url, data=self.post_data)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_when_no_proposal(self):
        post_data = {"learning_unit_year_id": self.learning_unit_year.id + 1}

        response = self.client.post("learning_unit_consolidate_proposal", data=post_data)

        self.assertTemplateUsed(response, "page_not_found.html")
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_when_no_post_data(self):
        response = self.client.post("learning_unit_consolidate_proposal", data={})

        self.assertTemplateUsed(response, "page_not_found.html")
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    @mock.patch("base.business.learning_unit_proposal.consolidate_proposals_and_send_report",
                side_effect=lambda prop, author, send_mail: {})
    def test_when_proposal_and_can_consolidate_proposal(self, mock_consolidate):
        response = self.client.post(self.url, data=self.post_data, follow=False)

        expected_redirect_url = reverse('learning_unit', args=[self.learning_unit_year.id])
        self.assertRedirects(response, expected_redirect_url)
        mock_consolidate.assert_called_once_with([self.proposal], self.person, {})

    @mock.patch("base.business.learning_units.perms.is_eligible_to_consolidate_proposal", return_value=True)
    def test_creation_proposal_consolidation(self, mock_perms):
        creation_proposal = ProposalLearningUnitFactory(
            type=proposal_type.ProposalType.CREATION,
            state=proposal_state.ProposalState.ACCEPTED.name,
            learning_unit_year__subtype=learning_unit_year_subtypes.FULL,
            learning_unit_year__academic_year=self.current_academic_year,
            learning_unit_year__learning_container_year__academic_year=self.current_academic_year
        )
        lu_id = creation_proposal.learning_unit_year.learning_unit.id
        self.client.post("learning_unit_consolidate_proposal",
                         data={"learning_unit_year_id": creation_proposal.learning_unit_year.id}, follow=False)
        self.assertTrue(mdl_base.learning_unit.LearningUnit.objects.filter(pk=lu_id).exists())


@override_flag('learning_unit_proposal_delete', active=True)
class TestConsolidateDelete(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = AcademicYearFactory.produce_in_future(quantity=5)
        cls.current_academic_year = cls.academic_years[1]

        cls.person = PersonFactory()
        cls.person.user.user_permissions.add(Permission.objects.get(codename="can_access_learningunit"))
        cls.person.user.user_permissions.add(Permission.objects.get(codename="can_consolidate_learningunit_proposal"))
        cls.requirement_entity = EntityVersionFactory().entity

    def setUp(self):
        self.proposal = ProposalLearningUnitFactory(
            type=proposal_type.ProposalType.SUPPRESSION.name,
            state=proposal_state.ProposalState.ACCEPTED.name,
            learning_unit_year__subtype=learning_unit_year_subtypes.FULL,
            learning_unit_year__academic_year=self.current_academic_year,
            learning_unit_year__learning_unit__start_year=self.current_academic_year,
            learning_unit_year__learning_container_year__academic_year=self.current_academic_year,
            learning_unit_year__learning_container_year__container_type=learning_container_year_types.COURSE,
            learning_unit_year__learning_container_year__requirement_entity=self.requirement_entity,
        )
        self.learning_unit_year = self.proposal.learning_unit_year

        person_entity = PersonEntityFactory(person=self.person,
                                            entity=self.learning_unit_year.learning_container_year.requirement_entity)
        EntityVersionFactory(entity=person_entity.entity)

        self.url = reverse("learning_unit_consolidate_proposal",
                           kwargs={'learning_unit_year_id': self.learning_unit_year.id})
        self.post_data = {"learning_unit_year_id": self.learning_unit_year.id}

        self.client.force_login(self.person.user)

    @mock.patch("base.business.learning_unit_proposal.consolidate_proposals_and_send_report",
                side_effect=lambda prop, author, send_mail: {})
    def test_when_proposal_and_can_consolidate_proposal_suppression_with_previous_year(self, mock_consolidate):
        LearningUnitYearFactory(
            academic_year=self.academic_years[0],
            subtype=learning_unit_year_subtypes.FULL,
            learning_unit=self.learning_unit_year.learning_unit,
            learning_container_year__academic_year=self.academic_years[0],
            learning_container_year__container_type=learning_container_year_types.COURSE,
            learning_container_year__requirement_entity=self.requirement_entity,
        )
        response = self.client.post(self.url, data=self.post_data, follow=False)

        expected_redirect_url = reverse('learning_unit',
                                        args=[self.learning_unit_year.get_learning_unit_previous_year().id])
        self.assertRedirects(response, expected_redirect_url)
        mock_consolidate.assert_called_once_with([self.proposal], self.person, {})

    @mock.patch("base.business.learning_unit_proposal.consolidate_proposals_and_send_report",
                side_effect=lambda prop, author, send_mail: {})
    def test_when_proposal_and_can_consolidate_proposal_suppression_without_previous_year(self, mock_consolidate):
        response = self.client.post(self.url, data=self.post_data, follow=False)

        expected_redirect_url = reverse('learning_units')
        self.assertRedirects(response, expected_redirect_url)
        mock_consolidate.assert_called_once_with([self.proposal], self.person, {})


class TestConsolidateReportForCmsLearningUnitAchievement(TestCase):

    def setUp(self):
        self.language_fr = LanguageFactory(code=FR_CODE_LANGUAGE)
        self.language_en = LanguageFactory(code=EN_CODE_LANGUAGE)

        current_year = get_current_year()
        self.lu = LearningUnitFactory()

        self.learning_unit_year_in_future = []
        self.luy_past = []

        year = current_year - 3

        concerned_cms_labels = \
            CMS_LABEL_PEDAGOGY_FR_AND_EN + CMS_LABEL_PEDAGOGY_FR_ONLY + CMS_LABEL_SPECIFICATIONS + CMS_LABEL_SUMMARY

        self.text_label = TextLabelFactory(label=random.choice(concerned_cms_labels),
                                           entity='learning_unit_year')

        while year <= current_year + 6:
            ay = AcademicYearFactory(year=year)
            luy = LearningUnitYearFactory(learning_unit=self.lu, academic_year=ay,
                                          acronym='LECON2365')

            self._create_description_fiche_and_specifications_data(current_year, luy, year)
            year += 1

    @patch('base.business.learning_units.edition._update_descriptive_fiche')
    def test_descriptive_fiche_and_achievements_no_update_because_is_past(self, mock__update_descriptive_fiche):
        proposal_in_past = ProposalLearningUnitFactory(
            state=proposal_state.ProposalState.ACCEPTED.name,
            learning_unit_year=self.luy_past[0])

        _descriptive_fiche_and_achievements_update(proposal_in_past.learning_unit_year, self.luy_past[1])
        mock__update_descriptive_fiche.assert_not_called()

    @override_settings(LANGUAGES=[('fr-be', 'French'), ], LANGUAGE_CODE='fr-be')
    def test_descriptive_fiche_and_achievements_update_and_report(self):
        proposal = ProposalLearningUnitFactory(
            state=proposal_state.ProposalState.ACCEPTED.name,
            learning_unit_year=self.learning_unit_year)

        _descriptive_fiche_and_achievements_update(proposal.learning_unit_year, self.learning_unit_year_in_future[0])

        self._assert_learning_unit_achievement_update(proposal)
        self._assert_cms_data_update(proposal)

    def _assert_cms_data_update(self, proposal):
        for learning_unit_yr in self.learning_unit_year_in_future:
            for t in TranslatedText.objects.filter(reference=learning_unit_yr.id, entity='learning_unit_year',
                                                   language=self.language_fr, text_label=self.text_label):
                self.assertEqual(t.text, NEW_TEXT.format(proposal.learning_unit_year.academic_year.year))

    def _assert_learning_unit_achievement_update(self, proposal):
        for la in mdl_base.learning_achievement.LearningAchievement.objects. \
                filter(learning_unit_year__learning_unit=proposal.learning_unit_year.learning_unit):
            if la.learning_unit_year.academic_year.year < self.learning_unit_year.academic_year.year:
                self.assertEqual(la.text, "old text {}".format(la.learning_unit_year.academic_year.year))
            else:
                self.assertEqual(la.text, NEW_TEXT.format(proposal.learning_unit_year.academic_year.year))

    def _create_description_fiche_and_specifications_data(self, current_year, luy, year):
        a_text = "old text {}".format(year)
        if year > current_year:
            self.learning_unit_year_in_future.append(luy)
        if year < current_year:
            self.luy_past.append(luy)
        if year == current_year:
            self.learning_unit_year = luy
            a_text = NEW_TEXT.format(current_year)
        LearningAchievementFactory(learning_unit_year=luy,
                                   text=a_text,
                                   code_name="1",
                                   language=self.language_fr,
                                   consistency_id=1)
        TranslatedTextFactory(reference=luy.id, entity='learning_unit_year',
                              language="fr-be", text=a_text,
                              text_label=self.text_label)
