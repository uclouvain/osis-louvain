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
from django.core.urlresolvers import reverse
from django.test import TestCase
from assessments.views import scores_responsible
from attribution.models import attribution
from attribution.tests.models import test_attribution
from base import models as mdl_base
from base.tests.factories import academic_year, entity_manager, learning_unit_year, structure, tutor, user
from base.tests.models.test_person import create_person_with_user


class ScoresResponsibleViewTestCase(TestCase):
    def setUp(self):
        self.user = user.UserFactory()
        self.user.save()
        self.person = create_person_with_user(self.user)
        self.structure = structure.StructureFactory()
        self.structure_children = structure.StructureFactory(part_of=self.structure)
        self.entity_manager = entity_manager.EntityManagerFactory(person=self.person, structure=self.structure)
        self.tutor = tutor.TutorFactory()
        self.academic_year = academic_year.AcademicYearFactory(year=datetime.date.today().year,
                                                               start_date=datetime.date.today())
        self.learning_unit_year = learning_unit_year.LearningUnitYearFactory(structure=self.structure,
                                                                             acronym="LBIR1210",
                                                                             academic_year=self.academic_year)
        self.learning_unit_year_children = learning_unit_year.LearningUnitYearFactory(structure=self.structure_children,
                                                                                      acronym="LBIR1211",
                                                                                      academic_year=self.academic_year)
        self.attribution = test_attribution.create_attribution(tutor=self.tutor,
                                                               learning_unit_year=self.learning_unit_year,
                                                               score_responsible=True)
        self.attribution_children = test_attribution.create_attribution(tutor=self.tutor,
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
        response = self.client.get(url+"?course_code=%s&learning_unit_title=%s&tutor=%s&scores_responsible=%s"
                                   % ("LBIR121", "", self.tutor.person.last_name, ""))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context[-1]['dict_attribution']), 2)

    def test_scores_responsible_search_without_elements(self):
        self.client.force_login(self.user)
        url = reverse('scores_responsible_search')
        response = self.client.get(url+"?course_code=%s&learning_unit_title=%s&tutor=%s&scores_responsible=%s"
                                   % ("", "", "", ""))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context[-1]['dict_attribution']), 2)

    def test_create_attributions_list(self):
        entities_manager = mdl_base.entity_manager.find_by_user(self.user)
        structures = mdl_base.structure.find_all_structure_parents(entities_manager)
        attributions_searched = attribution.search_scores_responsible(learning_unit_title=None,
                                                                      course_code=None,
                                                                      structures=structures,
                                                                      tutor=None,
                                                                      responsible=None)
        dictionary = scores_responsible.create_attributions_list(attributions_searched)
        self.assertIsNotNone(dictionary)

    def test_scores_responsible_management(self):
        self.client.force_login(self.user)
        url = reverse('scores_responsible_management')
        response = self.client.get(url, data={'learning_unit_year': "learning_unit_year_%d" % self.learning_unit_year.id})
        self.assertEqual(response.status_code, 200)

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
