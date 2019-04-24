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
from http import HTTPStatus

import reversion
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.http import HttpResponseNotFound, HttpResponseForbidden
from django.test import TestCase
from django.urls import reverse

from base.models.enums import education_group_categories
from base.models.enums.education_group_categories import TRAINING
from base.models.enums.education_group_types import TrainingType, GroupType
from base.models.enums.groups import CENTRAL_MANAGER_GROUP
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year
from base.tests.factories.certificate_aim import CertificateAimFactory
from base.tests.factories.education_group_certificate_aim import EducationGroupCertificateAimFactory
from base.tests.factories.education_group_language import EducationGroupLanguageFactory
from base.tests.factories.education_group_organization import EducationGroupOrganizationFactory
from base.tests.factories.education_group_type import GroupEducationGroupTypeFactory, \
    MiniTrainingEducationGroupTypeFactory, EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory, TrainingFactory, GroupFactory, \
    MiniTrainingFactory, EducationGroupYearCommonFactory, EducationGroupYearCommonAgregationFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory, PersonWithPermissionsFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.user import UserFactory


class EducationGroupRead(TestCase):
    @classmethod
    def setUpTestData(cls):
        academic_year = AcademicYearFactory(current=True)
        cls.education_group_parent = EducationGroupYearFactory(acronym="Parent", academic_year=academic_year)
        cls.education_group_child_1 = EducationGroupYearFactory(acronym="Child_1", academic_year=academic_year)
        cls.education_group_child_2 = EducationGroupYearFactory(acronym="Child_2", academic_year=academic_year)

        GroupElementYearFactory(parent=cls.education_group_parent, child_branch=cls.education_group_child_1)
        GroupElementYearFactory(parent=cls.education_group_parent, child_branch=cls.education_group_child_2)

        cls.education_group_language_parent = \
            EducationGroupLanguageFactory(education_group_year=cls.education_group_parent)
        cls.education_group_language_child_1 = \
            EducationGroupLanguageFactory(education_group_year=cls.education_group_child_1)

        cls.user = PersonWithPermissionsFactory("can_access_education_group").user
        cls.url = reverse("education_group_read", args=[cls.education_group_parent.id, cls.education_group_child_1.id])

    def setUp(self):
        self.client.force_login(self.user)

    def test_when_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_user_without_permission(self):
        an_other_user = UserFactory()
        self.client.force_login(an_other_user)
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_without_get_data(self):
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "education_group/tab_identification.html")

        context = response.context
        self.assertEqual(context["education_group_year"], self.education_group_child_1)
        self.assertListEqual(
            list(context["education_group_languages"]),
            [self.education_group_language_child_1.language.name]
        )
        self.assertEqual(context["enums"], education_group_categories)
        self.assertEqual(context["parent"], self.education_group_parent)

    def test_with_root_set(self):
        response = self.client.get(self.url, data={"root": self.education_group_parent.id})

        self.assertTemplateUsed(response, "education_group/tab_identification.html")

        context = response.context
        self.assertEqual(context["education_group_year"], self.education_group_child_1)
        self.assertListEqual(
            list(context["education_group_languages"]),
            [self.education_group_language_child_1.language.name]
        )
        self.assertEqual(context["enums"], education_group_categories)
        self.assertEqual(context["parent"], self.education_group_parent)

    def test_with_non_existent_root_id(self):
        non_existent_id = self.education_group_child_1.id + self.education_group_child_2.id + \
                          self.education_group_parent.id
        url = reverse("education_group_read",
                      args=[non_existent_id, self.education_group_child_1.id])

        response = self.client.get(url)

        self.assertTemplateUsed(response, "page_not_found.html")
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_with_root_set_as_current_education_group_year(self):
        response = self.client.get(self.url, data={"root": self.education_group_child_1.id})

        self.assertTemplateUsed(response, "education_group/tab_identification.html")

        context = response.context
        self.assertEqual(context["education_group_year"], self.education_group_child_1)
        self.assertListEqual(
            list(context["education_group_languages"]),
            [self.education_group_language_child_1.language.name]
        )
        self.assertEqual(context["enums"], education_group_categories)
        self.assertEqual(context["parent"], self.education_group_parent)

    def test_without_education_group_language(self):
        url = reverse("education_group_read", args=[self.education_group_parent.pk, self.education_group_child_2.id])
        response = self.client.get(url)

        self.assertTemplateUsed(response, "education_group/tab_identification.html")

        context = response.context
        self.assertEqual(context["education_group_year"], self.education_group_child_2)
        self.assertListEqual(
            list(context["education_group_languages"]),
            []
        )
        self.assertEqual(context["enums"], education_group_categories)
        self.assertEqual(context["parent"], self.education_group_parent)

    def test_versions(self):
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["versions"]), 0)

        with reversion.create_revision():
            self.education_group_child_1.acronym = "Snape"
            self.education_group_child_1.save()

        response = self.client.get(self.url)
        self.assertEqual(len(response.context["versions"]), 1)

        with reversion.create_revision():
            EducationGroupOrganizationFactory(education_group_year=self.education_group_child_1)

        response = self.client.get(self.url)
        self.assertEqual(len(response.context["versions"]), 2)


class TestReadEducationGroup(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.person = PersonFactory(user=cls.user)
        cls.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))
        cls.academic_year = AcademicYearFactory(current=True)

    def setUp(self):
        self.client.force_login(self.user)

    def test_training_template_used(self):
        training = TrainingFactory()
        url = reverse("education_group_read", args=[training.pk, training.pk])
        expected_template = "education_group/identification_training_details.html"

        response = self.client.get(url)
        self.assertTemplateUsed(response, expected_template)

    def test_mini_training_template_used(self):
        mini_training = MiniTrainingFactory()
        url = reverse("education_group_read", args=[mini_training.pk, mini_training.pk])
        expected_template = "education_group/identification_mini_training_details.html"

        response = self.client.get(url)
        self.assertTemplateUsed(response, expected_template)

    def test_group_template_used(self):
        group = GroupFactory()
        url = reverse("education_group_read", args=[group.pk, group.pk])
        expected_template = "education_group/identification_group_details.html"

        response = self.client.get(url)
        self.assertTemplateUsed(response, expected_template)

    def test_show_coorganization_case_not_2m(self):
        training_not_2m = EducationGroupYearFactory(
            education_group_type__category=TRAINING,
            education_group_type__name=TrainingType.CAPAES.name
        )
        url = reverse("education_group_read", args=[training_not_2m.pk, training_not_2m.pk])

        response = self.client.get(url)
        self.assertTrue(response.context['show_coorganization'])

    def test_show_coorganization_case_2m(self):
        training_2m = EducationGroupYearFactory(
            education_group_type__category=TRAINING,
            education_group_type__name=TrainingType.PGRM_MASTER_120.name
        )
        url = reverse("education_group_read", args=[training_2m.pk, training_2m.pk])

        response = self.client.get(url)
        self.assertFalse(response.context['show_coorganization'])

    def test_show_and_edit_coorganization(self):
        user = UserFactory()
        person = PersonFactory(user=user)
        user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))
        person.user.user_permissions.add(Permission.objects.get(codename='change_educationgroup'))
        training_not_2m = EducationGroupYearFactory(
            education_group_type__category=TRAINING,
            education_group_type__name=TrainingType.CAPAES.name
        )
        PersonEntityFactory(person=person, entity=training_not_2m.management_entity)
        url = reverse("education_group_read", args=[training_not_2m.pk, training_not_2m.pk])
        self.client.force_login(user)

        response = self.client.get(url)
        self.assertTrue(response.context['show_coorganization'])
        self.assertFalse(response.context['can_change_coorganization'])

        user.groups.add(Group.objects.get(name=CENTRAL_MANAGER_GROUP))

        response = self.client.get(url)
        self.assertTrue(response.context['show_coorganization'])
        self.assertTrue(response.context['can_change_coorganization'])

    def test_context_contains_show_tabs_args(self):
        group = GroupFactory()
        url = reverse("education_group_read", args=[group.pk, group.pk])

        response = self.client.get(url)
        self.assertTrue('show_identification' in response.context)
        self.assertTrue('show_diploma' in response.context)
        self.assertTrue('show_general_information' in response.context)
        self.assertTrue('show_skills_and_achievements' in response.context)
        self.assertTrue('show_administrative' in response.context)
        self.assertTrue('show_content' in response.context)
        self.assertTrue('show_utilization' in response.context)
        self.assertTrue('show_admission_conditions' in response.context)

    def test_main_common_show_only_identification_and_general_information(self):
        main_common = EducationGroupYearCommonFactory(
            academic_year=self.academic_year
        )
        url = reverse("education_group_read", args=[main_common.pk, main_common.pk])

        response = self.client.get(url)
        self.assertTrue(response.context['show_identification'])
        self.assertTrue(response.context['show_general_information'])

        self.assertFalse(response.context['show_diploma'])
        self.assertFalse(response.context['show_skills_and_achievements'])
        self.assertFalse(response.context['show_administrative'])
        self.assertFalse(response.context['show_content'])
        self.assertFalse(response.context['show_utilization'])
        self.assertFalse(response.context['show_admission_conditions'])

    def test_common_not_main_show_only_identification_and_admission_condition(self):
        agregation_common = EducationGroupYearCommonAgregationFactory(
            academic_year=self.academic_year
        )

        url = reverse("education_group_read", args=[agregation_common.pk, agregation_common.pk])

        response = self.client.get(url)
        self.assertTrue(response.context['show_identification'])
        self.assertTrue(response.context['show_admission_conditions'])

        self.assertFalse(response.context['show_diploma'])
        self.assertFalse(response.context['show_skills_and_achievements'])
        self.assertFalse(response.context['show_administrative'])
        self.assertFalse(response.context['show_content'])
        self.assertFalse(response.context['show_utilization'])
        self.assertFalse(response.context['show_general_information'])

    def test_not_show_general_info_and_admission_condition_and_achievement_for_n_plus_2(self):
        edy = EducationGroupYearFactory(
            academic_year=AcademicYearFactory(year=self.academic_year.year+2),
        )

        url = reverse("education_group_read", args=[edy.pk, edy.pk])

        response = self.client.get(url)
        self.assertFalse(response.context['show_general_information'])
        self.assertFalse(response.context['show_admission_conditions'])
        self.assertFalse(response.context['show_skills_and_achievements'])

    def test_not_show_general_info_and_admission_condition_and_achievement_for_year_smaller_than_2017(self):
        edy = EducationGroupYearFactory(
            academic_year=AcademicYearFactory(year=2016),
        )

        url = reverse("education_group_read", args=[edy.pk, edy.pk])

        response = self.client.get(url)
        self.assertFalse(response.context['show_general_information'])
        self.assertFalse(response.context['show_admission_conditions'])
        self.assertFalse(response.context['show_skills_and_achievements'])

    def test_not_show_general_info_for_group_which_are_not_common_core(self):
        group_type = GroupEducationGroupTypeFactory(name=GroupType.SUB_GROUP.name)

        group = EducationGroupYearFactory(
            academic_year=self.academic_year,
            education_group_type=group_type,
        )
        url = reverse("education_group_read", args=[group.pk, group.pk])
        response = self.client.get(url)

        self.assertFalse(response.context['show_general_information'])

    def test_show_general_info_for_group_which_are_common_core(self):
        common_type = GroupEducationGroupTypeFactory(name=GroupType.COMMON_CORE.name)

        group = EducationGroupYearFactory(
            academic_year=self.academic_year,
            education_group_type=common_type,
        )
        url = reverse("education_group_read", args=[group.pk, group.pk])
        response = self.client.get(url)

        self.assertTrue(response.context['show_general_information'])


class EducationGroupDiplomas(TestCase):
    @classmethod
    def setUpTestData(cls):
        academic_year = create_current_academic_year()
        type_training = EducationGroupTypeFactory(category=education_group_categories.TRAINING)
        cls.education_group_parent = EducationGroupYearFactory(acronym="Parent", academic_year=academic_year,
                                                               education_group_type=type_training)
        cls.education_group_child = EducationGroupYearFactory(acronym="Child_1", academic_year=academic_year,
                                                              education_group_type=type_training)
        GroupElementYearFactory(parent=cls.education_group_parent, child_branch=cls.education_group_child)
        cls.user = UserFactory()
        cls.person = PersonFactory(user=cls.user)
        cls.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))
        cls.url = reverse("education_group_diplomas",
                          args=[cls.education_group_parent.pk, cls.education_group_child.id])

    def setUp(self):
        self.client.force_login(self.user)

    def test_when_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_user_without_permission(self):
        an_other_user = UserFactory()
        self.client.force_login(an_other_user)
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_with_non_existent_education_group_year(self):
        non_existent_id = self.education_group_child.id + self.education_group_parent.id
        url = reverse("education_group_diplomas", args=[self.education_group_parent.pk, non_existent_id])
        response = self.client.get(url)

        self.assertTemplateUsed(response, "page_not_found.html")
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_with_education_group_year_of_type_mini_training(self):
        mini_training_education_group_year = EducationGroupYearFactory()
        mini_training_education_group_year.education_group_type.category = education_group_categories.MINI_TRAINING
        mini_training_education_group_year.education_group_type.save()

        url = reverse("education_group_diplomas",
                      args=[mini_training_education_group_year.id, mini_training_education_group_year.id])
        response = self.client.get(url)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_with_education_group_year_of_type_group(self):
        group_education_group_year = EducationGroupYearFactory()
        group_education_group_year.education_group_type.category = education_group_categories.GROUP
        group_education_group_year.education_group_type.save()

        url = reverse("education_group_diplomas",
                      args=[group_education_group_year.id, group_education_group_year.id]
                      )
        response = self.client.get(url)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_without_get_data(self):
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "education_group/tab_diplomas.html")

        context = response.context
        self.assertEqual(context["education_group_year"], self.education_group_child)
        self.assertEqual(context["parent"], self.education_group_parent)

    def test_with_non_existent_root_id(self):
        non_existent_id = self.education_group_child.id + self.education_group_parent.id
        url = reverse("education_group_diplomas", args=[non_existent_id, self.education_group_child.pk])
        response = self.client.get(url)

        self.assertTemplateUsed(response, "page_not_found.html")
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_with_root_set(self):
        response = self.client.get(self.url, data={"root": self.education_group_parent.id})

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "education_group/tab_diplomas.html")

        context = response.context
        self.assertEqual(context["education_group_year"], self.education_group_child)
        self.assertEqual(context["parent"], self.education_group_parent)

    def test_get_queryset__order_certificate_aims(self):
        self._generate_certificate_aims_with_wrong_order()

        response = self.client.get(self.url, data={"root": self.education_group_parent.id})
        certificate_aims = response.context['education_group_year'].certificate_aims.all()
        expected_order = sorted(certificate_aims, key=lambda obj: (obj.section, obj.code))
        self.assertListEqual(expected_order, list(certificate_aims))

    def _generate_certificate_aims_with_wrong_order(self):
        # Numbers below are used only to ensure records are saved in wrong order (there's no other meaning)
        for section in range(4, 2, -1):
            code_range = section * 11
            for code in range(code_range, code_range - 2, -1):
                EducationGroupCertificateAimFactory(
                    education_group_year=self.education_group_child,
                    certificate_aim=CertificateAimFactory(code=code, section=section),
                )


class TestUtilizationTab(TestCase):
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
                                                           child_branch=cls.education_group_year_2)
        cls.group_element_year_2 = GroupElementYearFactory(parent=cls.education_group_year_2,
                                                           child_branch=None,
                                                           child_leaf=cls.learning_unit_year_1)
        cls.group_element_year_3 = GroupElementYearFactory(parent=cls.education_group_year_1,
                                                           child_branch=cls.education_group_year_3)
        cls.group_element_year_4 = GroupElementYearFactory(parent=cls.education_group_year_3,
                                                           child_branch=None,
                                                           child_leaf=cls.learning_unit_year_2)
        cls.user = UserFactory()
        cls.person = PersonFactory(user=cls.user)
        cls.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))

        AcademicYearFactory(current=True)
        cls.url = reverse(
            "education_group_utilization",
            args=[
                cls.education_group_year_2.id,
                cls.education_group_year_2.id,
            ]
        )

    def test_education_group_using_template_use(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'education_group/tab_utilization.html')

    def test_education_group_using_check_parent_list_with_group(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(len(response.context_data['group_element_years']), 1)
        self.assertTemplateUsed(response, 'education_group/tab_utilization.html')


class TestContent(TestCase):
    def setUp(self):
        self.current_academic_year = create_current_academic_year()
        self.person = PersonFactory()
        self.education_group_year_1 = EducationGroupYearFactory(academic_year=self.current_academic_year)
        self.education_group_year_2 = EducationGroupYearFactory(academic_year=self.current_academic_year)
        self.education_group_year_3 = EducationGroupYearFactory(academic_year=self.current_academic_year)
        self.learning_unit_year_1 = LearningUnitYearFactory()

        self.learning_component_year_1 = LearningComponentYearFactory(
            learning_unit_year=self.learning_unit_year_1,
            hourly_volume_partial_q1=10,
            hourly_volume_partial_q2=10
        )

        self.learning_component_year_2 = LearningComponentYearFactory(
            learning_unit_year=self.learning_unit_year_1,
            hourly_volume_partial_q1=10,
            hourly_volume_partial_q2=10
        )

        self.learning_unit_year_without_container = LearningUnitYearFactory(
            learning_container_year=None
        )

        self.group_element_year_1 = GroupElementYearFactory(parent=self.education_group_year_1,
                                                            child_branch=self.education_group_year_2)

        self.group_element_year_2 = GroupElementYearFactory(parent=self.education_group_year_1,
                                                            child_branch=None,
                                                            child_leaf=self.learning_unit_year_1)

        self.group_element_year_3 = GroupElementYearFactory(parent=self.education_group_year_1,
                                                            child_branch=self.education_group_year_3)

        self.group_element_year_without_container = GroupElementYearFactory(
            parent=self.education_group_year_1,
            child_branch=None,
            child_leaf=self.learning_unit_year_without_container
        )

        self.user = UserFactory()
        self.person = PersonFactory(user=self.user)
        self.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))

        self.url = reverse(
            "education_group_content",
            args=[
                self.education_group_year_1.id,
                self.education_group_year_1.id,
            ]
        )
        self.client.force_login(self.user)

    def test_context(self):
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "education_group/tab_content.html")

        geys = response.context["group_element_years"]
        self.assertIn(self.group_element_year_1, geys)
        self.assertIn(self.group_element_year_2, geys)
        self.assertIn(self.group_element_year_3, geys)
        self.assertNotIn(self.group_element_year_without_container, geys)

    def test_show_minor_major_option_table_case_right_type(self):
        minor_major_option_types = [
            GroupType.MINOR_LIST_CHOICE.name,
            GroupType.MAJOR_LIST_CHOICE.name,
            GroupType.OPTION_LIST_CHOICE.name,
        ]

        for group_type_name in minor_major_option_types:
            education_group_type = GroupEducationGroupTypeFactory(name=group_type_name)
            self.education_group_year_1.education_group_type = education_group_type
            self.education_group_year_1.save()

            response = self.client.get(self.url)
            self.assertTrue(response.context["show_minor_major_option_table"])

    def test_show_minor_major_option_table_case_not_right_type(self):
        self.education_group_year_1.education_group_type = MiniTrainingEducationGroupTypeFactory()
        self.education_group_year_1.save()

        response = self.client.get(self.url)
        self.assertFalse(response.context["show_minor_major_option_table"])
