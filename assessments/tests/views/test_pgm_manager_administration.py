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
from datetime import datetime

from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.test import TestCase, Client, RequestFactory

from assessments.views import pgm_manager_administration
from base.models import program_manager

from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.structure import StructureFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.offer_type import OfferTypeFactory
from base.tests.factories.entity_manager import EntityManagerFactory
from unittest import mock
from django.core.urlresolvers import reverse


class PgmManagerAdministrationTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('tmp', 'tmp@gmail.com', 'tmp')
        self.person = PersonFactory()

        self.structure_parent1 = StructureFactory(acronym='SSH')

        self.structure_child1 = StructureFactory(acronym='TECO', part_of=self.structure_parent1)
        self.structure_child11 = StructureFactory(acronym='TEBI', part_of=self.structure_child1)

        self.structure_child2 = StructureFactory(acronym='ESPO', part_of=self.structure_parent1)
        self.structure_child21 = StructureFactory(acronym='ECON', part_of=self.structure_child2)
        self.structure_child22 = StructureFactory(acronym='COMU', part_of=self.structure_child2)

        a_year = datetime.now().year
        self.academic_year_previous = AcademicYearFactory(year=a_year-1)
        self.academic_year_current = AcademicYearFactory(year=a_year)

        self.Client = Client()

    def test_find_children_entities_from_acronym(self):
        self.assertIsNone(pgm_manager_administration.get_managed_entities(None))

        self.assertEqual(len(pgm_manager_administration.get_managed_entities([{'root': self.structure_parent1}])), 6)
        self.assertEqual(len(pgm_manager_administration.get_managed_entities([{'root': self.structure_child2}])), 3)

    def test_search_find_programs_by_entity_grade_type(self):
        an_offer_type = OfferTypeFactory()
        offer_year1 = OfferYearFactory(academic_year=self.academic_year_current,
                                       entity_management=self.structure_parent1,
                                       offer_type=an_offer_type)
        OfferYearFactory(academic_year=self.academic_year_current,
                         entity_management=StructureFactory(),
                         offer_type=an_offer_type)
        self.assertEqual(len(pgm_manager_administration._filter_by_entity_offer_type(offer_year1.academic_year,
                                                                                     [self.structure_parent1],
                                                                                     an_offer_type)), 1)

        self.assertEqual(len(pgm_manager_administration._filter_by_entity_offer_type(offer_year1.academic_year,
                                                                                     [self.structure_parent1],
                                                                                     None)), 1)
        self.assertEqual(len(pgm_manager_administration._filter_by_entity_offer_type(offer_year1.academic_year,
                                                                                     None,
                                                                                     None)), 2)

    def test_add_pgm_manager_to_non_existing_pgm(self):
        self.client.force_login(self.user)
        list_offer_id = []
        pgm_manager_administration.add_program_managers(list_offer_id, self.person)
        managers = program_manager.ProgramManager.objects.all()
        self.assertEqual(len(managers), 0)

    def test_add_pgm_manager_to_one_pgm(self):
        self.client.force_login(self.user)
        offer_year1 = OfferYearFactory(academic_year=self.academic_year_current)
        list_offer_id = [offer_year1]
        pgm_manager_administration.add_program_managers(list_offer_id, self.person)
        managers = program_manager.find_by_offer_year_list([offer_year1])
        self.assertEqual(len(managers), 1)

    def test_add_pgm_manager_to_two_pgm(self):
        self.client.force_login(self.user)
        offer_year1 = OfferYearFactory(academic_year=self.academic_year_current)
        offer_year2 = OfferYearFactory(academic_year=self.academic_year_current)
        list_offer_id = [offer_year1, offer_year2]
        pgm_manager_administration.add_program_managers(list_offer_id, self.person)
        managers = program_manager.find_by_offer_year_list([offer_year1, offer_year2])
        self.assertEqual(len(managers), 2)

    def test_remove_pgm_manager_from_one_pgm(self):
        self.client.force_login(self.user)
        offer_year1 = OfferYearFactory(academic_year=self.academic_year_current)
        ProgramManagerFactory(person=self.person, offer_year=offer_year1)
        managers_count_before = len(program_manager.ProgramManager.objects.all())
        pgm_manager_administration.remove_program_mgr_from_offers([offer_year1], self.person)
        managers_count_after = len(program_manager.ProgramManager.objects.all())
        self.assertEqual(managers_count_after, managers_count_before-1)

    def test_remove_pgm_manager_from_two_pgm(self):
        self.client.force_login(self.user)
        offer_year1 = OfferYearFactory(academic_year=self.academic_year_current)
        offer_year2 = OfferYearFactory(academic_year=self.academic_year_current)
        ProgramManagerFactory(person=self.person, offer_year=offer_year1)
        ProgramManagerFactory(person=self.person, offer_year=offer_year2)

        managers_count_before = len(program_manager.ProgramManager.objects.all())
        pgm_manager_administration.remove_program_mgr_from_offers([offer_year1, offer_year2], self.person)
        managers_count_after = len(program_manager.ProgramManager.objects.all())
        self.assertEqual(managers_count_after, managers_count_before-2)

    def test_offer_year_queried_by_academic_year(self):
        self.client.force_login(self.user)
        an_entity_management = StructureFactory()
        OfferYearFactory(academic_year=self.academic_year_previous, entity_management=an_entity_management)
        OfferYearFactory(academic_year=self.academic_year_current, entity_management=an_entity_management)
        OfferYearFactory(academic_year=self.academic_year_current, entity_management=an_entity_management)

        self.assertEqual(len(pgm_manager_administration._get_programs(self.academic_year_current,
                                                                      [an_entity_management],
                                                                      None,
                                                                      None)), 2)
        self.assertEqual(len(pgm_manager_administration._get_programs(self.academic_year_previous,
                                                                      [an_entity_management],
                                                                      None,
                                                                      None)), 1)

    def test_pgm_manager_queried_by_academic_year(self):
        self.client.force_login(self.user)

        a_management_entity = StructureFactory()
        offer_year_previous_year = OfferYearFactory(academic_year=self.academic_year_previous,
                                                    entity_management=a_management_entity)
        offer_year_current_year = OfferYearFactory(academic_year=self.academic_year_current,
                                                   entity_management=a_management_entity)
        person_previous_year = PersonFactory()
        person_current_year = PersonFactory()

        ProgramManagerFactory(person=person_previous_year, offer_year=offer_year_previous_year)
        ProgramManagerFactory(person=person_current_year, offer_year=offer_year_current_year)

        self.assertEqual(len(pgm_manager_administration._get_entity_program_managers([{'root': a_management_entity}],
                                                                                     self.academic_year_current)), 1)

    def test_get_administrator_entities(self):
        a_person = PersonFactory(user=self.user)
        root_acronyms = ['A', 'B']
        child_acronyms = ['AA', 'BB']

        structure_root_1 = StructureFactory(acronym=root_acronyms[0])

        StructureFactory(acronym=child_acronyms[0], part_of=structure_root_1)
        StructureFactory(acronym=child_acronyms[1], part_of=structure_root_1)

        structure_root_2 = StructureFactory(acronym=root_acronyms[1])

        EntityManagerFactory(person=a_person,
                             structure=structure_root_1)
        EntityManagerFactory(person=a_person,
                             structure=structure_root_2)

        data = pgm_manager_administration.get_administrator_entities(self.user)
        self.assertEqual(data[0]['root'], structure_root_1)
        self.assertEqual(len(data[0]['structures']), 3)
        self.assertEqual(data[1]['root'], structure_root_2)
        self.assertEqual(len(data[1]['structures']), 1)

    def test_get_entity_root(self):
        a_structure = StructureFactory()
        self.assertEqual(pgm_manager_administration.get_entity_root(a_structure.id), a_structure)

    def test_get_entity_root_with_none(self):
        self.assertIsNone(pgm_manager_administration.get_entity_root(None))

    def test_get_not_entity_root(self):
        self.assertIsNone(pgm_manager_administration.get_entity_root(1))

    @mock.patch('django.contrib.auth.decorators')
    def test_get_entity_root_selected_all(self, mock_decorators):
        post_request = set_post_request(mock_decorators, {'entity': 'all_ESPO'}, '/pgm_manager/search')
        self.assertEqual(pgm_manager_administration.get_entity_root_selected(post_request), 'ESPO')

    @mock.patch('django.contrib.auth.decorators')
    def test_get_entity_root_selected(self, mock_decorators):
        post_request = set_post_request(mock_decorators, {'entity': '2',
                                                          'entity_root': '2'}, '/pgm_manager/search')
        self.assertEqual(pgm_manager_administration.get_entity_root_selected(post_request), '2')

    @mock.patch('django.contrib.auth.decorators')
    def test_get_filter_value(self, mock_decorators):
        request = set_post_request(mock_decorators, {'offer_type': '-'}, '/pgm_manager/search')
        self.assertIsNone(pgm_manager_administration.get_filter_value(request, 'offer_type'))
        request = set_post_request(mock_decorators, {'offer_type': '1'}, '/pgm_manager/search')
        self.assertEqual(pgm_manager_administration.get_filter_value(request, 'offer_type'), '1')

    def test_filter_by_person(self):
        an_offer_type = OfferTypeFactory()
        offer_year1 = OfferYearFactory(academic_year=self.academic_year_current,
                                       entity_management=self.structure_parent1,
                                       offer_type=an_offer_type)

        offer_year2 = OfferYearFactory(academic_year=self.academic_year_current,
                                       entity_management=self.structure_child1,
                                       offer_type=an_offer_type)
        ProgramManagerFactory(person=self.person, offer_year=offer_year1)
        ProgramManagerFactory(person=self.person, offer_year=offer_year2)
        offer_year_results = pgm_manager_administration._filter_by_person(self.person,
                                                              [self.structure_parent1, self.structure_child1],
                                                              self.academic_year_current, an_offer_type)
        self.assertCountEqual(offer_year_results, [offer_year1,offer_year2])

        offer_year_results = pgm_manager_administration._filter_by_person(self.person, [self.structure_parent1],
                                                              self.academic_year_current, an_offer_type)
        self.assertCountEqual(offer_year_results, [offer_year1])

        offer_year_results = pgm_manager_administration._filter_by_person(self.person, [], self.academic_year_current,
                                                              an_offer_type)
        self.assertCountEqual(offer_year_results, [offer_year1,offer_year2])

        an_other_offer_type = OfferTypeFactory()
        offer_year_results = pgm_manager_administration._filter_by_person(self.person, [self.structure_parent1],
                                                              self.academic_year_current, an_other_offer_type)
        self.assertCountEqual(offer_year_results, [])

    def test_get_entity_list_for_one_entity(self):
        entity_parent1 = StructureFactory(acronym='P1')

        entity_child1 = StructureFactory(acronym='C1', part_of=entity_parent1)
        StructureFactory(acronym='C11', part_of=entity_child1)

        entity_child2 = StructureFactory(acronym='C2', part_of=entity_parent1)
        StructureFactory(acronym='C21', part_of=entity_child2)
        StructureFactory(acronym='C22', part_of=entity_child2)

        self.assertEqual(len(pgm_manager_administration.get_entity_list(entity_child1.id, None)), 1)
        self.assertIsNone(pgm_manager_administration.get_entity_list(5, None))

    def test_get_entity_list_for_entity_hierarchy(self):
        entity_parent1 = StructureFactory(acronym='P1')

        entity_child1 = StructureFactory(acronym='C1', part_of=entity_parent1)
        StructureFactory(acronym='C11', part_of=entity_child1)

        entity_child2 = StructureFactory(acronym='P2', part_of=entity_parent1)
        StructureFactory(acronym='P21', part_of=entity_child2)
        StructureFactory(acronym='P22', part_of=entity_child2)

        self.assertEqual(len(pgm_manager_administration.get_entity_list(None, entity_parent1)), 6)

    def test_delete_manager_no_person_to_be_removed(self):
        self.client.force_login(self.user)
        url = reverse('delete_manager')
        response = self.client.get(url+"?person=&pgms=")
        self.assertEqual(response.status_code, 204)

    def test_delete_manager(self):
        offer_year1 = OfferYearFactory(academic_year=self.academic_year_current,
                                       entity_management=self.structure_parent1)
        ProgramManagerFactory(person=self.person, offer_year=offer_year1)
        self.client.force_login(self.user)
        url = reverse('delete_manager')
        response = self.client.get(url+"?person=%s&pgms=%s"
                                   % (self.person.id, offer_year1.id))
        self.assertEqual(response.status_code, 204)

    def test_is_already_program_manager(self):
        offer_year1 = OfferYearFactory(academic_year=self.academic_year_current,
                                       entity_management=self.structure_parent1)
        ProgramManagerFactory(person=self.person, offer_year=offer_year1)
        self.assertTrue(pgm_manager_administration.is_already_program_manager(self.person, offer_year1))

    def test_is_not_already_program_manager(self):
        offer_year1 = OfferYearFactory(academic_year=self.academic_year_current,
                                       entity_management=self.structure_parent1)
        self.assertFalse(pgm_manager_administration.is_already_program_manager(self.person, offer_year1))

    def test_add_offer_program_manager(self):
        offer_year1 = OfferYearFactory(academic_year=self.academic_year_current,
                                       entity_management=self.structure_parent1)
        offer_year2 = OfferYearFactory(academic_year=self.academic_year_current,
                                       entity_management=self.structure_parent1)

        ProgramManagerFactory(person=self.person, offer_year=offer_year1)
        self.assertFalse(pgm_manager_administration.add_offer_program_manager(offer_year1, self.person))
        self.assertTrue(pgm_manager_administration.add_offer_program_manager(offer_year2, self.person))

    def test_add_program_managers(self):
        offer_year1 = OfferYearFactory(academic_year=self.academic_year_current,
                                       entity_management=self.structure_parent1)
        offer_year2 = OfferYearFactory(academic_year=self.academic_year_current,
                                       entity_management=self.structure_parent1)

        ProgramManagerFactory(person=self.person, offer_year=offer_year1)
        self.assertEqual(len(pgm_manager_administration.add_program_managers([offer_year1, offer_year2], self.person)),
                         1)

    def test_convert_to_int_list(self):
        self.assertEqual(len(pgm_manager_administration._convert_to_int_list("1,2,3")), 3)
        self.assertEqual(len(pgm_manager_administration._convert_to_int_list(None)), 0)

    def test__get_all_offer_years_grouped_by_person(self):
        offer_year1 = OfferYearFactory(academic_year=self.academic_year_current,
                                       entity_management=self.structure_parent1)
        offer_year2 = OfferYearFactory(academic_year=self.academic_year_current,
                                       entity_management=self.structure_parent1)
        person1 = PersonFactory(last_name='AAA')
        person2 = PersonFactory(last_name='BBB')
        ProgramManagerFactory(person=person1, offer_year=offer_year1)
        ProgramManagerFactory(person=person2, offer_year=offer_year1)
        ProgramManagerFactory(person=person2, offer_year=offer_year2)

        data = pgm_manager_administration._get_all_offer_years_grouped_by_person([person1.id, person2.id])

        self.assertEqual(len(data), 2)
        self.assertEqual(len(data[person1.id]), 1)
        self.assertEqual(len(data[person2.id]), 2)

    def test_get_administrator_entities_acronym_list(self):

        structure_root_1 = StructureFactory(acronym='A')

        structure_child_1 = StructureFactory(acronym='AA', part_of=structure_root_1)
        structure_child_2 = StructureFactory(acronym='BB', part_of=structure_root_1)

        structure_root_2 = StructureFactory(acronym='B')

        data = [{'root': structure_root_1, 'structures': [structure_root_1, structure_child_1, structure_child_2]},
                {'root': structure_root_2, 'structures': []}]

        EntityManagerFactory(person=self.person,
                             structure=structure_root_1)

        data = pgm_manager_administration._get_administrator_entities_acronym_list(data)

        self.assertEqual(data, "A, B")


def add_permission(user, codename):
    perm = get_permission(codename)
    user.user_permissions.add(perm)


def get_permission(codename):
    return Permission.objects.get(codename=codename)


def set_post_request(mock_decorators, data_dict, url):
    mock_decorators.login_required = lambda x: x
    request_factory = RequestFactory()
    request = request_factory.post(url, data_dict)
    request.user = mock.Mock()
    return request
