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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.test import TestCase, RequestFactory, Client
import random
from django.core.urlresolvers import reverse
from dissertation.tests.models import test_proposition_dissertation, test_offer_proposition, test_adviser, \
                                      test_proposition_role
from base.tests.models import test_offer

from dissertation.models.proposition_dissertation import PropositionDissertation
from dissertation.models.proposition_role import PropositionRole

class PropositionDissertationViewTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        #Teacher
        self.adviser_teacher = test_adviser.create_adviser_from_scratch(username='teacher', email='teacher@uclouvain.be',
                                                                        password='teacher', type='PRF')
        #Manager
        self.adviser_manager = test_adviser.create_adviser_from_scratch(username='manager', email='manager@uclouvain.be',
                                                                        password='manager', type='MGR')
        #Proposition Offer
        offer = test_offer.create_offer(title="TEST_OFFER")
        self.offer_proposition = test_offer_proposition.create_offer_proposition(acronym="TEST_OFFER_NOW", offer=offer)
        # Create multiple propositions dissertations
        self.teacher_propositon_dissertations = []
        self.manager_proposition_dissertations = []
        for x in range(0, 5):
            # Teacher proposition dissertation creation
            teacher_prop = test_proposition_dissertation.create_proposition_dissertation(title="Teacher proposition " + str(x),
                                                                          adviser=self.adviser_teacher,
                                                                          person=self.adviser_teacher.person,
                                                                          offer_proposition=self.offer_proposition)
            self.teacher_propositon_dissertations.append(teacher_prop)
            # Manager proposition dissertation creation
            manager_prop = test_proposition_dissertation.create_proposition_dissertation(title="Manager propostion " + str(x),
                                                                          adviser=self.adviser_manager,
                                                                          person=self.adviser_manager.person,
                                                                          offer_proposition=self.offer_proposition)
            self.manager_proposition_dissertations.append(manager_prop)


    ###########################
    #         TEACHER         #
    ###########################
    def test_get_new_proposition_dissertation(self):
        self.client.login(username='teacher', password='teacher')
        url = reverse('proposition_dissertation_new')
        response = self.client.get(url)
        self.assertEqual(response.context['form'].initial['active'], True)
        self.assertEqual(response.context['form'].initial['author'], self.adviser_teacher)

    def test_post_new_proposition_dissertation(self):
        self.client.login(username='teacher', password='teacher')
        url = reverse('proposition_dissertation_new')
        response = self.client.post(url, data=self.get_form_teacher_new_proposition_dissertation())
        # Nous pouvons tester uniquement la redirection, impossible de deviner l'ID
        self.assertEqual(response.status_code, 302)

    def test_get_detail_proposition_dissertation(self):
        self.client.login(username='teacher', password='teacher')
        proposition_dissertation = self.teacher_propositon_dissertations[1]
        url = reverse('proposition_dissertation_detail', args=[proposition_dissertation.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        context = response.context[-1]
        self.assertEqual(context.get("proposition_dissertation"), proposition_dissertation)

    def test_get_edit_proposition_dissertation(self):
        self.client.login(username='teacher', password='teacher')
        proposition_dissertation = self.teacher_propositon_dissertations[1]
        url = reverse('proposition_dissertation_edit', args=[proposition_dissertation.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        #Check form fields
        form = response.context['form']
        self.assertEqual(form.initial['title'], proposition_dissertation.title)
        self.assertEqual(form.initial['author'], proposition_dissertation.author.id)
        self.assertEqual(form.initial['collaboration'], proposition_dissertation.collaboration)
        self.assertEqual(form.initial['type'], proposition_dissertation.type)
        self.assertEqual(form.initial['level'], proposition_dissertation.level)
        self.assertEqual(form.initial['max_number_student'], proposition_dissertation.max_number_student)

    # Must correct bug osis/#1814
    # def test_get_wrong_edit_proposition_dissertation(self):
    #     self.client.login(username=self.user_teacher.username, password='teacher')
    #     url = reverse('proposition_dissertation_edit', args=[self.get_unused_id_proposition_dissertation()])
    #     response = self.client.get(url, follow=True)
    #     self.assertEqual(response.status_code, 404)

    def test_post_edit_proposition_dissertation(self):
        self.client.login(username='teacher', password='teacher')
        proposition_dissertation = self.teacher_propositon_dissertations[1]
        url = reverse('proposition_dissertation_edit', args=[proposition_dissertation.id])
        response = self.client.post(url, data = self.get_form_teacher_edit_proposition_dissertation())
        #Si l'objet est mis à jour redirection, impossible de tester actuellement le contenu
        self.assertEqual(response.status_code, 302)

    def test_get_all_proposition_dissertations(self):
        self.client.login(username='teacher', password='teacher')
        url = reverse('proposition_dissertations')
        response = self.client.get(url)
        self.assertEqual(len(response.context['propositions_dissertations']), 10) #5 teachers / 5 managers

    def test_get_my_proposition_dissertations(self):
        self.client.login(username='teacher', password='teacher')
        url = reverse('my_dissertation_propositions')
        response = self.client.get(url)
        self.assertEqual(len(response.context['propositions_dissertations']), 5)

    def test_delete_proposition_dissertation(self):
        self.client.login(username='teacher', password='teacher')
        proposition = self.teacher_propositon_dissertations[1]
        url = reverse('proposition_dissertation_delete', args=[proposition.id])
        response = self.client.post(url)
        # Si l'objet est mis à jour redirection
        self.assertEqual(response.status_code, 302)
        is_not_active=PropositionDissertation.objects.filter(pk=proposition.id, active=False).count()
        self.assertTrue(is_not_active)

    def test_search_proposition_dissertations(self):
        self.client.login(username='teacher', password='teacher')
        url = reverse('proposition_dissertations_search')
        response = self.client.get(url, data={"search": "Teacher proposition 4"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['propositions_dissertations']), 1)

    #TODO: Check if the redirection is correct because it seems strange to render a layout
    #      "proposition_dissertations_jury_edit"
    def test_get_new_jury_proposition_dissertations(self):
        self.client.login(username='teacher', password='teacher')
        proposition = self.teacher_propositon_dissertations[1]
        url = reverse('proposition_dissertations_jury_new', args=[proposition.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        #self.assertRedirects(response, reverse('proposition_dissertations_jury_edit', args=[proposition.id]))

    def test_post_new_jury_proposition_dissertations(self):
        self.client.login(username='teacher', password='teacher')
        proposition = self.teacher_propositon_dissertations[1]
        new_adviser = test_adviser.create_adviser_from_scratch(username='thomas', email='thomas@uclouvain.be',
                                                               password='thomas', type='PRF')

        url = reverse('proposition_dissertations_jury_new', args=[proposition.id])
        response = self.client.post(url, data={ "status"  : 'PROMOTEUR',
                                                "adviser" : new_adviser.id,
                                                "proposition_dissertation" : proposition.id })
        self.assertRedirects(response, reverse('proposition_dissertation_detail', args=[proposition.id]))

        nb_occurence = PropositionRole.objects.filter(status="PROMOTEUR",adviser=new_adviser,
                                                      proposition_dissertation=proposition).count()
        self.assertEqual(nb_occurence, 1)

    #Test max [4] number for jury
    def test_post_max_new_jury_proposition_dissertations(self):
        self.client.login(username='teacher', password='teacher')
        proposition = self.teacher_propositon_dissertations[1]
        url = reverse('proposition_dissertations_jury_new', args=[proposition.id])

        #PROMOTEUR
        new_adviser_1 = test_adviser.create_adviser_from_scratch(username='thomas', email='thomas@uclouvain.be',
                                                                 password='thomas', type='PRF')
        response = self.client.post(url, data={"status": 'PROMOTEUR',
                                               "adviser": new_adviser_1.id,
                                               "proposition_dissertation": proposition.id})
        self.assertRedirects(response, reverse('proposition_dissertation_detail', args=[proposition.id]))

        #CO_PROMOTEUR
        new_adviser_2 = test_adviser.create_adviser_from_scratch(username='dupont', email='dupont@uclouvain.be',
                                                                 password='dupont', type='PRF')
        response = self.client.post(url, data={"status": 'CO_PROMOTEUR',
                                               "adviser": new_adviser_2.id,
                                               "proposition_dissertation": proposition.id})
        self.assertRedirects(response, reverse('proposition_dissertation_detail', args=[proposition.id]))

        #READER
        new_adviser_3 = test_adviser.create_adviser_from_scratch(username='durant', email='durant@uclouvain.be',
                                                                 password='durant', type='PRF')
        response = self.client.post(url, data={"status": 'READER',
                                               "adviser": new_adviser_3.id,
                                               "proposition_dissertation": proposition.id})
        self.assertRedirects(response, reverse('proposition_dissertation_detail', args=[proposition.id]))

        #ACCOMPANIST
        new_adviser_4 = test_adviser.create_adviser_from_scratch(username='paul', email='paul@uclouvain.be',
                                                                 password='paul', type='PRF')
        response = self.client.post(url, data={"status": 'ACCOMPANIST',
                                               "adviser": new_adviser_4.id,
                                               "proposition_dissertation": proposition.id})
        self.assertRedirects(response, reverse('proposition_dissertation_detail', args=[proposition.id]))
        nb_occurence = PropositionRole.objects.filter(proposition_dissertation=proposition).count()
        self.assertEqual(nb_occurence, 4)

        #Try another add but must not pass
        new_adviser_5 = test_adviser.create_adviser_from_scratch(username='xavier', email='xavier@uclouvain.be',
                                                                 password='xavier', type='PRF')
        response = self.client.post(url, data={"status": 'PRESIDENT',
                                               "adviser": new_adviser_5.id,
                                               "proposition_dissertation": proposition.id})
        self.assertRedirects(response, reverse('proposition_dissertation_detail', args=[proposition.id]))
        nb_occurence = PropositionRole.objects.filter(proposition_dissertation=proposition).count()
        self.assertEqual(nb_occurence, 4) #4 elem and not 5 (Max: 4) !

    def test_delete_jury_proposition_dissertations(self):
        self.client.login(username='teacher', password='teacher')
        proposition = self.teacher_propositon_dissertations[1]
        adviser = test_adviser.create_adviser_from_scratch(username='thomas', email='thomas@uclouvain.be',
                                                           password='thomas', type='PRF')
        status = "CO_PROMOTEUR"
        proposition_role = test_proposition_role.create_proposition_role(proposition=proposition, adviser=adviser,
                                                                         status=status)
        nb_occurence = PropositionRole.objects.filter(proposition_dissertation=proposition).count()
        self.assertEqual(nb_occurence, 2) #teacher as "PROMOTEUR" AND thomas as "CO_PROMOTEUR"

        url = reverse('proposition_dissertations_role_delete', args=[proposition_role.id])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('proposition_dissertation_detail', args=[proposition.id]))
        nb_occurence_after_delete = PropositionRole.objects.filter(proposition_dissertation=proposition).count()
        self.assertEqual(nb_occurence_after_delete, 1)  # teacher as "PROMOTEUR"


    def get_unused_id_proposition_dissertation(self):
        allowed_values = list(range(0, 600))
        allowed_values.remove(self.proposition_dissertation.id)
        return random.choice(allowed_values)

    def get_form_teacher_new_proposition_dissertation(self):
        return {
            "title": "proposition_dissertation",
            "visibility": True,
            "author": self.adviser_teacher.id,
            "description": "proposition dissertation description",
            "type": "OTH",
            "level": "SPECIFIC",
            "collaboration": "FORBIDDEN",
            "max_number_student": 5,
            "txt_checkbox_" + str(self.offer_proposition.id) : "on"  #Simulate checkbox
        }

    def get_form_teacher_edit_proposition_dissertation(self):
        return {
            "title" : "Updated proposition dissertation",
            "visibility" : False,
            "author": self.adviser_teacher.id,
            "description" : "Updated proposition description",
            "type" : "OTH",
            "level" : "SPECIFIC",
            "collaboration" : "FORBIDDEN",
            "max_number_student" : 1,
            "txt_checkbox_" + str(self.offer_proposition.id) : "on"  # Simulate checkbox
        }

    ###########################
    #         MANAGER         #
    ###########################