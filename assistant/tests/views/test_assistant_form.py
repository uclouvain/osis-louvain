##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test import TestCase, RequestFactory
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from base.models.person import Person
from base.models.academic_year import AcademicYear
from base.models import academic_year
from datetime import date
from assistant.views.assistant_form import form_part4_edit
from assistant.models.academic_assistant import AcademicAssistant
from assistant.models.assistant_mandate import AssistantMandate
from assistant.tests.factories.settings import SettingsFactory


class AssistantFormViewTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='assistant', email='laurent.buset@uclouvain.be', password='assistant'
        )
        self.user.save()
        self.client.login(username=self.user.username, password=self.user.password)
        self.person = Person.objects.create(user=self.user, first_name='first_name', last_name='last_name')
        self.person.save()
        self.academic_assistant = AcademicAssistant.objects.create(person=self.person)
        self.academic_assistant.save()
        self.academic_year = AcademicYear.objects.create(year=2016, start_date=date(2016, 9, 1),
                                                         end_date=date(2017, 8, 31))
        self.academic_year.save()
        self.current_academic_year = academic_year.current_academic_year()
        self.assistant_mandate = AssistantMandate.objects.create(assistant=self.academic_assistant,
                                                                 academic_year=self.current_academic_year,
                                                                 entry_date=date(2015, 9, 1),
                                                                 end_date=date(2017, 9, 1),
                                                                 fulltime_equivalent=1,
                                                                 renewal_type='normal',
                                                                 state='TRTS'
                                                                 )
        self.assistant_mandate.save()
        self.settings = SettingsFactory()

    def test_assistant_form_part4_edit_view_basic(self):
        request = self.factory.get(reverse('form_part4_edit', kwargs={'mandate_id': self.assistant_mandate.id}))
        request.user = self.user
        with self.assertTemplateUsed('assistant_form_part4.html'):
            response = form_part4_edit(request, self.assistant_mandate.id)
            self.assertEqual(response.status_code, 200)
