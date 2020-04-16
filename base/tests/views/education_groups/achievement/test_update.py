############################################################################
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
############################################################################
from django.contrib.messages import get_messages
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from backoffice.settings.base import LANGUAGE_CODE_FR, LANGUAGE_CODE_EN
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_achievement import EducationGroupAchievementFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from base.views.education_groups.achievement.detail import CMS_LABEL_PROGRAM_AIM, CMS_LABEL_ADDITIONAL_INFORMATION
from cms.enums import entity_name
from cms.models.translated_text import TranslatedText
from cms.tests.factories.text_label import TextLabelFactory
from cms.tests.factories.translated_text import TranslatedTextFactory
from education_group.tests.factories.auth.central_manager import CentralManagerFactory


class TestEducationGroupAchievementActionUpdateDelete(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.education_group_year = EducationGroupYearFactory()

        cls.achievement_0 = EducationGroupAchievementFactory(education_group_year=cls.education_group_year)
        cls.achievement_1 = EducationGroupAchievementFactory(education_group_year=cls.education_group_year)
        cls.achievement_2 = EducationGroupAchievementFactory(education_group_year=cls.education_group_year)

        cls.person = PersonFactory()
        CentralManagerFactory(person=cls.person, entity=cls.education_group_year.management_entity)

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_form_valid_up(self):
        response = self.client.post(
            reverse(
                "education_group_achievements_actions",
                args=[
                    self.education_group_year.pk,
                    self.education_group_year.pk,
                    self.achievement_2.pk,
                ]), data={"action": "up"}
        )

        self.assertEqual(response.status_code, 302)
        self.achievement_2.refresh_from_db()
        self.assertEqual(self.achievement_2.order, 1)

    def test_form_valid_down(self):
        response = self.client.post(
            reverse(
                "education_group_achievements_actions",
                args=[
                    self.education_group_year.pk,
                    self.education_group_year.pk,
                    self.achievement_0.pk,
                ]), data={"action": "down"}
        )

        self.assertEqual(response.status_code, 302)
        self.achievement_0.refresh_from_db()
        self.assertEqual(self.achievement_0.order, 1)

    def test_form_invalid(self):
        response = self.client.post(
            reverse(
                "education_group_achievements_actions",
                args=[
                    self.education_group_year.pk,
                    self.education_group_year.pk,
                    self.achievement_2.pk,
                ]), data={"action": "not_an_action"}
        )

        self.assertEqual(response.status_code, 302)

        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(messages[0], _("Invalid action"))

    def test_update(self):
        code = "The life is like a box of chocolates"
        response = self.client.post(
            reverse(
                "update_education_group_achievement",
                args=[
                    self.education_group_year.pk,
                    self.education_group_year.pk,
                    self.achievement_2.pk,
                ]), data={"code_name": code}
        )

        self.assertEqual(response.status_code, 302)
        self.achievement_2.refresh_from_db()
        self.assertEqual(self.achievement_2.code_name, code)

    def test_update_case_user_without_permissions(self):
        self.client.force_login(user=UserFactory())
        code = "The life is like a box of chocolates"
        response = self.client.post(
            reverse(
                "update_education_group_achievement",
                args=[
                    self.education_group_year.pk,
                    self.education_group_year.pk,
                    self.achievement_2.pk,
                ]), data={"code_name": code}
        )

        self.assertEqual(response.status_code, 403)

    def test_delete(self):
        response = self.client.post(
            reverse(
                "delete_education_group_achievement",
                args=[
                    self.education_group_year.pk,
                    self.education_group_year.pk,
                    self.achievement_0.pk,
                ]), data={}
        )

        self.assertEqual(response.status_code, 302)
        with self.assertRaises(ObjectDoesNotExist):
            self.achievement_0.refresh_from_db()

    def test_delete_case_user_without_permissions(self):
        self.client.force_login(user=UserFactory())
        response = self.client.post(
            reverse(
                "delete_education_group_achievement",
                args=[
                    self.education_group_year.pk,
                    self.education_group_year.pk,
                    self.achievement_2.pk,
                ]), data={}
        )
        self.assertEqual(response.status_code, 403)


class TestEducationGroupAchievementCMSSetup(TestCase):
    def setUp(self):
        self.person = PersonFactory()
        self.academic_year = AcademicYearFactory(current=True)
        self.education_group_year = EducationGroupYearFactory(academic_year=self.academic_year)
        CentralManagerFactory(person=self.person, entity=self.education_group_year.management_entity)
        self.client.force_login(self.person.user)


class TestEditEducationGroupAchievementProgramAim(TestEducationGroupAchievementCMSSetup):
    def setUp(self):
        super().setUp()

        self.url = reverse(
            "education_group_achievement_program_aim",
            args=[
                self.education_group_year.pk,
                self.education_group_year.pk,
            ]
        )
        self.text_label = TextLabelFactory(label=CMS_LABEL_PROGRAM_AIM, entity=entity_name.OFFER_YEAR)
        self.program_aim_french = TranslatedTextFactory(
            text_label=self.text_label,
            language=LANGUAGE_CODE_FR,
            entity=entity_name.OFFER_YEAR,
            reference=self.education_group_year.pk,
            text="dummy text"
        )

    def test_update_achievement_program_aim(self):
        """This test ensure that the french version is updated and the english version is created"""
        data = {
            "text_french": 'dummy text in french',
            "text_english": 'dummy text in english'
        }

        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 302)
        self.program_aim_french.refresh_from_db()
        # Update french version
        self.assertEqual(self.program_aim_french.text, data['text_french'])
        # Create english version
        self.assertTrue(TranslatedText.objects.filter(
            text_label=self.text_label,
            reference=self.education_group_year.pk,
            language=LANGUAGE_CODE_EN,
            entity=entity_name.OFFER_YEAR,
            text=data['text_english']
        ).exists())

    def test_update_without_permission(self):
        self.client.force_login(user=UserFactory())
        response = self.client.post(self.url, data={'french_text': 'Evil hacker'})
        self.assertEqual(response.status_code, 403)

    def test_update_when_user_not_logged(self):
        self.client.logout()
        response = self.client.post(self.url, data={'french_text': 'Evil hacker'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/login/?next={}".format(self.url))


class TestEditEducationGroupAchievementAdditionalInformation(TestEducationGroupAchievementCMSSetup):
    def setUp(self):
        super().setUp()

        self.url = reverse(
            "education_group_achievement_additional_information",
            args=[
                self.education_group_year.pk,
                self.education_group_year.pk,
            ]
        )

        self.text_label = TextLabelFactory(label=CMS_LABEL_ADDITIONAL_INFORMATION, entity=entity_name.OFFER_YEAR)
        self.program_aim_french = TranslatedTextFactory(
            text_label=self.text_label,
            language=LANGUAGE_CODE_FR,
            entity=entity_name.OFFER_YEAR,
            reference=self.education_group_year.pk,
            text="dummy text"
        )

    def test_update_achievement_program_aim(self):
        """This test ensure that the french version is updated and the english version is created"""
        data = {
            "text_french": 'dummy text in french',
            "text_english": 'dummy text in english'
        }

        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 302)
        self.program_aim_french.refresh_from_db()
        # Update french version
        self.assertEqual(self.program_aim_french.text, data['text_french'])
        # Create english version
        self.assertTrue(TranslatedText.objects.filter(
            text_label=self.text_label,
            reference=self.education_group_year.pk,
            language=LANGUAGE_CODE_EN,
            entity=entity_name.OFFER_YEAR,
            text=data['text_english']
        ).exists())

    def test_update_without_permission(self):
        self.client.force_login(user=UserFactory())
        response = self.client.post(self.url, data={'french_text': 'Evil hacker'})
        self.assertEqual(response.status_code, 403)

    def test_update_when_user_not_logged(self):
        self.client.logout()
        response = self.client.post(self.url, data={'french_text': 'Evil hacker'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/login/?next={}".format(self.url))
