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
from django.test import TestCase
from django.core.urlresolvers import reverse

from base.tests.factories.person import PersonFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFakerFactory


class TestLearningUnitModificationProposal(TestCase):
    def setUp(self):
        self.person = PersonFactory()
        self.learning_unit_year = LearningUnitYearFakerFactory()

        self.client.force_login(self.person.user)
        self.url = reverse('learning_unit_modification_proposal', args=[self.learning_unit_year.id])

    def test_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_with_inexistent_learning_unnit_year(self):
        self.learning_unit_year.delete()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "page_not_found.html")

    def test_with_none_person(self):
        self.person.delete()
        response = self.client.get(self.url)

        self.assertTrue(response.status_code, 202)
        self.assertTemplateUsed(response, 'proposal/learning_unit_modification.html')
        self.assertEqual(response.context['learning_unit_year'], self.learning_unit_year)
        self.assertEqual(response.context['experimental_phase'], True)
        self.assertEqual(response.context['person'], None)

    def test_get_request(self):
        response = self.client.get(self.url)

        self.assertTrue(response.status_code, 202)
        self.assertTemplateUsed(response, 'proposal/learning_unit_modification.html')
        self.assertEqual(response.context['learning_unit_year'], self.learning_unit_year)
        self.assertEqual(response.context['experimental_phase'], True)
        self.assertEqual(response.context['person'], self.person)
