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
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from backoffice.settings.base import LANGUAGE_CODE_FR, LANGUAGE_CODE_EN
from base.business.education_groups.general_information_sections import CMS_LABEL_PROGRAM_AIM, \
    CMS_LABEL_ADDITIONAL_INFORMATION
from base.models.education_group_detailed_achievement import EducationGroupDetailedAchievement
from base.models.enums import academic_calendar_type
from base.tests.factories.academic_calendar import OpenAcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_achievement import EducationGroupAchievementFactory
from base.tests.factories.education_group_detailed_achievement import EducationGroupDetailedAchievementFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from cms.enums import entity_name
from cms.models.translated_text import TranslatedText
from cms.tests.factories.text_label import OfferTextLabelFactory
from cms.tests.factories.translated_text import OfferTranslatedTextFactory
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from education_group.views.proxy.read import Tab
from program_management.tests.factories.education_group_version import StandardEducationGroupVersionFactory


class TestEducationGroupAchievementActionUpdateDelete(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.education_group_year = EducationGroupYearFactory()
        StandardEducationGroupVersionFactory(offer=cls.education_group_year)

        cls.person = PersonFactory()
        CentralManagerFactory(person=cls.person, entity=cls.education_group_year.management_entity)
        for perm_name in ['delete_educationgroupachievement', 'change_educationgroupachievement']:
            perm = Permission.objects.get(codename=perm_name)
            cls.person.user.user_permissions.add(perm)

    def setUp(self):
        self.achievement_0 = EducationGroupAchievementFactory(education_group_year=self.education_group_year)
        self.achievement_1 = EducationGroupAchievementFactory(education_group_year=self.education_group_year)
        self.achievement_2 = EducationGroupAchievementFactory(education_group_year=self.education_group_year)

        self.client.force_login(self.person.user)

    def test_form_valid_up(self):
        response = self.client.post(
            reverse(
                "training_achievement_actions",
                args=[
                    self.education_group_year.academic_year.year,
                    self.education_group_year.partial_acronym,
                    self.achievement_2.pk,
                ]) + '?path={}&tab={}'.format(1111, Tab.SKILLS_ACHIEVEMENTS), data={"action": "up"}
        )

        self.assertEqual(response.status_code, 302)
        self.achievement_2.refresh_from_db()
        self.assertEqual(self.achievement_2.order, 1)

    def test_form_valid_down(self):
        response = self.client.post(
            reverse(
                "training_achievement_actions",
                args=[
                    self.education_group_year.academic_year.year,
                    self.education_group_year.partial_acronym,
                    self.achievement_0.pk,
                ]) + '?path={}&tab={}'.format(1111, Tab.SKILLS_ACHIEVEMENTS), data={"action": "down"}
        )

        self.assertEqual(response.status_code, 302)
        self.achievement_0.refresh_from_db()
        self.assertEqual(self.achievement_0.order, 1)

    def test_form_invalid(self):
        response = self.client.post(
            reverse(
                "training_achievement_actions",
                args=[
                    self.education_group_year.academic_year.year,
                    self.education_group_year.partial_acronym,
                    self.achievement_2.pk,
                ]) + '?path={}&tab={}'.format(1111, Tab.SKILLS_ACHIEVEMENTS), data={"action": "not_an_action"}
        )

        self.assertEqual(response.status_code, 302)

        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(messages[0], _("Invalid action"))

    def test_update(self):
        code = "The life is like a box of chocolates"
        response = self.client.post(
            reverse(
                "training_achievement_update",
                args=[
                    self.education_group_year.academic_year.year,
                    self.education_group_year.partial_acronym,
                    self.achievement_2.pk,
                ]) + '?path={}&tab={}'.format(1111, Tab.SKILLS_ACHIEVEMENTS), data={"code_name": code, 'path': 1111}
        )

        self.assertEqual(response.status_code, 302)
        self.achievement_2.refresh_from_db()
        self.assertEqual(self.achievement_2.code_name, code)

    def test_update_case_user_without_permissions(self):
        self.client.force_login(user=UserFactory())
        code = "The life is like a box of chocolates"
        response = self.client.post(
            reverse(
                "training_achievement_update",
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
                "training_achievement_delete",
                args=[
                    self.education_group_year.academic_year.year,
                    self.education_group_year.partial_acronym,
                    self.achievement_0.pk,
                ]), data={'path': 1111}
        )

        self.assertEqual(response.status_code, 302)
        with self.assertRaises(ObjectDoesNotExist):
            self.achievement_0.refresh_from_db()

    def test_delete_case_user_without_permissions(self):
        self.client.force_login(user=UserFactory())
        response = self.client.post(
            reverse(
                "training_achievement_delete",
                args=[
                    self.education_group_year.academic_year.year,
                    self.education_group_year.partial_acronym,
                    self.achievement_2.pk,
                ]), data={"path": 1111}
        )
        self.assertEqual(response.status_code, 403)

    def test_update_detailed_achievement(self):
        code = "The life is like a box of chocolates"
        achievement = EducationGroupAchievementFactory(education_group_year=self.education_group_year)
        d_achievement = EducationGroupDetailedAchievementFactory(education_group_achievement=achievement)
        response = self.client.post(
            reverse(
                "training_detailed_achievement_update",
                args=[
                    self.education_group_year.academic_year.year,
                    self.education_group_year.partial_acronym,
                    achievement.pk,
                    d_achievement.pk
                ]), data={"code_name": code, "path": 1111}
        )

        self.assertEqual(response.status_code, 302)
        d_achievement.refresh_from_db()
        self.assertEqual(d_achievement.code_name, code)

    def test_training_detailed_achievement_actions(self):
        achievement = EducationGroupAchievementFactory(education_group_year=self.education_group_year)
        d_achievement_1 = EducationGroupDetailedAchievementFactory(education_group_achievement=achievement, order=0)
        d_achievement_2 = EducationGroupDetailedAchievementFactory(education_group_achievement=achievement, order=1)
        response = self.client.post(
            reverse(
                "training_detailed_achievement_actions",
                args=[
                    self.education_group_year.academic_year.year,
                    self.education_group_year.partial_acronym,
                    self.achievement_2.pk,
                    d_achievement_2.pk

                ]) + '?path={}&tab={}'.format(1111, Tab.SKILLS_ACHIEVEMENTS), data={"action": "up"}
        )

        self.assertEqual(response.status_code, 302)
        d_achievement_1.refresh_from_db()
        d_achievement_2.refresh_from_db()
        self.assertEqual(d_achievement_1.order, 1)
        self.assertEqual(d_achievement_2.order, 0)
