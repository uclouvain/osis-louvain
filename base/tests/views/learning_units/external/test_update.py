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
import datetime

from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages, SUCCESS
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from waffle.testutils import override_flag

from base.models.enums.learning_container_year_types import EXTERNAL
from base.tests.factories.academic_calendar import AcademicCalendarLearningUnitCentralEditionFactory
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.external_learning_unit_year import ExternalLearningUnitYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFullFactory
from base.tests.factories.person import CentralManagerForUEFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.user import UserFactory
from base.tests.forms.test_external_learning_unit import get_valid_external_learning_unit_form_data
from base.views.learning_units.update import update_learning_unit


@override_flag('learning_unit_update', active=True)
class TestUpdateExternalLearningUnitView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.person = CentralManagerForUEFactory(
            "can_access_learningunit", "can_edit_learningunit",
            user=cls.user
        )

        person_entity = PersonEntityFactory(
            person=cls.person,
            entity=EntityVersionFactory().entity,
        )

        cls.academic_year = create_current_academic_year()
        AcademicCalendarLearningUnitCentralEditionFactory(
            data_year=cls.academic_year,
            start_date=datetime.datetime(cls.academic_year.year - 6, 9, 15),
            end_date=datetime.datetime(cls.academic_year.year + 1, 9, 14)
        )

        cls.luy = LearningUnitYearFullFactory(
            academic_year=cls.academic_year,
            internship_subtype=None,
            acronym="EFAC1000",
            learning_container_year__container_type=EXTERNAL,
            learning_container_year__requirement_entity=person_entity.entity,
        )
        cls.data = get_valid_external_learning_unit_form_data(cls.academic_year, cls.person, cls.luy)

        cls.url = reverse(update_learning_unit, args=[cls.luy.pk])

    def setUp(self):
        self.external = ExternalLearningUnitYearFactory(learning_unit_year=self.luy)
        self.client.force_login(self.user)

    def test_update_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_update_get_permission_denied(self):
        self.user.user_permissions.remove(Permission.objects.get(codename="can_edit_learningunit"))

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_update_post(self):
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 302)
        messages = [m.level for m in get_messages(response.wsgi_request)]
        self.assertEqual(messages, [SUCCESS])

    def test_update_message_with_report(self):
        self.data['postponement'] = "1"
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 302)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(messages[0], _("The learning unit has been updated (with report)."))

    def test_update_message_without_report(self):
        self.data['postponement'] = "0"
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 302)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(messages[0], _("The learning unit has been updated (without report)."))
