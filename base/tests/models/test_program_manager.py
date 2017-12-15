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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime
from base.tests.models import test_person
from base.models import program_manager
from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.structure import StructureFactory
from base.tests.factories.education_group import EducationGroupFactory
from django.test import TestCase


def create_program_manager(offer_year, person=None):
    if not person:
        person = PersonFactory(first_name="program", last_name="manager")
    return ProgramManagerFactory(offer_year=offer_year, person=person)


class FindByOfferYearTest(TestCase):

    def setUp(self):
        self.academic_year = AcademicYearFactory(year=datetime.datetime.now().year)
        self.offer_year = OfferYearFactory(academic_year=self.academic_year)

    def test_case_offer_is_none(self):
        self.assertEquals(len(program_manager.find_by_offer_year(None)), 0)

    def test_case_no_existing_program_manager_for_one_offer(self):
        offer_year = OfferYearFactory(academic_year=self.academic_year)
        self.assertEquals(len(program_manager.find_by_offer_year(offer_year)), 0)

    def test_case_with_existing_program_manager(self):
        ProgramManagerFactory(offer_year=self.offer_year)
        self.assertEquals(len(program_manager.find_by_offer_year(self.offer_year)), 1)

    def test_return_sorted_managers(self):
        ProgramManagerFactory(offer_year=self.offer_year, person=PersonFactory(first_name="Yannick", last_name="Leblanc"))
        ProgramManagerFactory(offer_year=self.offer_year, person=PersonFactory(first_name="Yannick", last_name="Ferreira"))
        ProgramManagerFactory(offer_year=self.offer_year, person=PersonFactory(first_name="Laura", last_name="Ferreira"))
        ProgramManagerFactory(offer_year=self.offer_year, person=PersonFactory(first_name="Bob", last_name="Uncle"))
        ProgramManagerFactory(offer_year=self.offer_year, person=PersonFactory(first_name="Laura", last_name="Dupont"))

        managers = program_manager.find_by_offer_year(self.offer_year)
        self.assertEquals(managers[0].person.last_name, "Dupont")
        self.assertEquals(managers[1].person.last_name, "Ferreira")
        self.assertEquals(managers[1].person.first_name, "Laura")
        self.assertEquals(managers[2].person.last_name, "Ferreira")
        self.assertEquals(managers[2].person.first_name, "Yannick")
        self.assertEquals(managers[3].person.last_name, "Leblanc")
        self.assertEquals(managers[4].person.last_name, "Uncle")

    def test_is_program_manager(self):
        user = UserFactory(username="PGRM_1")
        ProgramManagerFactory(offer_year=self.offer_year, person=PersonFactory(user=user))
        self.assertTrue(program_manager.is_program_manager(user=user))

    def test_is_program_manager_of_education_group(self):
        user = UserFactory(username="PGRM_1")
        an_education_group = EducationGroupFactory()
        ProgramManagerFactory(education_group=an_education_group, person=PersonFactory(user=user))
        self.assertTrue(program_manager.is_program_manager(user=user, education_group=an_education_group))

    def test_is_not_program_manager(self):
        user = UserFactory(username="NO_PGRM")
        self.assertFalse(program_manager.is_program_manager(user=user))

    def test_find_program_manager_by_entity_administration_fac(self):
        a_management_entity = StructureFactory()
        offer_yr = OfferYearFactory(academic_year=self.academic_year,
                                    entity_management=a_management_entity)
        ProgramManagerFactory(offer_year=offer_yr, person=PersonFactory())
        self.assertEquals(len(program_manager.find_by_management_entity([a_management_entity], self.academic_year)), 1)

    def test_find_by_person_exclude_offer_list(self):
        a_person = PersonFactory(first_name="Yannick", last_name="Leblanc")

        previous_academic_year = AcademicYearFactory(year=datetime.datetime.now().year-1)
        offer_yr_previous = OfferYearFactory(academic_year=previous_academic_year)
        ProgramManagerFactory(offer_year=offer_yr_previous,
                              person=a_person)

        offer_yr1 = OfferYearFactory(academic_year=self.academic_year)
        offer_yr2 = OfferYearFactory(academic_year=self.academic_year)
        ProgramManagerFactory(offer_year=offer_yr1,
                              person=a_person)
        ProgramManagerFactory(offer_year=offer_yr2,
                              person=a_person)
        self.assertEquals(len(program_manager.find_by_person_exclude_offer_list(a_person,
                                                                                [offer_yr1],
                                                                                self.academic_year)), 1)

    def test_find_by_education_group(self):
        self.assertIsNone(program_manager.find_by_education_group(None))
        an_education_group = EducationGroupFactory()
        a_program_manager = ProgramManagerFactory(education_group=an_education_group)
        self.assertEquals(list(program_manager.find_by_education_group(an_education_group)), [a_program_manager])
