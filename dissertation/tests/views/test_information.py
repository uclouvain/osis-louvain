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
from django.test import TestCase
from django.core.urlresolvers import reverse
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.person import PersonFactory, PersonWithoutUserFactory
from base.tests.factories.student import StudentFactory
from dissertation.tests.factories.adviser import AdviserManagerFactory, AdviserTeacherFactory
from dissertation.tests.factories.dissertation import DissertationFactory
from dissertation.tests.factories.faculty_adviser import FacultyAdviserFactory
from dissertation.tests.factories.offer_proposition import OfferPropositionFactory
from dissertation.tests.factories.proposition_dissertation import PropositionDissertationFactory
from dissertation.tests.factories.proposition_offer import PropositionOfferFactory


class InformationViewTestCase(TestCase):

    def setUp(self):
        self.manager = AdviserManagerFactory()
        a_person_teacher = PersonFactory(first_name='Pierre', last_name='Dupont')
        self.teacher = AdviserTeacherFactory(person=a_person_teacher)
        a_person_student = PersonWithoutUserFactory(last_name="Durant")
        student = StudentFactory(person=a_person_student)

        offer_year_start = OfferYearFactory(acronym="test_offer")
        offer = offer_year_start.offer
        offer_proposition = OfferPropositionFactory(offer=offer)
        FacultyAdviserFactory(adviser=self.manager, offer=offer)

        roles = ['PROMOTEUR', 'CO_PROMOTEUR', 'READER', 'PROMOTEUR', 'ACCOMPANIST', 'PRESIDENT']
        status = ['DRAFT', 'COM_SUBMIT', 'EVA_SUBMIT', 'TO_RECEIVE', 'DIR_SUBMIT', 'DIR_SUBMIT']

        for x in range(0, 6):
            proposition_dissertation = PropositionDissertationFactory(author=self.teacher,
                                                                      creator=a_person_teacher,
                                                                      title='Proposition {}'.format(x)
                                                                      )
            PropositionOfferFactory(proposition_dissertation=proposition_dissertation,
                                    offer_proposition=offer_proposition)

            DissertationFactory(author=student,
                                title='Dissertation {}'.format(x),
                                offer_year_start=offer_year_start,
                                proposition_dissertation=proposition_dissertation,
                                status=status[x],
                                active=True,
                                dissertation_role__adviser=self.teacher,
                                dissertation_role__status=roles[x]
                                )

    def test_manager_informations_detail_list(self):
        self.client.force_login(self.manager.person.user)
        url = reverse('manager_informations_detail_list', kwargs={'pk': self.teacher.id})
        response = self.client.get(url)
        self.assertEqual(response.context[-1].get('adv_list_disserts_pro').count(), 1) # only 1 because 1st is DRAFT
        self.assertEqual(response.context[-1].get('adv_list_disserts_copro').count(), 1)
        self.assertEqual(response.context[-1].get('adv_list_disserts_reader').count(), 1)
        self.assertEqual(response.context[-1].get('adv_list_disserts_accompanist').count(), 1)
        self.assertEqual(response.context[-1].get('adv_list_disserts_president').count(), 1)
