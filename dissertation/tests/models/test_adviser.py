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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.contrib.auth.models import User
from django.test import TestCase
from base.models.person import Person
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.person import PersonFactory, PersonWithoutUserFactory
from base.tests.factories.offer import OfferFactory
from base.tests.factories.student import StudentFactory
from dissertation.models import adviser
from dissertation.tests.factories.adviser import AdviserManagerFactory, AdviserTeacherFactory
from dissertation.tests.factories.dissertation import DissertationFactory
from dissertation.tests.factories.faculty_adviser import FacultyAdviserFactory
from dissertation.tests.factories.offer_proposition import OfferPropositionFactory
from dissertation.tests.factories.proposition_dissertation import PropositionDissertationFactory
from dissertation.tests.factories.dissertation_role import DissertationRoleFactory


def create_adviser(person, type="PRF"):
    adv = adviser.Adviser.objects.create(person=person, type=type)
    return adv


def create_adviser_from_user(user, type="PRF"):
    person = Person.objects.create(user=user, first_name=user.username, last_name=user.username)
    return create_adviser(person, type)


def create_adviser_from_scratch(username, email, password, type="PRF"):
    user = User.objects.create_user(username=username, email=email, password=password)
    return create_adviser_from_user(user, type)


class UtilsTestCase(TestCase):
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
        self.teacher3 = AdviserTeacherFactory()
        self.teacher4 = AdviserTeacherFactory()
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
        self.dissertation1 = DissertationFactory(author=self.student,
                                                 title='Dissertation_test_email',
                                                 offer_year_start=self.offer_year_start1,
                                                 proposition_dissertation=self.proposition_dissertation,
                                                 status='DIR_SUBMIT',
                                                 active=True,
                                                 dissertation_role__adviser=self.teacher,
                                                 dissertation_role__status='PROMOTEUR'
                                                 )
        DissertationRoleFactory(adviser=self.teacher2, status='CO_PROMOTEUR', dissertation=self.dissertation1)
        DissertationRoleFactory(adviser=self.teacher3, status='READER', dissertation=self.dissertation1)

    def test_convert_none_to_empty_str(self):
        self.assertEqual(adviser.none_to_str(None), '')
        self.assertEqual(adviser.none_to_str('toto'), 'toto')

    def test_get_stat_dissertation_role(self):
        # list_stat[0]= count dissertation_role active of adviser
        # list_stat[1]= count dissertation_role Promoteur active of adviser
        # list_stat[2]= count dissertation_role coPromoteur active of adviser
        # list_stat[3]= count dissertation_role reader active of adviser
        # list_stat[4]= count dissertation_role need request active of adviser
        list_stat, tab_offer_count_read, tab_offer_count_copro, tab_offer_count_pro = \
            self.teacher.get_stat_dissertation_role
        self.assertEqual(list_stat[0], 1)
        self.assertEqual(list_stat[1], 1)
        self.assertEqual(list_stat[2], 0)
        self.assertEqual(list_stat[3], 0)
        self.assertEqual(list_stat[4], 1)
        self.assertEqual(tab_offer_count_pro[self.offer1], 1)
        self.assertEqual(tab_offer_count_read, {})
        self.assertEqual(tab_offer_count_copro, {})

        list_stat, tab_offer_count_read, tab_offer_count_copro, tab_offer_count_pro = \
            self.teacher2.get_stat_dissertation_role
        self.assertEqual(list_stat[0], 1)
        self.assertEqual(list_stat[1], 0)
        self.assertEqual(list_stat[2], 1)
        self.assertEqual(list_stat[3], 0)
        self.assertEqual(list_stat[4], 0)
        self.assertEqual(tab_offer_count_pro, {})
        self.assertEqual(tab_offer_count_read, {})
        self.assertEqual(tab_offer_count_copro[self.offer1], 1)

        list_stat, tab_offer_count_read, tab_offer_count_copro, tab_offer_count_pro = \
            self.teacher3.get_stat_dissertation_role
        self.assertEqual(list_stat[0], 1)
        self.assertEqual(list_stat[1], 0)
        self.assertEqual(list_stat[2], 0)
        self.assertEqual(list_stat[3], 1)
        self.assertEqual(list_stat[4], 0)
        self.assertEqual(tab_offer_count_pro, {})
        self.assertEqual(tab_offer_count_read[self.offer1], 1)
        self.assertEqual(tab_offer_count_copro, {})

