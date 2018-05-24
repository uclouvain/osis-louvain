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

import json
from django.test import TestCase
from django.core.urlresolvers import reverse
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.person import PersonFactory, PersonWithoutUserFactory
from base.tests.factories.offer import OfferFactory
from base.tests.factories.student import StudentFactory
from dissertation.tests.factories.adviser import AdviserManagerFactory, AdviserTeacherFactory
from dissertation.tests.factories.dissertation import DissertationFactory
from dissertation.tests.factories.faculty_adviser import FacultyAdviserFactory
from dissertation.tests.factories.offer_proposition import OfferPropositionFactory
from dissertation.tests.factories.proposition_dissertation import PropositionDissertationFactory
from dissertation.tests.factories.proposition_offer import PropositionOfferFactory
from osis_common.models import message_history
from osis_common.models import message_template
from dissertation.models import adviser
from dissertation.models import dissertation_role
from dissertation.tests.models.test_faculty_adviser import create_faculty_adviser
from dissertation.views.dissertation import adviser_can_manage

ERROR_405_BAD_REQUEST = 405
ERROR_404_PAGE_NO_FOUND = 404
HTTP_OK = 200
ERROR_403_NOT_AUTORIZED = 403
MAXIMUM_IN_REQUEST = 50


class DissertationViewTestCase(TestCase):
    fixtures = ['dissertation/fixtures/message_template.json', ]

    def setUp(self):
        self.maxDiff = None
        self.manager = AdviserManagerFactory()
        a_person_teacher = PersonFactory.create(first_name='Pierre',
                                                last_name='Dupont',
                                                email='laurent.dermine@uclouvain.be')
        self.teacher = AdviserTeacherFactory(person=a_person_teacher)
        a_person_teacher2 = PersonFactory.create(first_name='Marco',
                                                 last_name='Millet',
                                                 email='laurent.dermine@uclouvain.be')
        self.teacher2 = AdviserTeacherFactory(person=a_person_teacher2)
        a_person_student = PersonWithoutUserFactory.create(last_name="Durant",
                                                           email='laurent.dermine@uclouvain.be')
        self.student = StudentFactory.create(person=a_person_student)
        self.offer1 = OfferFactory(title="test_offer1")
        self.offer2 = OfferFactory(title="test_offer2")
        self.academic_year1 = AcademicYearFactory()
        self.academic_year2 = AcademicYearFactory(year=self.academic_year1.year - 1)
        self.offer_year_start1 = OfferYearFactory(acronym="test_offer1", offer=self.offer1,
                                                  academic_year=self.academic_year1)
        self.offer_year_start2 = OfferYearFactory(acronym="test_offer2", offer=self.offer2,
                                                  academic_year=self.academic_year1)
        self.offer_proposition1 = OfferPropositionFactory(offer=self.offer1,
                                                          global_email_to_commission=True,
                                                          evaluation_first_year=True)
        self.offer_proposition2 = OfferPropositionFactory(offer=self.offer2, global_email_to_commission=False)
        self.proposition_dissertation = PropositionDissertationFactory(author=self.teacher,
                                                                       creator=a_person_teacher,
                                                                       title='Proposition 1212121'
                                                                       )
        FacultyAdviserFactory(adviser=self.manager, offer=self.offer1)
        self.dissertation_test_email = DissertationFactory(author=self.student,
                                                           title='Dissertation_test_email',
                                                           offer_year_start=self.offer_year_start1,
                                                           proposition_dissertation=self.proposition_dissertation,
                                                           status='DRAFT',
                                                           active=True,
                                                           dissertation_role__adviser=self.teacher,
                                                           dissertation_role__status='PROMOTEUR'
                                                           )

        FacultyAdviserFactory(adviser=self.manager, offer=self.offer1)
        self.manager2 = AdviserManagerFactory()
        FacultyAdviserFactory(adviser=self.manager, offer=self.offer2)
        roles = ['PROMOTEUR', 'CO_PROMOTEUR', 'READER', 'PROMOTEUR', 'ACCOMPANIST', 'PRESIDENT']
        status = ['DRAFT', 'COM_SUBMIT', 'EVA_SUBMIT', 'TO_RECEIVE', 'DIR_SUBMIT', 'DIR_SUBMIT']
        self.dissertations_list = list()
        for x in range(0, 6):
            proposition_dissertation = PropositionDissertationFactory(author=self.teacher,
                                                                      creator=a_person_teacher,
                                                                      title='Proposition {}'.format(x)
                                                                      )
            PropositionOfferFactory(proposition_dissertation=proposition_dissertation,
                                    offer_proposition=self.offer_proposition1)

            self.dissertations_list.append(DissertationFactory(
                author=self.student,
                title='Dissertation {}'.format(x),
                offer_year_start=self.offer_year_start1,
                proposition_dissertation=proposition_dissertation,
                status=status[x],
                active=True,
                dissertation_role__adviser=self.teacher,
                dissertation_role__status=roles[x]
            ))
        self.dissertation_1 = DissertationFactory(author=self.student,
                                                  title='Dissertation 2017',
                                                  offer_year_start=self.offer_year_start1,
                                                  proposition_dissertation=proposition_dissertation,
                                                  status='COM_SUBMIT',
                                                  active=True,
                                                  dissertation_role__adviser=self.teacher2,
                                                  dissertation_role__status='PROMOTEUR')

    def test_get_dissertations_list_for_teacher(self):
        self.client.force_login(self.teacher.person.user)
        url = reverse('dissertations_list')
        response = self.client.get(url)
        self.assertEqual(response.context[-1]['adviser_list_dissertations'].count(), 1)  # only 1 because 1st is DRAFT
        self.assertEqual(response.context[-1]['adviser_list_dissertations_copro'].count(), 1)
        self.assertEqual(response.context[-1]['adviser_list_dissertations_reader'].count(), 1)
        self.assertEqual(response.context[-1]['adviser_list_dissertations_accompanist'].count(), 1)
        self.assertEqual(response.context[-1]['adviser_list_dissertations_president'].count(), 1)

    def test_get_dissertations_list_for_manager(self):
        self.client.force_login(self.manager.person.user)
        url = reverse('manager_dissertations_list')
        response = self.client.get(url)
        self.assertEqual(response.context[-1]['dissertations'].count(), 8)
        self.assertCountEqual(response.context[-1]['dissertations'], [self.dissertation_1] +
                              [self.dissertation_test_email] + self.dissertations_list)

    def test_search_dissertations_for_manager_1(self):
        self.client.force_login(self.manager.person.user)
        url = reverse('manager_dissertations_search')
        response = self.client.get(url, data={"search": "no result search"})
        self.assertEqual(response.status_code, HTTP_OK)

    def test_search_dissertations_for_manager_2(self):
        self.client.force_login(self.manager.person.user)
        url = reverse('manager_dissertations_search')
        response = self.client.get(url, data={"search": "Dissertation 2"})
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertEqual(response.context[-1]['dissertations'].count(), 2)
        self.assertCountEqual(
            response.context[-1]['dissertations'],
            [self.dissertation_1, self.dissertations_list[2]]
        )

    def test_search_dissertations_for_manager_3(self):
        self.client.force_login(self.manager.person.user)
        url = reverse('manager_dissertations_search')
        response = self.client.get(url, data={"search": "Proposition 3"})
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertEqual(response.context[-1]['dissertations'].count(), 1)
        self.assertCountEqual(
            response.context[-1]['dissertations'],
            [self.dissertations_list[3]]
        )

    def test_search_dissertations_for_manager_4(self):
        self.client.force_login(self.manager.person.user)
        url = reverse('manager_dissertations_search')
        response = self.client.get(url, data={"search": "Dissertation"})
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertEqual(response.context[-1]['dissertations'].count(), 8)
        self.assertCountEqual(response.context[-1]['dissertations'], [self.dissertation_1] +
                              [self.dissertation_test_email] + self.dissertations_list)

    def test_search_dissertations_for_manager_5(self):
        self.client.force_login(self.manager.person.user)
        url = reverse('manager_dissertations_search')
        response = self.client.get(url, data={"search": "Dissertation",
                                              "offer_prop_search": self.offer_proposition1.id})
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertEqual(response.context[-1]['dissertations'].count(), 8)
        self.assertCountEqual(response.context[-1]['dissertations'], [self.dissertation_1] +
                              [self.dissertation_test_email] + self.dissertations_list)

    def test_search_dissertations_for_manager_6(self):
        self.client.force_login(self.manager.person.user)
        url = reverse('manager_dissertations_search')
        response = self.client.get(url, data={"search": "Dissertation",
                                              "offer_prop_search": self.offer_proposition2.id})
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertEqual(response.context[-1]['dissertations'].count(), 0)

    def test_search_dissertations_for_manager_7(self):
        self.client.force_login(self.manager.person.user)
        url = reverse('manager_dissertations_search')
        response = self.client.get(url, data={"academic_year": self.academic_year1.id})
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertEqual(response.context[-1]['dissertations'].count(), 8)
        self.assertCountEqual(response.context[-1]['dissertations'], [self.dissertation_1] +
                              [self.dissertation_test_email] + self.dissertations_list)

    def test_search_dissertations_for_manager_8(self):
        self.client.force_login(self.manager.person.user)
        url = reverse('manager_dissertations_search')
        response = self.client.get(url, data={"academic_year": self.academic_year2.id})
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertEqual(response.context[-1]['dissertations'].count(), 0)

    def test_search_dissertations_for_manager_9(self):
        self.client.force_login(self.manager.person.user)
        url = reverse('manager_dissertations_search')
        response = self.client.get(url, data={"status_search": "COM_SUBMIT"})
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertEqual(response.context[-1]['dissertations'].count(), 2)

    def test_search_dissertations_for_manager_10(self):
        self.client.force_login(self.manager.person.user)
        url = reverse('manager_dissertations_search')
        response = self.client.get(url, data={"search": "test_offer"})
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertEqual(response.context[-1]['dissertations'].count(), 8)
        self.assertCountEqual(response.context[-1]['dissertations'], [self.dissertation_1] +
                              [self.dissertation_test_email] + self.dissertations_list)

    def test_search_dissertations_for_manager_11(self):
        self.client.force_login(self.manager.person.user)
        url = reverse('manager_dissertations_search')
        response = self.client.get(url, data={"search": "Durant"})
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertEqual(response.context[-1]['dissertations'].count(), 8)
        self.assertCountEqual(response.context[-1]['dissertations'], [self.dissertation_1] +
                              [self.dissertation_test_email] + self.dissertations_list)

    def test_search_dissertations_for_manager_12(self):
        self.client.force_login(self.manager.person.user)
        url = reverse('manager_dissertations_search')
        response = self.client.get(url, data={"search": "Dupont"})
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertEqual(response.context[-1]['dissertations'].count(), 8)
        self.assertCountEqual(response.context[-1]['dissertations'], [self.dissertation_1] +
                              [self.dissertation_test_email] + self.dissertations_list)

    def test_manager_accept(self):
        self.dissertation_test_email.status = 'EVA_SUBMIT'
        self.dissertation_test_email.manager_accept()
        self.assertEqual(self.dissertation_test_email.status, 'TO_RECEIVE')
        self.dissertation_test_email.status = 'EVA_KO'
        self.dissertation_test_email.manager_accept()
        self.assertEqual(self.dissertation_test_email.status, 'TO_RECEIVE')
        self.dissertation_test_email.status = 'DEFENDED'
        self.dissertation_test_email.manager_accept()
        self.assertEqual(self.dissertation_test_email.status, 'ENDED_WIN')
        self.dissertation_test_email.status = 'DRAFT'
        self.dissertation_test_email.manager_accept()
        self.assertEqual(self.dissertation_test_email.status, 'DRAFT')

    def test_adviser_can_manage_dissertation(self):
        manager = AdviserManagerFactory()
        manager2 = AdviserManagerFactory()
        a_person_teacher = PersonFactory.create(first_name='Pierre', last_name='Dupont')
        a_person_teacher2 = PersonFactory.create(first_name='Marco', last_name='Millet')
        teacher = AdviserTeacherFactory(person=a_person_teacher)
        a_person_student = PersonWithoutUserFactory.create(last_name="Durant")
        student = StudentFactory.create(person=a_person_student)
        offer_year_start = OfferYearFactory(academic_year=self.academic_year1, acronym="test_offer2")
        offer_year_start2 = OfferYearFactory(acronym="test_offer3", academic_year=offer_year_start.academic_year)
        offer = offer_year_start.offer
        offer2 = offer_year_start2.offer
        FacultyAdviserFactory(adviser=manager, offer=offer)
        create_faculty_adviser(manager, offer)
        create_faculty_adviser(manager2, offer2)
        proposition_dissertation = PropositionDissertationFactory(author=teacher,
                                                                  creator=a_person_teacher,
                                                                  title='Proposition1')
        dissertation = DissertationFactory(author=student,
                                           title='Dissertation 2017',
                                           offer_year_start=offer_year_start,
                                           proposition_dissertation=proposition_dissertation,
                                           status='DIR_SUBMIT',
                                           active=True,
                                           dissertation_role__adviser=teacher,
                                           dissertation_role__status='PROMOTEUR')
        self.assertEqual(adviser_can_manage(dissertation, manager), True)
        self.assertEqual(adviser_can_manage(dissertation, manager2), False)
        self.assertEqual(adviser_can_manage(dissertation, teacher), False)

    def test_email_new_dissert(self):
        self.client.force_login(self.manager.person.user)
        count_messages_before_status_change = message_history.find_my_messages(self.teacher.person.id).count()
        self.dissertation_test_email.status = 'DRAFT'
        self.dissertation_test_email.go_forward()
        message_history_result = message_history.find_my_messages(self.teacher.person.id)
        self.assertEqual(count_messages_before_status_change + 1, len(message_history_result))
        self.assertIsNotNone(message_template.find_by_reference('dissertation_adviser_new_project_dissertation_txt'))
        self.assertIsNotNone(message_template.find_by_reference('dissertation_adviser_new_project_dissertation_html'))
        self.assertIn('Vous avez reçu une demande d\'encadrement de mémoire', message_history_result.last().subject)

    def test_email_new_dissert_refuse(self):
        count_messages_before_status_change = message_history.find_my_messages(
            self.dissertation_test_email.author.person.id).count()
        self.dissertation_test_email.status = 'DIR_SUBMIT'
        self.dissertation_test_email.refuse()
        message_history_result = message_history.find_my_messages(self.dissertation_test_email.author.person.id)
        self.assertEqual(count_messages_before_status_change + 1, len(message_history_result))
        self.assertIn('Votre projet de mémoire n\'a pas été validé par votre promoteur',
                      message_history_result.last().subject)

    def test_email_new_dissert_accept(self):
        count_messages_before_status_change = message_history.find_my_messages(
            self.dissertation_test_email.author.person.id).count()
        self.dissertation_test_email.status = 'DIR_SUBMIT'
        self.dissertation_test_email.go_forward()
        self.dissertation_test_email.manager_accept()
        message_history_result_after = message_history.find_my_messages(self.dissertation_test_email.author.person.id)
        self.assertIn('Votre projet de mémoire est validé par votre promoteur',
                      message_history_result_after.last().subject)
        self.assertEqual(count_messages_before_status_change + 1, len(message_history_result_after))

    def test_email_dissert_commission_refuse(self):
        count_message_history_result_author = message_history. \
            find_my_messages(self.dissertation_test_email.author.person.id).count()
        count_message_history_result_promotor = len(message_history.find_my_messages(
            self.teacher.person.id))
        self.dissertation_test_email.status = 'COM_SUBMIT'
        self.dissertation_test_email.refuse()
        message_history_result_author_after_change = message_history.find_my_messages(
            self.dissertation_test_email.author.person.id)
        message_history_result_promotor_after_change = message_history.find_my_messages(self.teacher.person.id)
        self.assertEqual(count_message_history_result_author + 1, len(message_history_result_author_after_change))
        self.assertEqual(count_message_history_result_promotor + 1, len(message_history_result_promotor_after_change))
        self.assertIn('La commission Mémoires n\'a pas validé le projet de mémoire',
                      message_history_result_promotor_after_change.last().subject)
        self.assertIn('La commission Mémoires n\'a pas validé votre projet de mémoire',
                      message_history_result_author_after_change.last().subject)

    def test_email_dissert_commission_accept_1(self):
        count_message_history_result_author = message_history. \
            find_my_messages(self.dissertation_test_email.author.person.id).count()
        count_message_history_result_promotor = len(message_history.find_my_messages(
            self.teacher.person.id))
        self.dissertation_test_email.status = 'COM_KO'
        self.dissertation_test_email.manager_accept()
        message_history_result_author_after_change = message_history.find_my_messages(
            self.dissertation_test_email.author.person.id)
        message_history_result_promotor_after_change = message_history.find_my_messages(self.teacher.person.id)
        self.assertEqual(count_message_history_result_author + 1, len(message_history_result_author_after_change))
        self.assertEqual(count_message_history_result_promotor + 1, len(message_history_result_promotor_after_change))
        self.assertIn('La commission Mémoires a accepté le projet de Mémoire :',
                      message_history_result_promotor_after_change.last().subject)
        self.assertIn('La commission Mémoires a accepté votre projet de mémoire',
                      message_history_result_author_after_change.last().subject)

    def test_email_dissert_commission_accept_2(self):
        count_message_history_result_author = message_history. \
            find_my_messages(self.dissertation_test_email.author.person.id).count()
        count_message_history_result_promotor = len(message_history.find_my_messages(
            self.teacher.person.id))
        self.dissertation_test_email.status = 'COM_SUBMIT'
        self.dissertation_test_email.manager_accept()
        message_history_result_author_after_change = message_history.find_my_messages(
            self.dissertation_test_email.author.person.id)
        message_history_result_promotor_after_change = message_history.find_my_messages(self.teacher.person.id)
        self.assertEqual(count_message_history_result_author + 1, len(message_history_result_author_after_change))
        self.assertEqual(count_message_history_result_promotor + 1, len(message_history_result_promotor_after_change))
        self.assertIn('La commission Mémoires a accepté le projet de Mémoire :',
                      message_history_result_promotor_after_change.last().subject)
        self.assertIn('La commission Mémoires a accepté votre projet de mémoire',
                      message_history_result_author_after_change.last().subject)

    def test_email_dissert_commission_accept_3(self):
        dissert = DissertationFactory(author=self.student,
                                      title='Dissertation_test_email',
                                      offer_year_start=self.offer_year_start2,
                                      proposition_dissertation=self.proposition_dissertation,
                                      status='COM_SUBMIT',
                                      active=True,
                                      dissertation_role__adviser=self.teacher,
                                      dissertation_role__status='PROMOTEUR')
        count_message_history_result_author = \
            message_history.find_my_messages(dissert.author.person.id).count()
        count_message_history_result_promotor = \
            message_history.find_my_messages(self.teacher.person.id).count()
        dissert.manager_accept()
        message_history_result_author_after_change = message_history.find_my_messages(
            dissert.author.person.id)
        message_history_result_promotor_after_change = message_history.find_my_messages(self.teacher.person.id)
        self.assertEqual(count_message_history_result_author + 1, len(message_history_result_author_after_change))
        self.assertEqual(count_message_history_result_promotor, len(message_history_result_promotor_after_change))
        self.assertIn('La commission Mémoires a accepté votre projet de mémoire',
                      message_history_result_author_after_change.last().subject)

    def test_email_dissert_acknowledgement(self):
        count_message_history_author = message_history. \
            find_my_messages(self.dissertation_test_email.author.person.id).count()
        self.dissertation_test_email.status = 'TO_RECEIVE'
        self.dissertation_test_email.go_forward()
        message_history_result_author_after_change = message_history.find_my_messages(
            self.dissertation_test_email.author.person.id)
        count_message_history_result_author = len(message_history_result_author_after_change)
        self.assertEqual(count_message_history_author + 1, count_message_history_result_author)
        self.assertIn('bien été réceptionné', message_history_result_author_after_change.last().subject)

    def test_get_all_advisers(self):
        res = adviser.find_all_advisers()
        self.assertEqual(res.count(), 4)

    def test_find_by_last_name_or_email(self):
        res = adviser.find_advisers_last_name_email('Dupont', MAXIMUM_IN_REQUEST)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].person.last_name, 'Dupont')
        res = adviser.find_advisers_last_name_email(None, MAXIMUM_IN_REQUEST)
        self.assertEqual(len(res), 0)

    def test_get_adviser_list_json(self):
        self.client.force_login(self.manager.person.user)
        response = self.client.get('/dissertation/find_adviser_list/', {'term': 'Dupont'})
        self.assertEqual(response.status_code, HTTP_OK)
        data_json = response.json()
        self.assertNotEqual(len(data_json), 0)
        for data in data_json:
            self.assertEqual(data['last_name'], 'Dupont')

    def test_manager_dissert_jury_new_by_ajax1(self):
        self.client.force_login(self.manager.person.user)
        dissert_role_count = dissertation_role.count_by_dissertation(self.dissertation_1)
        response = self.client.post('/dissertation/manager_dissertations_jury_new_ajax/',
                                    {'pk_dissertation': str(self.dissertation_1.id)})
        self.assertEqual(response.status_code, ERROR_405_BAD_REQUEST)
        response = self.client.get('/dissertation/manager_dissertations_jury_new_ajax/', {
            'pk_dissertation': str(self.dissertation_1.id)})
        self.assertEqual(response.status_code, ERROR_405_BAD_REQUEST)
        response = self.client.post('/dissertation/manager_dissertations_jury_new_ajax/',
                                    {'pk_dissertation': str(self.dissertation_1.id), 'status_choice': 'READER'})
        self.assertEqual(response.status_code, ERROR_405_BAD_REQUEST)
        response = self.client.post('/dissertation/manager_dissertations_jury_new_ajax/',
                                    {'pk_dissertation': str(self.dissertation_1.id),
                                     'status_choice': 'READER',
                                     'adviser_pk': str(self.teacher.id)})
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertEqual(dissert_role_count + 1, dissertation_role.count_by_dissertation(self.dissertation_1))

    def test_manager_dissert_jury_del_by_ajax(self):
        self.client.force_login(self.manager.person.user)
        response = self.client.post('/dissertation/manager_dissertations_jury_new_ajax/',
                                    {'pk_dissertation': str(self.dissertation_1.id),
                                     'status_choice': 'READER',
                                     'adviser_pk': str(self.teacher.id)})
        self.assertEqual(response.status_code, HTTP_OK)
        liste_dissert_roles = dissertation_role.search_by_dissertation_and_role(self.dissertation_1, 'READER')
        self.assertNotEqual(len(liste_dissert_roles), 0)
        for element in liste_dissert_roles:
            dissert_role_count = dissertation_role.count_by_dissertation(self.dissertation_1)
            url = "/dissertation/manager_dissertations_role_delete_by_ajax/{role}"
            response2 = self.client.get(url.format(role=str(element.id)))
            self.assertEqual(response2.status_code, HTTP_OK)
            self.assertEqual(dissertation_role.count_by_dissertation(self.dissertation_1), dissert_role_count - 1)

    def test_manager_dissert_wait_comm_jsonlist(self):
        self.client.force_login(self.manager.person.user)
        response = self.client.post('/dissertation/manager_dissertations_wait_comm_json_list', )
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertEqual(len(response_data), 2)

    def test_manager_dissert_jury_security_ajax(self):
        self.client.force_login(self.manager2.person.user)
        response = self.client.post('/dissertation/manager_dissertations_jury_new_ajax/',
                                    {'pk_dissertation': str(self.dissertation_1.id),
                                     'status_choice': 'READER',
                                     'adviser_pk': str(self.teacher.id)})
        self.assertEqual(response.status_code, ERROR_403_NOT_AUTORIZED)
        liste_dissert_roles = dissertation_role.search_by_dissertation_and_role(self.dissertation_1, 'READER')
        for element in liste_dissert_roles:
            url = "/dissertation/manager_dissertations_role_delete_by_ajax/{role}"
            response = self.client.get(url.format(role=str(element.id)))
            self.assertEqual(response.status_code, ERROR_403_NOT_AUTORIZED)

    def test_manager_students_list(self):
        self.client.force_login(self.manager.person.user)
        url = reverse('manager_students_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTP_OK)
