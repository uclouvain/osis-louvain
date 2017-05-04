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
from django.test import TestCase, RequestFactory, Client
from django.contrib.auth.models import User
from assistant.utils import send_email
from assistant.models.manager import Manager
from base.models.person import Person
from assistant.models.assistant_mandate import AssistantMandate
from assistant.models.academic_assistant import AcademicAssistant
from assistant.models.reviewer import Reviewer
from base.models.academic_year import AcademicYear
from base.models import academic_year
from datetime import date
from django.utils import timezone
from osis_common.models import message_template
from unittest.mock import patch
from django.core.mail.message import EmailMultiAlternatives
from assistant.models.settings import Settings


class SendEmailTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.user = User.objects.create_user(
            username='assistant', email='laurent.buset@uclouvain.be', password='assistant'
        )
        self.user.save()
        self.person = Person.objects.create(user=self.user, first_name='first_name', last_name='last_name')
        self.person.save()
        self.academic_assistant = AcademicAssistant.objects.create(person=self.person)
        self.academic_assistant.save()
        self.user = User.objects.create_user(
            username='manager', email='laurent.buset@uclouvain.be', password='manager')
        self.person = Person.objects.create(user=self.user, first_name='Lodia', last_name='Perzyna')
        self.person.save()
        self.manager = Manager.objects.create(person=self.person)
        self.manager.save()
        self.client.login(username=self.manager.person.user.username, password=self.manager.person.user.password)
        self.academic_year = AcademicYear.objects.create(year=2016, start_date=date(2016, 9, 1),
                                                         end_date=date(2017, 8, 31))
        self.academic_year.save()
        self.current_academic_year = academic_year.current_academic_year()
        self.assistant_mandate = AssistantMandate.objects.create(assistant=self.academic_assistant,
                                                                 academic_year=self.current_academic_year,
                                                                 entry_date=date(2015, 9, 1),
                                                                 end_date=date(2017, 9, 1),
                                                                 fulltime_equivalent=1,
                                                                 renewal_type='normal'
                                                                 )

        self.user = User.objects.create_user(
            username='phd_supervisor', email='phd_supervisor@uclouvain.be', password='phd_supervisor'
        )
        self.user.save()
        self.phd_supervisor = Person.objects.create(user=self.user, first_name='phd', last_name='supervisor')
        self.phd_supervisor.save()
        self.academic_assistant.supervisor = self.phd_supervisor
        self.academic_assistant.save()
        self.settings = Settings.objects.create(starting_date=timezone.now(),
                                                ending_date=timezone.now() + timezone.timedelta(days=100))
        self.settings.save()
        self.user = User.objects.create_user(
            username='reviewer', email='laurent.buset@uclouvain.be', password='reviewer'
        )
        self.user.save()
        self.person = Person.objects.create(user=self.user, first_name='first_name', last_name='last_name')
        self.person.save()
        self.reviewer = Reviewer.objects.create(person=self.person, role='SUPERVISION')
        self.reviewer.save()

        add_message_template_for_assistants_html()
        add_message_template_for_assistants_txt()
        add_message_template_for_phd_supervisor_html()
        add_message_template_for_phd_supervisor_txt()

    @patch("osis_common.messaging.send_message.EmailMultiAlternatives", autospec=True)
    def test_with_one_assistant(self, mock_class):
        if self.assistant_mandate.renewal_type == 'normal':
            html_template_ref = 'assistant_assistants_startup_normal_renewal_html'
            txt_template_ref = 'assistant_assistants_startup_normal_renewal_txt'
        else:
            html_template_ref = 'assistant_assistants_startup_except_renewal_html'
            txt_template_ref = 'assistant_assistants_startup_except_renewal_txt'
        send_email.send_message(self.academic_assistant.person, html_template_ref, txt_template_ref)
        mock_class.send.return_value = None
        self.assertIsInstance(mock_class, EmailMultiAlternatives)
        call_args = mock_class.call_args
        recipients = call_args[0][3]
        self.assertEqual(len(recipients), 1)


    @patch("osis_common.messaging.send_message.EmailMultiAlternatives", autospec=True)
    def test_with_one_phd_supervisor(self, mock_class):
        html_template_ref = 'assistant_phd_supervisor_review_html'
        txt_template_ref = 'assistant_phd_supervisor_review_txt'
        send_email.send_message(self.phd_supervisor, html_template_ref, txt_template_ref)
        mock_class.send.return_value = None
        self.assertIsInstance(mock_class, EmailMultiAlternatives)
        call_args = mock_class.call_args
        recipients = call_args[0][3]
        self.assertEqual(len(recipients), 1)


def add_message_template_for_assistants_txt():
    msg_template = message_template.MessageTemplate(
        reference="assistant_assistants_startup_normal_renewal_txt",
        template="<p><em>Ceci est un message automatique g&eacute;n&eacute;r&eacute; "
                 "renouvellement des mandats des assistant·e·s dont le contrat arrive à échéance"
                 "<strong> entre le {{ start_date }} et le {{ end_date }}</strong> vient de débuter. "
                 "Elle s'effectue intégralement par voie électronique.</em></p>\r\n\r\n"
                 "</p>\r\n\r\n<p>&nbsp;</p>",
        format="PLAIN",
        language="en"
    )
    msg_template.save()
    msg_template = message_template.MessageTemplate(
        reference="assistant_assistants_startup_normal_renewal_txt",
        template="<p><em>Ceci est un message automatique g&eacute;n&eacute;r&eacute; "
                 "renouvellement des mandats des assistant·e·s dont le contrat arrive à échéance"
                 "<strong> entre le {{ start_date }} et le {{ end_date }}</strong> vient de débuter. "
                 "Elle s'effectue intégralement par voie électronique.</em></p>\r\n\r\n"
                 "</p>\r\n\r\n<p>&nbsp;</p>",
        format="PLAIN",
        language="fr-be"
    )
    msg_template.save()


def add_message_template_for_assistants_html():
    msg_template = message_template.MessageTemplate(
        reference="assistant_assistants_startup_normal_renewal_html",
        template="<p>{% autoescape off %}<em>Ceci est un message automatique g&eacute;n&eacute;r&eacute; "
                 "renouvellement des mandats des assistant·e·s dont le contrat arrive à échéance"
                 "<strong> entre le {{ start_date }} et le {{ end_date }}</strong> vient de débuter. "
                 "Elle s'effectue intégralement par voie électronique.</em></p>\r\n\r\n"
                 "</p>\r\n\r\n<p>&nbsp;{% endautoescape %}</p>",
        format="HTML",
        language="fr-be"
    )
    msg_template.save()
    msg_template = message_template.MessageTemplate(
        reference="assistant_assistants_startup_normal_renewal_html",
        template="<p>{% autoescape off %}<em>Ceci est un message automatique g&eacute;n&eacute;r&eacute; "
                 "renouvellement des mandats des assistant·e·s dont le contrat arrive à échéance"
                 "<strong> entre le {{ start_date }} et le {{ end_date }}</strong> vient de débuter. "
                 "Elle s'effectue intégralement par voie électronique.</em></p>\r\n\r\n"
                 "</p>\r\n\r\n<p>&nbsp;{% endautoescape %}</p>",
        format="HTML",
        language="en"
    )
    msg_template.save()


def add_message_template_for_phd_supervisor_html():
    msg_template = message_template.MessageTemplate(
        reference="assistant_phd_supervisor_review_html",
        template="<p>{% autoescape off %}Bonjour {{ first_name }} {{ last_name }}"
                 "<em>Ceci est un message automatique g&eacute;n&eacute;r&eacute; "
                "https://osis.uclouvain.be/assistants/phd_supervisor/assistants_list/"
                 "</p>\r\n\r\n<p>&nbsp;{% endautoescape %}</p>",
        format="HTML",
        language="fr-be"
    )
    msg_template.save()
    msg_template = message_template.MessageTemplate(
        reference="assistant_phd_supervisor_review_html",
        template="<p>{% autoescape off %}Bonjour {{ first_name }} {{ last_name }}"
                 "<em>This is an automatic message."
                 "https://osis.uclouvain.be/assistants/phd_supervisor/assistants_list/"
                 "</p>\r\n\r\n<p>&nbsp;{% endautoescape %}</p>",
        format="HTML",
        language="en"
    )
    msg_template.save()


def add_message_template_for_phd_supervisor_txt():
    msg_template = message_template.MessageTemplate(
        reference="assistant_phd_supervisor_review_txt",
        template="<p><em>Ceci est un message automatique g&eacute;n&eacute;r&eacute; "
                 "renouvellement des mandats des assistant·e·s dont le contrat arrive à échéance"
                 "<strong> entre le {{ start_date }} et le {{ end_date }}</strong> vient de débuter. "
                 "Elle s'effectue intégralement par voie électronique.</em></p>\r\n\r\n"
                 "</p>\r\n\r\n<p>&nbsp;</p>",
        format="PLAIN",
        language="fr-be"
    )
    msg_template.save()
    msg_template = message_template.MessageTemplate(
        reference="assistant_phd_supervisor_review_txt",
        template="<p><em>Ceci est un message automatique g&eacute;n&eacute;r&eacute; "
                 "renouvellement des mandats des assistant·e·s dont le contrat arrive à échéance"
                 "<strong> entre le {{ start_date }} et le {{ end_date }}</strong> vient de débuter. "
                 "Elle s'effectue intégralement par voie électronique.</em></p>\r\n\r\n"
                 "</p>\r\n\r\n<p>&nbsp;</p>",
        format="PLAIN",
        language="en"
    )
    msg_template.save()
