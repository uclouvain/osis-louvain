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
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.person import PersonFactory, PersonWithoutUserFactory
from base.tests.factories.offer import OfferFactory
from base.tests.factories.student import StudentFactory
from dissertation.tests.factories.adviser import AdviserManagerFactory, AdviserTeacherFactory
from dissertation.tests.factories.dissertation import DissertationFactory
from dissertation.tests.factories.faculty_adviser import FacultyAdviserFactory
from dissertation.tests.factories.offer_proposition import OfferPropositionFactory
from dissertation.tests.factories.dissertation_role import DissertationRoleFactory
from dissertation.tests.factories.proposition_dissertation import PropositionDissertationFactory
from dissertation.utils import emails_dissert

HTTP_OK = 200


class DissertationUtilsTestCase(TestCase):
    fixtures = ['dissertation/fixtures/message_template.json', ]

    def setUp(self):
        self.maxDiff = None
        self.manager = AdviserManagerFactory()
        a_person_teacher = PersonFactory.create(first_name='Pierre',
                                                last_name='Dupont',
                                                email='pd@uclouvain.be')
        self.teacher = AdviserTeacherFactory(person=a_person_teacher)
        a_person_teacher2 = PersonFactory.create(first_name='Marco',
                                                 last_name='Millet',
                                                 email='mm@uclouvain.be')
        self.teacher2 = AdviserTeacherFactory(person=a_person_teacher2)
        a_person_student = PersonWithoutUserFactory.create(last_name="Durant",
                                                           email='laurent.dermine@uclouvain.be')
        self.student = StudentFactory.create(person=a_person_student)
        self.offer1 = OfferFactory(title="test_offer1")
        self.academic_year1 = AcademicYearFactory()
        self.offer_year_start1 = OfferYearFactory(acronym="test_offer1", offer=self.offer1,
                                                  academic_year=self.academic_year1)
        self.offer_proposition1 = OfferPropositionFactory(offer=self.offer1, global_email_to_commission=True)
        self.proposition_dissertation = PropositionDissertationFactory(author=self.teacher,
                                                                       creator=a_person_teacher,
                                                                       title='Proposition 1212121'
                                                                       )
        FacultyAdviserFactory(adviser=self.manager, offer=self.offer1)
        self.dissertation_1 = DissertationFactory(author=self.student,
                                                  title='Dissertation_test_email',
                                                  offer_year_start=self.offer_year_start1,
                                                  proposition_dissertation=self.proposition_dissertation,
                                                  status='DRAFT',
                                                  active=True,
                                                  dissertation_role__adviser=self.teacher,
                                                  dissertation_role__status='PROMOTEUR'
                                                  )
        FacultyAdviserFactory(adviser=self.manager, offer=self.offer1)
        self.dissert_role = DissertationRoleFactory(dissertation=self.dissertation_1,
                                                    adviser=self.teacher2,
                                                    status='READER')

    def test_create_string_list_promoteurs(self):
        promotors_string = emails_dissert.create_string_list_promotors(self.dissertation_1)
        self.assertIn("Pierre", promotors_string)
        self.assertIn("Dupont", promotors_string)

    def test_create_string_list_com_reading(self):
        promotors_string = emails_dissert.create_string_list_commission_reading(self.dissertation_1)
        self.assertIn("Pierre", promotors_string)
        self.assertIn("Dupont", promotors_string)
        self.assertIn("Marco", promotors_string)
        self.assertIn("Millet", promotors_string)

    def test_generate_receivers(self):
        tab_reslut = emails_dissert.generate_receivers([self.teacher] + [self.teacher2])
        self.assertIn("pd@uclouvain.be", str(tab_reslut))
        self.assertIn("mm@uclouvain.be", str(tab_reslut))

    def test_translating(self):
        str1 = 'READER'
        str2 = 'PROMOTEUR'
        self.assertEqual('Lecteur', emails_dissert.translating(str1))
        self.assertEqual('Promoteur', emails_dissert.translating(str2))
        self.assertEqual('Promotor', emails_dissert.translating(str2, 'en'))

    def test_get_subject_template(self):
        result = emails_dissert.get_subject_template(self.dissertation_1)
        self.assertEqual(result['title'], 'Dissertation_test_email')
        self.assertEqual('Durant', result['author'].person.last_name)
