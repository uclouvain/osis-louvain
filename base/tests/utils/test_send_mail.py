##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.test import TestCase
from osis_common.models import message_template
from base.utils import send_mail
from unittest.mock import patch
from base.tests.models import test_person, test_academic_year, test_learning_unit_year, test_offer_year, \
    test_exam_enrollment
from django.core.mail.message import EmailMultiAlternatives


class TestSendMessage(TestCase):
    def setUp(self):
        self.person_1 = test_person.create_person("person_1", last_name="test", email="person1@test.com")
        self.person_2 = test_person.create_person("person_2", last_name="test", email="person2@test.com")
        self.persons = [self.person_1, self.person_2]

        academic_year = test_academic_year.create_academic_year()
        self.learning_unit_year = test_learning_unit_year.create_learning_unit_year("TEST", "Cours de test",
                                                                                    academic_year)
        self.offer_year = test_offer_year.create_offer_year("SINF2MA", "Master en Sciences Informatique",
                                                            academic_year)

        self.exam_enrollment_1 = test_exam_enrollment.create_exam_enrollment_with_student(1, "64641200",
                                                                                          self.offer_year,
                                                                                          self.learning_unit_year,
                                                                                          academic_year)
        self.exam_enrollment_2 = test_exam_enrollment.create_exam_enrollment_with_student(2, "60601200",
                                                                                          self.offer_year,
                                                                                          self.learning_unit_year,
                                                                                          academic_year)
        add_message_template_html()
        add_message_template_txt()

    @patch("osis_common.messaging.send_message.EmailMultiAlternatives", autospec=True)
    def test_with_one_enrollment(self, mock_class):
        mock_class.send.return_value = None
        self.assertIsInstance(mock_class, EmailMultiAlternatives)
        send_mail.send_message_after_all_encoded_by_manager(self.persons, [self.exam_enrollment_1],
                                                            self.learning_unit_year.acronym, self.offer_year.acronym)
        call_args = mock_class.call_args
        subject = call_args[0][0]
        recipients = call_args[0][3]
        attachments = call_args[1]
        self.assert_subject_mail(subject, self.learning_unit_year.acronym, self.offer_year.acronym)
        self.assertEqual(len(recipients), 2)
        self.assertIsNotNone(attachments)

    def assert_subject_mail(self, subject, learning_unit_acronym, offer_year_acronym):
        self.assertIn(learning_unit_acronym, subject)
        self.assertIn(offer_year_acronym, subject)



def add_message_template_txt():
    msg_template = message_template.MessageTemplate(
        reference="assessments_all_scores_by_pgm_manager_txt",
        subject="Complete encoding of {learning_unit_acronym} for {offer_acronym}",
        template="<p>This is a generated message - Please don&#39;t reply</p>\r\n\r\n<p><br />\r\nWe inform you that "
                 "all the&nbsp; scores of<strong> {{ learning_unit_acronym }}</strong> for <strong>{{ offer_acronym }}"
                 "</strong> have been validated by the program manager.</p>\r\n\r\n<p>{{ enrollments }}</p>\r\n\r\n<p>"
                 "Osis UCLouvain</p>",
        format="PLAIN",
        language="en"
    )
    msg_template.save()

    msg_template = message_template.MessageTemplate(
        reference="assessments_all_scores_by_pgm_manager_txt",
        subject="Encodage complet des notes de {learning_unit_acronym} pour {offer_acronym}",
        template="<p>Encodage de notes</p>\r\n\r\n<p><em>Ceci est un message automatique g&eacute;n&eacute;r&eacute; "
                 "par le serveur OSIS &ndash; Merci de ne pas y r&eacute;pondre.</em></p>\r\n\r\n<p>Nous vous informons"
                 " que l&#39;ensemble des notes<strong> </strong>de<strong> {{ learning_unit_acronym }}</strong> pour"
                 " l&#39;offre <strong>{{ offer_acronym }}</strong> ont &eacute;t&eacute; valid&eacute;es par le "
                 "gestionnaire de programme.</p>\r\n\r\n<p>{{ enrollments }}</p>\r\n\r\n<p>Osis UCLouvain."
                 "</p>\r\n\r\n<p>&nbsp;</p>",
        format="PLAIN",
        language="fr-be"
    )
    msg_template.save()


def add_message_template_html():
    msg_template = message_template.MessageTemplate(
        reference="assessments_all_scores_by_pgm_manager_html",
        subject="Encodage complet des notes de {learning_unit_acronym} pour {offer_acronym}",
        template="<p>{% autoescape off %}</p>\r\n\r\n<h3>Encodage de notes</h3>\r\n\r\n<p><em>Ceci est un message "
                 "automatique g&eacute;n&eacute;r&eacute; par le serveur OSIS &ndash; Merci de ne pas y r&eacute;pondre"
                 ".</em></p>\r\n\r\n<p>Nous vous informons que l&#39;ensemble des notes<strong> </strong>de<strong> "
                 "{{ learning_unit_acronym }}</strong> pour l&#39;offre <strong>{{ offer_acronym }}</strong> ont "
                 "&eacute;t&eacute; valid&eacute;es par le gestionnaire de programme.</p>\r\n\r\n<p>{{ enrollments }}"
                 "</p>\r\n\r\n<p>{{ signature }}</p>\r\n\r\n<p>{% endautoescape %}</p>",
        format="HTML",
        language="fr-be"
    )
    msg_template.save()

    msg_template = message_template.MessageTemplate(
        reference="assessments_all_scores_by_pgm_manager_html",
        subject="Complete encoding of {learning_unit_acronym} for {offer_acronym}",
        template="<p>{% autoescape off %}</p>\r\n\r\n<h3>Scores submission</h3>\r\n\r\n<p>This is a generated message "
                 "- Please don&#39;t reply</p>\r\n\r\n<p>We inform you that all the&nbsp; scores of<strong> "
                 "{{ learning_unit_acronym }}</strong> for <strong>{{ offer_acronym }}</strong> have been validated by "
                 "the program manager.</p>\r\n\r\n<p>{{ enrollments }}</p>\r\n\r\n<p>{{ signature }}</p>\r\n\r\n"
                 "<p>{% endautoescape %}</p>",
        format="HTML",
        language="en"
    )
    msg_template.save()
