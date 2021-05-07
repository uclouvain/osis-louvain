##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest import mock

from django.contrib.auth.models import Permission
from django.test import TestCase, RequestFactory
from django.urls import reverse

from assessments.views import pgm_manager_administration
from base.auth.roles.program_manager import ProgramManager
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory, MiniTrainingFactory
from base.tests.factories.entity_manager import EntityManagerFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.group import ProgramManagerGroupFactory, EntityManagerGroupFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.session_exam_calendar import SessionExamCalendarFactory


class PgmManagerAdministrationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        ProgramManagerGroupFactory()
        group = EntityManagerGroupFactory()
        group.permissions.add(Permission.objects.get(codename='view_programmanager'))
        group.permissions.add(Permission.objects.get(codename='change_programmanager'))

        cls.structure_parent1 = EntityVersionFactory(acronym='SSH')
        cls.structure_child1 = EntityVersionFactory(acronym='TECO', parent=cls.structure_parent1.entity)
        cls.structure_child11 = EntityVersionFactory(acronym='TEBI', parent=cls.structure_child1.entity)
        cls.structure_child2 = EntityVersionFactory(acronym='ESPO', parent=cls.structure_parent1.entity)
        cls.structure_child21 = EntityVersionFactory(acronym='ECON', parent=cls.structure_child2.entity)
        cls.structure_child22 = EntityVersionFactory(acronym='COMU', parent=cls.structure_child2.entity)

        cls.entity_manager = EntityManagerFactory(entity=cls.structure_parent1.entity)
        cls.academic_year_previous, cls.academic_year_current = AcademicYearFactory.produce_in_past(quantity=2)
        cls.person = PersonFactory()
        SessionExamCalendarFactory.create_academic_event(cls.academic_year_current)

    def setUp(self) -> None:
        user = self.entity_manager.person.user
        self.client.force_login(user)

    def test_find_children_entities_from_acronym(self):
        self.assertIsNone(pgm_manager_administration.get_managed_entities(None))

        structures = [
            {
                'root': self.structure_parent1,
                'structures': [
                    self.structure_parent1, self.structure_child1, self.structure_child11,
                    self.structure_child2, self.structure_child21, self.structure_child22
                ]
            }
        ]
        self.assertEqual(len(pgm_manager_administration.get_managed_entities(structures)), 6)

        structures = [
            {
                'root': self.structure_child2,
                'structures': [
                    self.structure_child2, self.structure_child21, self.structure_child22
                ]
            }
        ]
        self.assertEqual(len(pgm_manager_administration.get_managed_entities(structures)), 3)

    def test_remove_pgm_manager(self):
        educ_group_year1 = EducationGroupYearFactory(academic_year=self.academic_year_current)
        educ_group_yaer2 = EducationGroupYearFactory(academic_year=self.academic_year_current)
        pgm1 = ProgramManagerFactory(person=self.person, education_group=educ_group_year1.education_group)
        pgm2 = ProgramManagerFactory(person=self.person, education_group=educ_group_yaer2.education_group)
        response = self.client.get(
            reverse('delete_manager', args=[pgm1.pk]) + "?education_groups={},{}".format(
                educ_group_year1.education_group_id,
                educ_group_yaer2.education_group_id
            )
        )
        self.assertEqual(response.context['other_programs'].get(), pgm2)
        self.assertTrue(isinstance(response.context['other_programs'].get(), ProgramManager))

        self.client.post(
            reverse('delete_manager', args=[pgm1.pk])
            + "?education_groups={},{}".format(educ_group_year1.education_group_id, educ_group_yaer2.education_group_id)
        )
        self.assertFalse(ProgramManager.objects.filter(pk=pgm1.pk).exists())
        self.assertTrue(ProgramManager.objects.filter(pk=pgm2.pk).exists())

    def test_remove_multiple_pgm_manager(self):
        educ_group_year1 = EducationGroupYearFactory(academic_year=self.academic_year_current)
        educ_group_year2 = EducationGroupYearFactory(academic_year=self.academic_year_current)
        pgm1 = ProgramManagerFactory(person=self.person, education_group=educ_group_year1.education_group)
        pgm2 = ProgramManagerFactory(person=self.person, education_group=educ_group_year2.education_group)

        response = self.client.get(
            reverse('delete_manager_person', args=[self.person.pk]) + "?education_groups={},{}".format(
                educ_group_year1.education_group_id,
                educ_group_year2.education_group_id
            )
        )
        self.assertFalse(response.context['other_programs'])

        self.client.post(
            reverse('delete_manager_person', args=[self.person.pk]) + "?education_groups={},{}".format(
                educ_group_year1.education_group_id,
                educ_group_year2.education_group_id
            )
        )
        self.assertFalse(ProgramManager.objects.filter(pk=pgm1.pk).exists())
        self.assertFalse(ProgramManager.objects.filter(pk=pgm2.pk).exists())

    def test_main_programmanager_update(self):
        educ_group_year1 = EducationGroupYearFactory(academic_year=self.academic_year_current)
        educ_group_year2 = EducationGroupYearFactory(academic_year=self.academic_year_current)
        pgm1 = ProgramManagerFactory(
            person=self.person,
            education_group=educ_group_year1.education_group,
            is_main=False,
        )
        pgm2 = ProgramManagerFactory(
            person=self.person,
            education_group=educ_group_year2.education_group,
            is_main=False,
        )

        self.client.post(
            reverse('update_main_person', args=[self.person.pk]) + "?education_groups={},{}".format(
                educ_group_year1.education_group_id,
                educ_group_year2.education_group_id
            ), data={'is_main': 'true'}
        )
        pgm1.refresh_from_db()
        pgm2.refresh_from_db()
        self.assertTrue(pgm1.is_main)
        self.assertTrue(pgm2.is_main)

        self.client.post(
            reverse('update_main', args=[pgm1.pk]) + "?education_groups={},{}".format(
                educ_group_year1.education_group_id,
                educ_group_year2.education_group_id
            ), data={'is_main': 'false'}
        )
        pgm1.refresh_from_db()
        pgm2.refresh_from_db()
        self.assertFalse(pgm1.is_main)
        self.assertTrue(pgm2.is_main)

    def test_list_pgm_manager(self):
        educ_group_year1 = EducationGroupYearFactory(academic_year=self.academic_year_current)
        educ_group_year2 = EducationGroupYearFactory(academic_year=self.academic_year_current)
        pgm1 = ProgramManagerFactory(person=self.person, education_group=educ_group_year1.education_group)
        pgm2 = ProgramManagerFactory(person=self.person, education_group=educ_group_year2.education_group)

        response = self.client.get(
            reverse('manager_list'),
            data={'education_groups': [educ_group_year1.education_group, educ_group_year2.education_group]}
        )
        self.assertEqual(
            response.context['by_person'], {self.person: [pgm1, pgm2]}
        )

    def test_offer_year_queried_by_academic_year(self):
        an_entity_management = EntityVersionFactory()
        EducationGroupYearFactory(
            academic_year=self.academic_year_previous,
            management_entity=an_entity_management.entity,
        )
        EducationGroupYearFactory(
            academic_year=self.academic_year_current,
            management_entity=an_entity_management.entity,
        )
        EducationGroupYearFactory(
            academic_year=self.academic_year_current,
            management_entity=an_entity_management.entity,
        )
        #  Mini-trainings : cannot be in results of _get_trainings
        MiniTrainingFactory(
            academic_year=self.academic_year_previous,
            management_entity=an_entity_management.entity,
        )
        MiniTrainingFactory(
            academic_year=self.academic_year_current,
            management_entity=an_entity_management.entity,
        )

        self.assertEqual(len(pgm_manager_administration._get_trainings(self.academic_year_current,
                                                                       [an_entity_management],
                                                                       None,
                                                                       None)), 2)
        self.assertEqual(len(pgm_manager_administration._get_trainings(self.academic_year_previous,
                                                                       [an_entity_management],
                                                                       None,
                                                                       None)), 1)

    def test_pgm_manager_queried_by_academic_year(self):
        a_management_entity = EntityVersionFactory()
        educ_group_year_previous_year = EducationGroupYearFactory(
            academic_year=self.academic_year_previous,
            management_entity=a_management_entity.entity
        )
        educ_group_year_current_year = EducationGroupYearFactory(
            academic_year=self.academic_year_current,
            management_entity=a_management_entity.entity,
            education_group=educ_group_year_previous_year.education_group,
        )
        person_previous_year = PersonFactory()
        person_current_year = PersonFactory()

        ProgramManagerFactory(
            person=person_previous_year,
            education_group=educ_group_year_previous_year.education_group
        )
        ProgramManagerFactory(
            person=person_current_year,
            education_group=educ_group_year_current_year.education_group
        )

        structures = [
            {
                'root': a_management_entity,
                'structures': [a_management_entity]
            }
        ]
        result = pgm_manager_administration._get_entity_program_managers(structures)
        self.assertEqual(len(result), 2)

    def test_get_administrator_entities_ensure_order(self):
        structure_root_1 = EntityVersionFactory(acronym='SST')
        EntityVersionFactory(acronym='EPL', parent=structure_root_1.entity)
        EntityVersionFactory(acronym='AGRO', parent=structure_root_1.entity)
        structure_root_2 = EntityVersionFactory(acronym='SIMM')

        EntityManagerFactory(person=self.entity_manager.person, entity=structure_root_1.entity)
        EntityManagerFactory(person=self.entity_manager.person, entity=structure_root_2.entity)

        data = pgm_manager_administration.get_administrator_entities(self.entity_manager.person.user)
        self.assertEqual(data[0]['root'], structure_root_2)  # SIMM
        self.assertEqual(len(data[0]['structures']), 1)
        self.assertEqual(data[1]['root'], self.structure_parent1)  # SSH
        self.assertEqual(len(data[1]['structures']), 6)
        self.assertEqual(data[2]['root'], structure_root_1)  # SST
        self.assertEqual(len(data[2]['structures']), 3)

    def test_get_entity_root(self):
        entity_version = EntityVersionFactory()
        self.assertEqual(pgm_manager_administration.get_entity_root(entity_version.entity.id), entity_version)

    def test_get_entity_root_with_none(self):
        self.assertIsNone(pgm_manager_administration.get_entity_root(None))

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

    def test_get_entity_list_for_one_entity(self):
        entity_parent1 = EntityVersionFactory(acronym='P1')

        entity_child1 = EntityVersionFactory(acronym='C1', parent=entity_parent1.entity)
        EntityVersionFactory(acronym='C11', parent=entity_child1.entity)

        entity_child2 = EntityVersionFactory(acronym='C2', parent=entity_parent1.entity)
        EntityVersionFactory(acronym='C21', parent=entity_child2.entity)
        EntityVersionFactory(acronym='C22', parent=entity_child2.entity)

        self.assertEqual(len(pgm_manager_administration.get_entity_list(entity_child1.entity_id, None)), 1)

    def test_get_entity_list_for_entity_hierarchy(self):
        entity_parent1 = EntityVersionFactory(acronym='P1')

        entity_child1 = EntityVersionFactory(acronym='C1', parent=entity_parent1.entity)
        EntityVersionFactory(acronym='C11', parent=entity_child1.entity)

        entity_child2 = EntityVersionFactory(acronym='P2', parent=entity_parent1.entity)
        EntityVersionFactory(acronym='P21', parent=entity_child2.entity)
        EntityVersionFactory(acronym='P22', parent=entity_child2.entity)

        self.assertEqual(len(pgm_manager_administration.get_entity_list(None, entity_parent1)), 6)

    def test_add_program_managers(self):
        educ_group_year1 = EducationGroupYearFactory(
            academic_year=self.academic_year_current,
            management_entity=self.structure_parent1.entity,
        )
        educ_group_year2 = EducationGroupYearFactory(
            academic_year=self.academic_year_current,
            management_entity=self.structure_parent1.entity,
        )

        self.client.post(
            reverse("create_manager_person")
            + "?education_groups={},{}".format(educ_group_year1.education_group_id, educ_group_year2.education_group_id),
            data={'person': self.person.pk}
        )
        self.assertEqual(ProgramManager.objects.filter(person=self.person).count(), 2)

    def test_get_administrator_entities_acronym_list(self):
        structure_root_1 = EntityVersionFactory(acronym='A')

        structure_child_1 = EntityVersionFactory(acronym='AA', parent=structure_root_1.entity)
        structure_child_2 = EntityVersionFactory(acronym='BB', parent=structure_root_1.entity)

        structure_root_2 = EntityVersionFactory(acronym='B')

        data = [{'root': structure_root_1, 'structures': [structure_root_1, structure_child_1, structure_child_2]},
                {'root': structure_root_2, 'structures': []}]

        EntityManagerFactory(person=self.person,
                             entity=structure_root_1.entity)

        data = pgm_manager_administration._get_administrator_entities_acronym_list(data)

        self.assertEqual(data, "A, B")


def set_post_request(mock_decorators, data_dict, url):
    mock_decorators.login_required = lambda x: x
    request_factory = RequestFactory()
    request = request_factory.post(url, data_dict)
    request.user = mock.Mock()
    return request
