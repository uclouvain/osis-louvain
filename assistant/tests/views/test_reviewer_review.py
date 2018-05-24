##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime

from django.test import TestCase, RequestFactory, Client

from base.models.enums import entity_type
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory


from assistant.models.enums import assistant_mandate_state, review_status, reviewer_role
from assistant.tests.factories.academic_assistant import AcademicAssistantFactory
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.mandate_entity import MandateEntityFactory
from assistant.tests.factories.review import ReviewFactory
from assistant.tests.factories.reviewer import ReviewerFactory
from assistant.tests.factories.settings import SettingsFactory
from assistant.views.reviewer_review import generate_reviewer_menu_tabs
from assistant.views.reviewer_review import validate_review_and_update_mandate

HTTP_OK = 200


class ReviewerReviewViewTestCase(TestCase):

    def setUp(self):

        self.factory = RequestFactory()
        self.client = Client()
        self.settings = SettingsFactory()
        today = datetime.date.today()
        self.current_academic_year = AcademicYearFactory(start_date=today,
                                                         end_date=today.replace(year=today.year + 1),
                                                         year=today.year)
        self.current_academic_year.save()
        self.phd_supervisor = PersonFactory()
        self.assistant = AcademicAssistantFactory(supervisor=self.phd_supervisor)

        self.assistant_mandate = AssistantMandateFactory(
            academic_year=self.current_academic_year,
            assistant=self.assistant,
            state=assistant_mandate_state.RESEARCH
        )
        self.assistant_mandate2 = AssistantMandateFactory(
            academic_year=self.current_academic_year,
            assistant=self.assistant,
            state=assistant_mandate_state.RESEARCH
        )
        self.phd_supervisor_review = ReviewFactory(
            reviewer=None,
            mandate=self.assistant_mandate,
            status=review_status.DONE
        )
        self.entity_version = EntityVersionFactory(entity_type=entity_type.INSTITUTE)
        self.entity_mandate = MandateEntityFactory(assistant_mandate=self.assistant_mandate,
                                                   entity=self.entity_version.entity)
        self.entity_mandate2 = MandateEntityFactory(
            assistant_mandate=self.assistant_mandate2,
            entity=self.entity_version.entity
        )
        self.reviewer = ReviewerFactory(role=reviewer_role.RESEARCH,
                                        entity=self.entity_version.entity)
        self.review = ReviewFactory(reviewer=self.reviewer, mandate=self.assistant_mandate,
                                    status=review_status.IN_PROGRESS)
        self.entity_version2 = EntityVersionFactory(entity_type=entity_type.FACULTY)
        self.entity_mandate2 = MandateEntityFactory(
            assistant_mandate=self.assistant_mandate,
            entity=self.entity_version2.entity
        )
        self.reviewer2 = ReviewerFactory(
            role=reviewer_role.SUPERVISION,
            entity=self.entity_version2.entity
        )
        self.entity_version3 = EntityVersionFactory(entity_type=entity_type.SECTOR)
        self.entity_mandate3 = MandateEntityFactory(
            assistant_mandate=self.assistant_mandate,
            entity=self.entity_version3.entity
        )
        self.reviewer3 = ReviewerFactory(
            role=reviewer_role.VICE_RECTOR,
            entity=self.entity_version3.entity
        )

    def test_pst_form_view(self):
        self.client.force_login(self.reviewer.person.user)
        response = self.client.post('/assistants/reviewer/pst_form/', {'mandate_id': self.assistant_mandate.id})
        self.assertEqual(response.status_code, HTTP_OK)

    def test_review_edit(self):
        self.client.force_login(self.reviewer.person.user)
        response = self.client.post('/assistants/reviewer/review/edit/', {'mandate_id': self.assistant_mandate2.id})
        self.assertEqual(response.status_code, HTTP_OK)

    def test_review_save(self):
        self.client.force_login(self.reviewer.person.user)
        response = self.client.post('/assistants/reviewer/review/save/', {'mandate_id': self.assistant_mandate.id,
                                                                          'review_id': self.review.id
                                                                          })
        self.assertEqual(response.status_code, HTTP_OK)

    def test_validate_review_and_update_mandate(self):
        validate_review_and_update_mandate(self.review, self.assistant_mandate)
        self.assertEqual(self.review.status, review_status.DONE)
        self.assertEqual(self.assistant_mandate.state, assistant_mandate_state.SUPERVISION)
        self.review2 = ReviewFactory(
            reviewer=self.reviewer2, mandate=self.assistant_mandate,
            status=review_status.IN_PROGRESS
        )
        validate_review_and_update_mandate(self.review2, self.assistant_mandate)
        self.assertEqual(self.review2.status, review_status.DONE)
        self.assertEqual(self.assistant_mandate.state, assistant_mandate_state.VICE_RECTOR)
        self.review3 = ReviewFactory(reviewer=self.reviewer3, mandate=self.assistant_mandate,
                                     status=review_status.IN_PROGRESS)
        validate_review_and_update_mandate(self.review3, self.assistant_mandate)
        self.assertEqual(self.review3.status, review_status.DONE)
        self.assertEqual(self.assistant_mandate.state, assistant_mandate_state.DONE)

    def test_review_view(self):
        self.client.force_login(self.reviewer.person.user)
        response = self.client.post('/assistants/reviewer/review/view/', {'mandate_id': self.assistant_mandate.id,
                                                                          'role': reviewer_role.PHD_SUPERVISOR})
        self.assertEqual(response.status_code, HTTP_OK)
        response = self.client.post('/assistants/reviewer/review/view/', {'mandate_id': self.assistant_mandate.id,
                                                                          'role': reviewer_role.RESEARCH})
        self.assertEqual(response.status_code, HTTP_OK)

    def test_generate_reviewer_menu_tabs(self):
        self.client.force_login(self.reviewer.person.user)
        self.assertEqual([{'action': 'view', 'class': '', 'item': 'PHD_SUPERVISOR'},
                          {'item': 'RESEARCH', 'class': '', 'action': 'edit'}],
                         generate_reviewer_menu_tabs(reviewer_role.RESEARCH, self.assistant_mandate, None))
        self.review.status = review_status.DONE
        self.review.save()
        self.assistant_mandate.state = assistant_mandate_state.SUPERVISION
        self.assistant_mandate.save()
        self.review2 = ReviewFactory(
            reviewer=self.reviewer2,
            mandate=self.assistant_mandate,
            status=review_status.IN_PROGRESS
        )
        self.assertEqual([{'action': 'view', 'class': '', 'item': 'PHD_SUPERVISOR'},
                          {'item': 'RESEARCH', 'class': 'active', 'action': 'view'}],
                         generate_reviewer_menu_tabs(reviewer_role.RESEARCH, self.assistant_mandate,
                                                     assistant_mandate_state.RESEARCH))
        self.assertEqual([{'action': 'view', 'class': '', 'item': 'PHD_SUPERVISOR'},
                          {'item': 'RESEARCH', 'class': '', 'action': 'view'},
                          {'item': 'SUPERVISION', 'class': '', 'action': 'edit'}],
                         generate_reviewer_menu_tabs(reviewer_role.SUPERVISION, self.assistant_mandate, None))
