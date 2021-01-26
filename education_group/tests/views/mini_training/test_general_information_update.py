#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
import mock
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from base.business.education_groups.general_information_sections import WELCOME_INTRODUCTION, \
    CMS_LABEL_ADDITIONAL_INFORMATION, CMS_LABEL_PROGRAM_AIM
from cms.models.translated_text import TranslatedText
from cms.tests.factories.text_label import OfferTextLabelFactory
from cms.tests.factories.translated_text import OfferTranslatedTextFactory
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from education_group.tests.factories.group_year import GroupYearDeepeningFactory
from program_management.tests.factories.education_group_version import StandardEducationGroupVersionFactory
from program_management.tests.factories.element import ElementGroupYearFactory


class TestMiniTrainingUpdateGeneralInformationView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.standard_mini_training = StandardEducationGroupVersionFactory(
            root_group=GroupYearDeepeningFactory(academic_year__current=True)
        )
        ElementGroupYearFactory(group_year=cls.standard_mini_training.root_group)
        cls.central_manager = CentralManagerFactory()
        cls.text_label = OfferTextLabelFactory(label=WELCOME_INTRODUCTION)

    def setUp(self) -> None:
        self.perm_patcher = mock.patch("django.contrib.auth.models.User.has_perm", return_value=True)
        self.mocked_perm = self.perm_patcher.start()
        self.addCleanup(self.perm_patcher.stop)

        self.url = reverse(
            "mini_training_general_information_update",
            args=[
                self.standard_mini_training.root_group.academic_year.year,
                self.standard_mini_training.root_group.partial_acronym
            ]
        )
        self.client.force_login(self.central_manager.person.user)

    def test_title_value(self):
        specific_labels = (CMS_LABEL_PROGRAM_AIM, CMS_LABEL_ADDITIONAL_INFORMATION)
        expected_title_values = (_("the program aims"), _("additional informations"))
        for label, expected_title in zip(specific_labels, expected_title_values):
            with self.subTest(label=label):
                response = self.client.get(self.url, {"label": label})
                self.assertEqual(response.context["title"], expected_title)

    def test_upsert(self):
        OfferTranslatedTextFactory(
            reference=self.standard_mini_training.offer.pk,
            text_label=self.text_label,
            text="to update"
        )
        self.client.post(self.url, data={
            "label": WELCOME_INTRODUCTION,
            "text_english": "Created",
            "text_french": "Updated"
        })

        self.assertQuerysetEqual(
            TranslatedText.objects.filter(reference=self.standard_mini_training.offer.id).values_list("text", flat=True),
            ['Created', 'Updated'],
            transform=lambda obj: obj,
            ordered=False
        )
