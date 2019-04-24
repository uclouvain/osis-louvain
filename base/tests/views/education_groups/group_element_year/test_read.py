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
from django.db.models import F, When, Case
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from base.business.education_groups.group_element_year_tree import EducationGroupHierarchy
from base.models.learning_component_year import LearningComponentYear, volume_total_verbose
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import SuperUserFactory


class TestRead(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory()
        cls.person = PersonFactory()
        cls.education_group_year_1 = EducationGroupYearFactory(title_english="", academic_year=cls.academic_year)
        cls.education_group_year_2 = EducationGroupYearFactory(title_english="", academic_year=cls.academic_year)
        cls.education_group_year_3 = EducationGroupYearFactory(title_english="", academic_year=cls.academic_year)
        cls.learning_unit_year_1 = LearningUnitYearFactory(specific_title_english="")
        cls.learning_unit_year_2 = LearningUnitYearFactory(specific_title_english="")
        cls.learning_component_year_1 = LearningComponentYearFactory(
            learning_unit_year=cls.learning_unit_year_1, hourly_volume_partial_q1=10,
            hourly_volume_partial_q2=10)
        cls.learning_component_year_2 = LearningComponentYearFactory(
            learning_unit_year=cls.learning_unit_year_1, hourly_volume_partial_q1=10,
            hourly_volume_partial_q2=10)
        cls.group_element_year_1 = GroupElementYearFactory(parent=cls.education_group_year_1,
                                                           child_branch=cls.education_group_year_2,
                                                           comment="commentaire",
                                                           comment_english="english")
        cls.group_element_year_2 = GroupElementYearFactory(parent=cls.education_group_year_2,
                                                           child_branch=None,
                                                           child_leaf=cls.learning_unit_year_1,
                                                           comment="commentaire",
                                                           comment_english="english")
        cls.group_element_year_3 = GroupElementYearFactory(parent=cls.education_group_year_1,
                                                           child_branch=cls.education_group_year_3,
                                                           comment="commentaire",
                                                           comment_english="english")
        cls.group_element_year_4 = GroupElementYearFactory(parent=cls.education_group_year_3,
                                                           child_branch=None,
                                                           child_leaf=cls.learning_unit_year_2,
                                                           comment="commentaire",
                                                           comment_english="english")
        cls.a_superuser = SuperUserFactory()

    def test_pdf_content(self):
        self.client.force_login(self.a_superuser)
        url = reverse("pdf_content", args=[self.education_group_year_1.id, self.education_group_year_2.id, "fr-be"])
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'education_group/pdf_content.html')
        url = reverse("pdf_content", args=[self.education_group_year_1.id, self.education_group_year_2.id, "en"])
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'education_group/pdf_content.html')

    def test_get_verbose_children(self):
        result = EducationGroupHierarchy(self.education_group_year_1).to_list()
        context_waiting = [self.group_element_year_1, [self.group_element_year_2], self.group_element_year_3,
                           [self.group_element_year_4]]
        self.assertEqual(result, context_waiting)

        credits = self.group_element_year_1.relative_credits or self.group_element_year_1.child_branch.credits or 0
        verbose_branch = "{} ({} {})".format(self.group_element_year_1.child.title, credits, _("credits"))

        self.assertEqual(self.group_element_year_1.verbose, verbose_branch)

        components = LearningComponentYear.objects.filter(
            learning_unit_year=self.group_element_year_2.child_leaf).annotate(
            total=Case(When(hourly_volume_total_annual=None, then=0),
                       default=F('hourly_volume_total_annual'))).values('type', 'total')

        verbose_leaf = "{} {} [{}] ({} {})".format(
            self.group_element_year_2.child_leaf.acronym,
            self.group_element_year_2.child_leaf.complete_title,
            volume_total_verbose(components),
            self.group_element_year_2.relative_credits or self.group_element_year_2.child_leaf.credits or 0,
            _("credits"),
        )
        self.assertEqual(self.group_element_year_2.verbose, verbose_leaf)
