#############################################################################
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

from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.urls import reverse

from attribution.tests.factories.attribution import AttributionFactory
from base.models.enums import academic_calendar_type
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFakerFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.tutor import TutorFactory
from base.tests.factories.user import SuperUserFactory
from osis_common.models import message_history

LANGUAGE_CODE_FR = 'fr-be'
LANGUAGE_CODE_EN = 'en'


class MyOsisViewTestCase(TestCase):
    fixtures = ['osis_common/fixtures/messages_tests.json']

    def setUp(self):
        self.a_superuser = SuperUserFactory()
        self.person = PersonFactory(user=self.a_superuser,
                                    language=LANGUAGE_CODE_FR)
        self.client.force_login(self.a_superuser)

        academic_year = create_current_academic_year()
        self.summary_course_submission_calendar = AcademicCalendarFactory(
            academic_year=academic_year,
            start_date=academic_year.start_date,
            end_date=academic_year.end_date,
            reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION)

        self.tutor = TutorFactory(person=self.person)
        # FIXME CHANGE LEARNINGUNITYEARFACTORY FOR AVOID MULTI ACADEMIC YEAR
        self.learning_container_year = LearningContainerYearFactory(academic_year=academic_year)
        self.learning_unit_year = LearningUnitYearFakerFactory(academic_year=academic_year,
                                                               learning_container_year=self.learning_container_year)
        self.attribution = AttributionFactory(learning_unit_year=self.learning_unit_year, summary_responsible=True,
                                              tutor=self.tutor)

    @staticmethod
    def get_message_history():
        return message_history.MessageHistory.objects.all().first()

    def test_my_osis_index(self):
        from base.views.my_osis import my_osis_index
        response = self.client.get(reverse(my_osis_index))
        self.assertTemplateUsed(response, 'my_osis/home.html')

    def test_my_messages_index(self):
        from base.views.my_osis import my_messages_index

        response = self.client.get(reverse(my_messages_index))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'my_osis/my_messages.html')

    def test_get_messages_formset(self):
        messages = message_history.MessageHistory.objects.all()
        from base.views.my_osis import get_messages_formset
        formset_factory_result = get_messages_formset(messages)

        self.assertEqual(len(messages), len(formset_factory_result))

        cpt = 0
        for form in formset_factory_result:
            message = messages[cpt]
            self.assertEqual(message.subject, form['subject'].value())
            self.assertEqual(message.id, form['id'].value())
            cpt += 1

    def test_profile(self):
        from base.views.my_osis import profile
        response = self.client.get(reverse(profile))

        self.assertTemplateUsed(response, 'my_osis/profile.html')
        with self.assertRaises(KeyError):
            response.context['tab_attribution_on']

        self.check_context_data(response.context)

    def test_profile_attributions(self):
        from base.views.my_osis import profile_attributions
        response = self.client.get(reverse(profile_attributions))

        self.assertTemplateUsed(response, 'my_osis/profile.html')
        self.assertEqual(response.context['tab_attribution_on'], True)
        self.check_context_data(response.context)

    def test_read_message(self):
        message = self.get_message_history()
        from base.views.my_osis import read_message

        response = self.client.get(reverse(read_message, args=[message.id]))

        self.assertTemplateUsed(response, 'my_osis/my_message.html')
        self.assertEqual(response.context['my_message'], message)

    def test_get_data(self):
        request = self.get_request()
        from base.views.my_osis import _get_data

        data = _get_data(request)
        self.assertEqual(data['person'], self.person)

    @override_settings(LANGUAGES=[('fr-be', 'French'), ('en', 'English'), ], LANGUAGE_CODE='fr-be')
    def test_profile_lang(self):
        data = {
            "ui_language": LANGUAGE_CODE_EN
        }
        response = self.client.post(reverse('profile_lang'), data)

        self.assertTemplateUsed(response, 'my_osis/profile.html')
        self.assertEqual(response.context['person'].language, LANGUAGE_CODE_EN)

    def get_request(self):
        request_factory = RequestFactory()
        request = request_factory.get(reverse('home'))
        request.user = self.a_superuser
        return request

    def check_context_data(self, context):
        self.assertEqual(context['person'], self.person)
        self.assertCountEqual(context['addresses'], [])
        self.assertEqual(context['tutor'], self.tutor)
        self.assertCountEqual(context['attributions'], [self.attribution])
        self.assertCountEqual(context['programs'], [])
        self.assertTrue(context['summary_submission_opened'])
