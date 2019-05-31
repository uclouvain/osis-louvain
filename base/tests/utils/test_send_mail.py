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
from unittest.mock import patch

from django.test import TestCase

from base.models.education_group import EducationGroup
from base.models.education_group_year import EducationGroupYear
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonWithPermissionsFactory
from base.tests.models import test_person, test_academic_year, test_offer_year, \
    test_exam_enrollment
from base.utils import send_mail
from osis_common.models import message_template

LEARNING_UNIT_YEARS_VARIABLE_PARAGRAPH_ = "<p>{{ learning_unit_years }}/p>"


class TestSendMessage(TestCase):
    def setUp(self):
        self.person_1 = test_person.create_person("person_1", last_name="test", email="person1@test.com")
        self.person_2 = test_person.create_person("person_2", last_name="test", email="person2@test.com")
        self.persons = [self.person_1, self.person_2]

        self.person_3 = PersonWithPermissionsFactory("can_receive_emails_about_automatic_postponement")

        self.academic_year = test_academic_year.create_academic_year()
        test_academic_year.create_academic_year(year=self.academic_year.year - 1)

        self.learning_unit_year = LearningUnitYearFactory(acronym="TEST",
                                                          specific_title="Cours de test",
                                                          academic_year=self.academic_year)

        self.offer_year = test_offer_year.create_offer_year("SINF2MA", "Master en Sciences Informatique",
                                                            self.academic_year)

        self.exam_enrollment_1 = test_exam_enrollment.create_exam_enrollment_with_student(1, "64641200",
                                                                                          self.offer_year,
                                                                                          self.learning_unit_year)
        self.exam_enrollment_2 = test_exam_enrollment.create_exam_enrollment_with_student(2, "60601200",
                                                                                          self.offer_year,
                                                                                          self.learning_unit_year)

        self.msg_list = [
            'The partim TEST_A has been deleted for the year ' + str(self.academic_year.year),
            'The partim TEST_B has been deleted for the year ' + str(self.academic_year.year),
            'The class TEST_C has been deleted for the year ' + str(self.academic_year.year),
            'The class TEST_A_C1 has been deleted for the year ' + str(self.academic_year.year),
            'The class TEST_A_C2 has been deleted for the year ' + str(self.academic_year.year),
            'The class TEST_B_C1 has been deleted for the year ' + str(self.academic_year.year),
            'The class TEST_B_C2 has been deleted for the year ' + str(self.academic_year.year),
            'The learning unit TEST has been successfully deleted for all years'
        ]

        self.egys_to_postpone = EducationGroupYear.objects.all()
        self.egys_already_existing = EducationGroupYear.objects.all()
        self.egys_ending_this_year = EducationGroupYear.objects.all()

        self.luys_to_postpone = LearningUnitYear.objects.all()
        self.luys_already_existing = LearningUnitYear.objects.all()
        self.luys_ending_this_year = LearningUnitYear.objects.all()

        add_message_template_html()
        add_message_template_txt()

    @patch("osis_common.messaging.send_message.send_messages")
    def test_send_mail_after_the_learning_unit_year_deletion(self, mock_send_messages):
        send_mail.send_mail_after_the_learning_unit_year_deletion(
            self.persons,
            self.learning_unit_year.acronym,
            self.academic_year,
            self.msg_list
        )
        args = mock_send_messages.call_args[0][0]
        self.assertEqual(self.learning_unit_year.acronym, args.get('subject_data').get('learning_unit_acronym'))
        self.assertEqual(len(args.get('receivers')), 2)
        self.assertIsNone(args.get('attachment'))

    @patch("osis_common.messaging.send_message.send_messages")
    def test_send_mail_before_annual_procedure_of_automatic_postponement_of_luy(self, mock_send_messages):
        send_mail.send_mail_before_annual_procedure_of_automatic_postponement_of_luy(
            self.academic_year,
            self.luys_to_postpone,
            self.luys_already_existing,
            self.luys_ending_this_year
        )
        args = mock_send_messages.call_args[0][0]
        self.assertEqual(self.academic_year.year, args.get('template_base_data').get('end_academic_year'))
        self.assertEqual(len(args.get('receivers')), 1)
        self.assertIsNone(args.get('attachment'))

    @patch("osis_common.messaging.send_message.send_messages")
    def test_send_mail_after_annual_procedure_of_automatic_postponement_of_luy(self, mock_send_messages):
        send_mail.send_mail_after_annual_procedure_of_automatic_postponement_of_luy(
            self.academic_year,
            self.luys_to_postpone,
            self.luys_already_existing,
            self.luys_ending_this_year,
            self.msg_list
        )
        args = mock_send_messages.call_args[0][0]
        self.assertEqual(self.academic_year.year, args.get('template_base_data').get('end_academic_year'))
        self.assertEqual(len(args.get('receivers')), 1)
        self.assertIsNone(args.get('attachment'))

    @patch("osis_common.messaging.send_message.send_messages")
    def test_send_mail_before_annual_procedure_of_automatic_postponement_of_egy(self, mock_send_messages):
        send_mail.send_mail_before_annual_procedure_of_automatic_postponement_of_egy(
            self.academic_year,
            self.egys_to_postpone,
            self.egys_already_existing,
            self.egys_ending_this_year
        )
        args = mock_send_messages.call_args[0][0]
        self.assertEqual(self.academic_year.year, args.get('template_base_data').get('end_academic_year'))
        self.assertEqual(len(args.get('receivers')), 1)
        self.assertIsNone(args.get('attachment'))

    @patch("osis_common.messaging.send_message.send_messages")
    def test_send_mail_after_annual_procedure_of_automatic_postponement_of_egy(self, mock_send_messages):
        send_mail.send_mail_after_annual_procedure_of_automatic_postponement_of_egy(
            self.academic_year,
            self.egys_to_postpone,
            self.egys_already_existing,
            self.egys_ending_this_year,
            EducationGroup.objects.all()
        )
        args = mock_send_messages.call_args[0][0]
        self.assertEqual(self.academic_year.year, args.get('template_base_data').get('end_academic_year'))
        self.assertEqual(len(args.get('receivers')), 1)
        self.assertIsNone(args.get('attachment'))

    @patch("osis_common.messaging.send_message.send_messages")
    def test_with_one_enrollment(self, mock_send_messages):
        send_mail.send_message_after_all_encoded_by_manager(
            self.persons,
            [self.exam_enrollment_1],
            self.learning_unit_year.acronym,
            self.offer_year.acronym
        )
        args = mock_send_messages.call_args[0][0]
        self.assertEqual(self.learning_unit_year.acronym, args.get('subject_data').get('learning_unit_acronym'))
        self.assertEqual(self.offer_year.acronym, args.get('subject_data').get('offer_acronym'))
        self.assertEqual(len(args.get('receivers')), 2)
        self.assertIsNotNone(args.get('attachment'))

    @patch("osis_common.messaging.send_message.send_messages")
    def test_send_mail_for_educational_information_update(self, mock_send_messages):
        add_message_template_html_education_update()
        add_message_template_txt_education_update()
        send_mail.send_mail_for_educational_information_update([self.person_1], [self.learning_unit_year])
        args = mock_send_messages.call_args[0][0]
        self.assertEqual(len(args.get('receivers')), 1)
        self.assertEqual([self.learning_unit_year], args.get('template_base_data').get('learning_unit_years'))


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
                 "gestionnaire de parcours étudiant.</p>\r\n\r\n<p>{{ enrollments }}</p>\r\n\r\n<p>Osis UCLouvain."
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
                 "&eacute;t&eacute; valid&eacute;es par le gestionnaire de parcours étudiant.</p>\r\n\r\n"
                 "<p>{{ enrollments }}</p>\r\n\r\n<p>{{ signature }}</p>\r\n\r\n<p>{% endautoescape %}</p>",
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


def add_message_template_txt_education_update():
    msg_template = message_template.MessageTemplate(
        reference=send_mail.EDUCATIONAL_INFORMATION_UPDATE_TXT,
        subject="",
        template=LEARNING_UNIT_YEARS_VARIABLE_PARAGRAPH_,
        format="PLAIN",
        language="en"
    )
    msg_template.save()

    msg_template = message_template.MessageTemplate(
        reference=send_mail.EDUCATIONAL_INFORMATION_UPDATE_TXT,
        subject="",
        template=LEARNING_UNIT_YEARS_VARIABLE_PARAGRAPH_,
        format="PLAIN",
        language="fr-be"
    )
    msg_template.save()


def add_message_template_html_education_update():
    msg_template = message_template.MessageTemplate(
        reference=send_mail.EDUCATIONAL_INFORMATION_UPDATE_HTML,
        subject="",
        template="<p>{% autoescape off %}</p>"
                 "<p>{{ learning_unit_years }}</p>\r\n\r\n"
                 "<p>{% endautoescape %}</p>",
        format="HTML",
        language="fr-be"
    )
    msg_template.save()

    msg_template = message_template.MessageTemplate(
        reference=send_mail.EDUCATIONAL_INFORMATION_UPDATE_HTML,
        subject="",
        template="<p>{% autoescape off %}</p>"
                 "<p>{{ learning_unit_years }}</p>\r\n\r\n"
                 "<p>{% endautoescape %}</p>",
        format="HTML",
        language="en"
    )
    msg_template.save()
