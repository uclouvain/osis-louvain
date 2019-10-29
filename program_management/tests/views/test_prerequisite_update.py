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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import json

from django.http import HttpResponseForbidden
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from base.models.prerequisite import Prerequisite
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import TrainingFactory, GroupFactory
from base.tests.factories.group_element_year import GroupElementYearFactory, GroupElementYearChildLeafFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFakerFactory, LearningUnitYearFactory
from base.tests.factories.person import PersonFactory, CentralManagerFactory
from base.tests.factories.person_entity import PersonEntityFactory


class TestUpdateLearningUnitPrerequisite(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2020)
        cls.education_group_year_parents = [TrainingFactory(academic_year=cls.academic_year) for _ in range(0, 2)]
        cls.learning_unit_year_child = LearningUnitYearFakerFactory(
            learning_container_year__academic_year=cls.academic_year
        )
        cls.group_element_years = [
            GroupElementYearFactory(parent=cls.education_group_year_parents[i],
                                    child_leaf=cls.learning_unit_year_child,
                                    child_branch=None)
            for i in range(0, 2)
        ]
        cls.person = CentralManagerFactory("change_educationgroup", 'can_access_education_group')
        PersonEntityFactory(person=cls.person,
                            entity=cls.education_group_year_parents[0].management_entity)

        cls.url = reverse("learning_unit_prerequisite_update",
                          args=[cls.education_group_year_parents[0].id, cls.learning_unit_year_child.id])

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_permission_denied_when_no_permission(self):
        person_without_permission = PersonFactory()
        self.client.force_login(person_without_permission.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_permission_denied_when_learning_unit_not_contained_in_training(self):
        other_education_group_year = TrainingFactory(academic_year=self.academic_year)
        url = reverse("learning_unit_prerequisite_update",
                      args=[other_education_group_year.id, self.learning_unit_year_child.id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_permission_denied_when_context_not_a_formation(self):
        group_parent = GroupFactory(academic_year=self.academic_year)
        PersonEntityFactory(person=self.person, entity=group_parent.management_entity)
        url = reverse("learning_unit_prerequisite_update",
                      args=[group_parent.id, self.learning_unit_year_child.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertIn(
            "{} - {}".format(group_parent.partial_acronym, group_parent.acronym),
            str(response.context['exception'])
        )

    def test_template_used(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "learning_unit/tab_prerequisite_update.html")

    def test_context(self):
        response = self.client.get(self.url)
        context = response.context
        self.assertEqual(
            context['root'],
            self.education_group_year_parents[0]
        )

        tree = json.loads(context['tree'])
        self.assertTrue(tree)
        self.assertEqual(
            tree['text'],
            self.education_group_year_parents[0].verbose
        )

    def test_post_data_simple_prerequisite(self):
        luy_1 = LearningUnitYearFactory(acronym='LSINF1111', academic_year=self.academic_year)
        GroupElementYearChildLeafFactory(parent=self.education_group_year_parents[0], child_leaf=luy_1)

        form_data = {
            "prerequisite_string": "LSINF1111"
        }
        response = self.client.post(self.url, data=form_data)

        redirect_url = reverse(
            "learning_unit_prerequisite",
            args=[self.education_group_year_parents[0].id, self.learning_unit_year_child.id]
        )
        self.assertRedirects(response, redirect_url)

        prerequisite = Prerequisite.objects.get(
            learning_unit_year=self.learning_unit_year_child.id,
            education_group_year=self.education_group_year_parents[0].id,
        )

        self.assertTrue(prerequisite)
        self.assertEqual(
            prerequisite.prerequisite_string,
            "LSINF1111"
        )

    def test_post_data_complex_prerequisite_AND(self):
        luy_1 = LearningUnitYearFactory(acronym='LSINF1111', academic_year=self.academic_year)
        GroupElementYearChildLeafFactory(parent=self.education_group_year_parents[0], child_leaf=luy_1)
        luy_2 = LearningUnitYearFactory(acronym='LDROI1200', academic_year=self.academic_year)
        GroupElementYearChildLeafFactory(parent=self.education_group_year_parents[0], child_leaf=luy_2)
        luy_3 = LearningUnitYearFactory(acronym='LEDPH1200', academic_year=self.academic_year)
        GroupElementYearChildLeafFactory(parent=self.education_group_year_parents[0], child_leaf=luy_3)

        sub_parent_group = GroupElementYearFactory(parent=self.education_group_year_parents[0],)
        luy_4 = LearningUnitYearFactory(acronym='LEDPH9900', academic_year=self.academic_year)
        GroupElementYearChildLeafFactory(parent=sub_parent_group.child_branch, child_leaf=luy_4)

        form_data = {
            "prerequisite_string": "LSINF1111 ET (LDROI1200 OU LEDPH1200) ET LEDPH9900"
        }
        self.client.post(self.url, data=form_data)

        prerequisite = Prerequisite.objects.get(
            learning_unit_year=self.learning_unit_year_child.id,
            education_group_year=self.education_group_year_parents[0].id,
        )

        self.assertTrue(prerequisite)
        self.assertEqual(
            prerequisite.prerequisite_string,
            "LSINF1111 ET (LDROI1200 OU LEDPH1200) ET LEDPH9900"
        )

    def test_post_data_complex_prerequisite_OR(self):
        luy_1 = LearningUnitYearFactory(acronym='LSINF1111', academic_year=self.academic_year)
        GroupElementYearChildLeafFactory(parent=self.education_group_year_parents[0], child_leaf=luy_1)
        luy_2 = LearningUnitYearFactory(acronym='LDROI1200', academic_year=self.academic_year)
        GroupElementYearChildLeafFactory(parent=self.education_group_year_parents[0], child_leaf=luy_2)
        luy_3 = LearningUnitYearFactory(acronym='LEDPH1200', academic_year=self.academic_year)
        GroupElementYearChildLeafFactory(parent=self.education_group_year_parents[0], child_leaf=luy_3)

        form_data = {
            "prerequisite_string": "(LSINF1111 ET LDROI1200) OU LEDPH1200"
        }
        self.client.post(self.url, data=form_data)

        prerequisite = Prerequisite.objects.get(
            learning_unit_year=self.learning_unit_year_child.id,
            education_group_year=self.education_group_year_parents[0].id,
        )

        self.assertTrue(prerequisite)
        self.assertEqual(
            prerequisite.prerequisite_string,
            "(LSINF1111 ET LDROI1200) OU LEDPH1200"
        )

    def test_post_data_with_prerequisite_in_lower_case(self):
        luy_1 = LearningUnitYearFactory(acronym='LSINF1111', academic_year=self.academic_year)
        GroupElementYearChildLeafFactory(parent=self.education_group_year_parents[0], child_leaf=luy_1)
        luy_2 = LearningUnitYearFactory(acronym='LDROI1200', academic_year=self.academic_year)
        GroupElementYearChildLeafFactory(parent=self.education_group_year_parents[0], child_leaf=luy_2)

        form_data = {
            "prerequisite_string": "lsinf1111 et ldroi1200"
        }
        self.client.post(self.url, data=form_data)
        prerequisite = Prerequisite.objects.get(
            learning_unit_year=self.learning_unit_year_child.id,
            education_group_year=self.education_group_year_parents[0].id,
        )

        self.assertTrue(prerequisite)
        self.assertEqual(
            prerequisite.prerequisite_string,
            "LSINF1111 ET LDROI1200"
        )

    def test_post_data_prerequisite_accept_duplicates(self):
        luy_1 = LearningUnitYearFactory(acronym='LDROI1200', academic_year=self.academic_year)
        GroupElementYearChildLeafFactory(parent=self.education_group_year_parents[0], child_leaf=luy_1)
        luy_2 = LearningUnitYearFactory(acronym='LEDPH1200', academic_year=self.academic_year)
        GroupElementYearChildLeafFactory(parent=self.education_group_year_parents[0], child_leaf=luy_2)

        form_data = {
            "prerequisite_string": "(LDROI1200 ET LEDPH1200) OU LDROI1200"
        }
        self.client.post(self.url, data=form_data)

        prerequisite = Prerequisite.objects.get(
            learning_unit_year=self.learning_unit_year_child.id,
            education_group_year=self.education_group_year_parents[0].id,
        )

        self.assertTrue(prerequisite)
        self.assertEqual(
            prerequisite.prerequisite_string,
            "(LDROI1200 ET LEDPH1200) OU LDROI1200"
        )

    def test_post_data_prerequisite_learning_units_not_found(self):
        luy_1 = LearningUnitYearFactory(acronym='LDROI1200', academic_year=self.academic_year)
        GroupElementYearChildLeafFactory(parent=self.education_group_year_parents[0], child_leaf=luy_1)
        luy_2 = LearningUnitYearFactory(acronym='LEDPH1200', academic_year=self.academic_year)
        GroupElementYearChildLeafFactory(parent=self.education_group_year_parents[0], child_leaf=luy_2)
        luy_3 = LearningUnitYearFactory(acronym='LSINF1111', academic_year=self.academic_year)
        GroupElementYearChildLeafFactory(parent=self.education_group_year_parents[0], child_leaf=luy_3)

        form_data = {
            "prerequisite_string": "(LDROI1200 ET LEDPH1200) OU LZZZ9876 OU (LZZZ6789 ET LSINF1111)"
        }
        response = self.client.post(self.url, data=form_data)
        errors_prerequisite_string = response.context_data.get('form').errors.get('prerequisite_string')
        self.assertEqual(
            len(errors_prerequisite_string),
            2
        )
        self.assertEqual(
            str(errors_prerequisite_string[0]),
            _("No match has been found for this learning unit :  %(acronym)s") % {'acronym': 'LZZZ9876'}
        )
        self.assertEqual(
            str(errors_prerequisite_string[1]),
            _("No match has been found for this learning unit :  %(acronym)s") % {'acronym': 'LZZZ6789'}
        )

    def test_post_data_prerequisite_to_itself_error(self):
        self.learning_unit_year_child.acronym = 'LDROI1200'
        self.learning_unit_year_child.save()

        form_data = {
            "prerequisite_string": 'LDROI1200'
        }
        response = self.client.post(self.url, data=form_data)
        errors_prerequisite_string = response.context_data.get('form').errors.get('prerequisite_string')
        self.assertEqual(
            len(errors_prerequisite_string),
            1
        )
        self.assertEqual(
            str(errors_prerequisite_string[0]),
            _("A learning unit cannot be prerequisite to itself : %(acronym)s") % {'acronym': 'LDROI1200'}
        )

    def test_post_data_modify_existing_prerequisite(self):
        LearningUnitYearFactory(acronym='LSINF1111', academic_year=self.academic_year)
        luy_2 = LearningUnitYearFactory(acronym='LSINF1112', academic_year=self.academic_year)
        GroupElementYearChildLeafFactory(parent=self.education_group_year_parents[0], child_leaf=luy_2)

        form_data = {
            "prerequisite_string": "LSINF1111"
        }
        self.client.post(self.url, data=form_data)

        form_data = {
            "prerequisite_string": "LSINF1112"
        }
        self.client.post(self.url, data=form_data)

        prerequisite = Prerequisite.objects.get(
            learning_unit_year=self.learning_unit_year_child.id,
            education_group_year=self.education_group_year_parents[0].id,
        )

        self.assertTrue(prerequisite)
        self.assertEqual(
            prerequisite.prerequisite_string,
            "LSINF1112"
        )

    def test_should_not_accept_prerequisite_which_is_not_part_of_the_formation(self):
        LearningUnitYearFactory(acronym='LSINF1111', academic_year=self.academic_year)
        form_data = {
            "prerequisite_string": "LSINF1111"
        }
        response = self.client.post(self.url, data=form_data)
        form = response.context["form"]
        self.assertFalse(form.is_valid())
