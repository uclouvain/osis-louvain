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
import datetime

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from attribution.business.attribution import get_attributions_list
from attribution.models import attribution
from attribution.tests.models import test_attribution
from base import models as mdl_base
from base.models.entity import Entity
from base.models.entity_manager import EntityManager
from base.models.entity_version import EntityVersion
from base.tests.factories import structure, user
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.business.entities import create_entities_hierarchy
from base.tests.factories.business.learning_units import create_learning_unit_with_context
from base.tests.factories.entity_manager import EntityManagerFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.tutor import TutorFactory
from base.tests.models.test_person import create_person_with_user


class ScoresResponsibleViewTestCase(TestCase):
    def setUp(self):
        group, created = Group.objects.get_or_create(name='entity_managers')
        content_type = ContentType.objects.get_for_model(EntityManager)
        perm, created = Permission.objects.get_or_create(codename='is_entity_manager', content_type=content_type)
        group.permissions.add(perm)
        self.user = user.UserFactory()
        self.user.save()
        self.person = create_person_with_user(self.user)
        self.tutor = TutorFactory(person=self.person)
        self.academic_year = AcademicYearFactory(year=datetime.date.today().year,
                                                 start_date=datetime.date.today())
        # Old structure model [To remove]
        self.structure = structure.StructureFactory()
        self.structure_children = structure.StructureFactory(part_of=self.structure)

        # New structure model
        entities_hierarchy = create_entities_hierarchy()
        self.root_entity = entities_hierarchy.get('root_entity')
        self.child_one_entity = entities_hierarchy.get('child_one_entity')
        self.child_two_entity = entities_hierarchy.get('child_two_entity')

        self.entity_manager = EntityManagerFactory(
            person=self.person,
            structure=self.structure,
            entity=self.root_entity)

        # Create two learning_unit_year with context (Container + EntityContainerYear)
        self.learning_unit_year = create_learning_unit_with_context(
            academic_year=self.academic_year,
            structure=self.structure,
            entity=self.child_one_entity,
            acronym="LBIR1210")
        self.learning_unit_year_children = create_learning_unit_with_context(
            academic_year=self.academic_year,
            structure=self.structure_children,
            entity=self.child_two_entity,
            acronym="LBIR1211")

        self.attribution = test_attribution.create_attribution(
            tutor=self.tutor,
            learning_unit_year=self.learning_unit_year,
            score_responsible=True)
        self.attribution_children = test_attribution.create_attribution(
            tutor=self.tutor,
            learning_unit_year=self.learning_unit_year_children,
            score_responsible=True)

    def test_is_faculty_admin(self):
        entities_manager = mdl_base.entity_manager.is_entity_manager(self.user)
        self.assertTrue(entities_manager)

    def test_scores_responsible(self):
        self.client.force_login(self.user)
        url = reverse('scores_responsible')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_scores_responsible_search_with_many_elements(self):
        self.client.force_login(self.user)
        url = reverse('scores_responsible_search')
        data = {
            'course_code': 'LBIR121',
            'learning_unit_title': '',
            'tutor': self.tutor.person.last_name,
            'scores_responsible': ''
        }
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context[-1]['dict_attribution']), 2)

    def test_scores_responsible_search_without_elements(self):
        self.client.force_login(self.user)
        url = reverse('scores_responsible_search')
        data = {
            'course_code': '',
            'learning_unit_title': '',
            'tutor': '',
            'scores_responsible': ''
        }
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context[-1]['dict_attribution']), 2)

    def test_create_attributions_list(self):
        entities_manager = mdl_base.entity_manager.find_by_user(self.user)
        entities = [entity_manager.entity for entity_manager in entities_manager]
        entities_with_descendants = Entity.objects.filter(
            pk__in=[row['entity_id'] for row in EntityVersion.objects.get_tree(entities)])
        attributions_searched = attribution.search_scores_responsible(
            learning_unit_title=None,
            course_code=None,
            entities=entities_with_descendants,
            tutor=None,
            responsible=None
        )
        dictionary = get_attributions_list(attributions_searched, "-score_responsible")
        self.assertIsNotNone(dictionary)

    def test_scores_responsible_management(self):
        self.client.force_login(self.user)
        url = reverse('scores_responsible_management')
        data = {
            'learning_unit_year': "learning_unit_year_%d" % self.learning_unit_year.id
        }
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_scores_responsible_management_with_wrong_learning_unit_year(self):
        self.client.force_login(self.user)
        self.entity_manager.entity = EntityVersionFactory(parent=None, end_date=None).entity
        self.entity_manager.save()
        url = reverse('scores_responsible_management')
        data = {
            'learning_unit_year': "learning_unit_year_{}".format(self.learning_unit_year.id)
        }
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 403)

    def test_scores_responsible_add(self):
        self.client.force_login(self.user)
        url = reverse('scores_responsible_add', args=[self.learning_unit_year.id])
        attribution_id = 'attribution_' + str(self.attribution.id)
        response = self.client.post(url, {"action": "add",
                                          "attribution_id": attribution_id})
        self.assertEqual(response.status_code, 302)

    def test_scores_responsible_cancel(self):
        self.client.force_login(self.user)
        url = reverse('scores_responsible_add', args=[self.learning_unit_year.id])
        attribution_id = 'attribution_' + str(self.attribution.id)
        response = self.client.post(url, {"action": "cancel",
                                          "attribution_id": attribution_id})
        self.assertEqual(response.status_code, 302)
