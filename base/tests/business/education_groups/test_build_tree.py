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
import datetime
import json

from django.templatetags.static import static
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from waffle.testutils import override_switch

from base.business.education_groups.group_element_year_tree import EducationGroupHierarchy
from base.models import entity_version
from base.models.enums import organization_type
from base.models.enums.education_group_types import MiniTrainingType, GroupType, TrainingType
from base.models.enums.link_type import LinkTypes
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.external_learning_unit_year import ExternalLearningUnitYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.prerequisite import PrerequisiteFactory
from base.tests.factories.prerequisite_item import PrerequisiteItemFactory
from osis_common.utils.datetime import get_tzinfo
from reference.tests.factories.country import CountryFactory


class TestBuildTree(TestCase):
    def setUp(self):
        self.academic_year = AcademicYearFactory()
        self.country = CountryFactory()
        self.organization = OrganizationFactory(
            type=organization_type.MAIN
        )
        self.now = datetime.datetime.now(get_tzinfo())
        start_date = self.now - datetime.timedelta(days=10)
        end_date = None
        self._build_current_entity_version_structure(end_date, start_date)

        self.parent = EducationGroupYearFactory(acronym='LTEST0000',
                                                academic_year=self.academic_year,
                                                management_entity=self.SC.entity,
                                                administration_entity=self.SC.entity)
        self.group_element_year_1 = GroupElementYearFactory(
            parent=self.parent,
            child_branch=EducationGroupYearFactory(acronym='LTEST0010',
                                                   academic_year=self.academic_year,
                                                   management_entity=self.SC.entity,
                                                   administration_entity=self.SC.entity)
        )
        self.group_element_year_1_1 = GroupElementYearFactory(
            parent=self.group_element_year_1.child_branch,
            child_branch=EducationGroupYearFactory(acronym='LTEST0011',
                                                   academic_year=self.academic_year,
                                                   management_entity=self.SC.entity,
                                                   administration_entity=self.SC.entity)
        )
        self.group_element_year_2 = GroupElementYearFactory(
            parent=self.parent,
            child_branch=EducationGroupYearFactory(acronym='LTEST0020',
                                                   academic_year=self.academic_year,
                                                   management_entity=self.MATH.entity,
                                                   administration_entity=self.MATH.entity)
        )
        self.learning_unit_year_1 = LearningUnitYearFactory(
            acronym='LTEST0021',
            academic_year=self.academic_year,
            learning_container_year__requirement_entity=self.MATH.entity)
        self.group_element_year_2_1 = GroupElementYearFactory(
            parent=self.group_element_year_2.child_branch,
            child_branch=None,
            child_leaf=self.learning_unit_year_1
        )

        self.parent_ILV = EducationGroupYearFactory(acronym='TURC LV',
                                                    academic_year=self.academic_year,
                                                    management_entity=self.ILV.entity,)

    def _build_current_entity_version_structure(self, end_date, start_date):
        """Build the following entity version structure :
                             SST                  ADEF
                        SC        LOCI       ILV
                    MATH PHYS  URBA  BARC
        """
        self.ADEF = EntityVersionFactory(
            entity=EntityFactory(country=self.country, organization=self.organization),
            acronym="ADEF",
            title="ADEF",
            entity_type=entity_version.entity_type.LOGISTICS_ENTITY,
            parent=None,
            start_date=start_date,
            end_date=end_date
        )

        self.ILV = EntityVersionFactory(
            entity=EntityFactory(country=self.country, organization=self.organization),
            acronym="ILV",
            title="ILV",
            entity_type=entity_version.entity_type.LOGISTICS_ENTITY,
            parent=self.ADEF.entity,
            start_date=start_date,
            end_date=end_date
        )

        self.root = EntityVersionFactory(
            entity=EntityFactory(country=self.country, organization=self.organization),
            acronym="SST",
            title="SST",
            entity_type=entity_version.entity_type.SECTOR,
            parent=None,
            start_date=start_date,
            end_date=end_date
        )
        self.SC = EntityVersionFactory(
            entity=EntityFactory(country=self.country, organization=self.organization),
            acronym="SC",
            title="SC",
            entity_type=entity_version.entity_type.FACULTY,
            parent=self.root.entity,
            start_date=start_date,
            end_date=end_date
        )
        self.MATH = EntityVersionFactory(
            entity=EntityFactory(country=self.country, organization=self.organization),
            acronym="MATH",
            title="MATH",
            entity_type=entity_version.entity_type.SCHOOL,
            parent=self.SC.entity,
            start_date=start_date,
            end_date=end_date
        )
        self.PHYS = EntityVersionFactory(
            entity=EntityFactory(country=self.country, organization=self.organization),
            acronym="PHYS",
            title="PHYS",
            entity_type=entity_version.entity_type.SCHOOL,
            parent=self.SC.entity,
            start_date=start_date,
            end_date=end_date
        )
        self.LOCI = EntityVersionFactory(
            entity=EntityFactory(country=self.country, organization=self.organization),
            acronym="LOCI",
            title="LOCI",
            entity_type=entity_version.entity_type.FACULTY,
            parent=self.root.entity,
            start_date=start_date,
            end_date=end_date
        )
        self.URBA = EntityVersionFactory(
            entity=EntityFactory(country=self.country, organization=self.organization),
            acronym="URBA",
            title="URBA",
            entity_type=entity_version.entity_type.SCHOOL,
            parent=self.LOCI.entity,
            start_date=start_date,
            end_date=end_date
        )
        self.BARC = EntityVersionFactory(
            entity=EntityFactory(country=self.country, organization=self.organization),
            acronym="BARC",
            title="BARC",
            entity_type=entity_version.entity_type.SCHOOL,
            parent=self.LOCI.entity,
            start_date=start_date,
            end_date=end_date
        )
        self.EDDY = EntityVersionFactory(
            entity=EntityFactory(country=self.country, organization=self.organization),
            acronym="EDDY",
            title="EDDY",
            entity_type=entity_version.entity_type.SCHOOL,
            parent=self.URBA.entity,
            start_date=start_date,
            end_date=end_date
        )
        self.E2DY = EntityVersionFactory(
            entity=EntityFactory(country=self.country, organization=self.organization),
            acronym="E2DY",
            title="E2DY",
            entity_type=entity_version.entity_type.SCHOOL,
            parent=self.root.entity,
            start_date=start_date,
            end_date=end_date
        )

    def test_init_tree(self):
        node = EducationGroupHierarchy(self.parent)

        self.assertEqual(node.education_group_year, self.parent)
        self.assertEqual(len(node.children), 2)
        self.assertEqual(node.children[0].group_element_year, self.group_element_year_1)
        self.assertEqual(node.children[1].group_element_year, self.group_element_year_2)

        self.assertEqual(node.children[0].children[0].group_element_year, self.group_element_year_1_1)
        self.assertEqual(node.children[1].children[0].group_element_year, self.group_element_year_2_1)

        self.assertEqual(node.children[0].children[0].education_group_year, self.group_element_year_1_1.child_branch)
        self.assertEqual(node.children[1].children[0].education_group_year, None)
        self.assertEqual(node.children[1].children[0].learning_unit_year, self.group_element_year_2_1.child_leaf)

    def test_tree_to_json(self):
        node = EducationGroupHierarchy(self.parent)

        json = node.to_json()
        self.assertEqual(json['text'], self.parent.verbose)

        self.assertEqual(json['a_attr']['href'], reverse('education_group_read', args=[
            self.parent.pk, self.parent.pk]) + "?group_to_parent=0")

        self.assertEqual(
            json['children'][1]['children'][0]['a_attr']['href'],
            reverse(
                'learning_unit_utilization',
                args=[self.parent.pk, self.group_element_year_2_1.child_leaf.pk]
            ) + "?group_to_parent={}".format(self.group_element_year_2_1.pk)
        )

    def test_tree_get_url(self):
        test_cases = [
            {'name': 'with tab',
             'node': EducationGroupHierarchy(self.parent, tab_to_show='show_identification'),
             'correct_url': reverse('education_group_read', args=[self.parent.pk, self.parent.pk]) +
                "?group_to_parent=0&tab_to_show=show_identification"},
            {'name': 'without tab',
             'node': EducationGroupHierarchy(self.parent),
             'correct_url': reverse('education_group_read',
                                    args=[self.parent.pk, self.parent.pk]) + "?group_to_parent=0"},
            {'name': 'with wrong tab',
             'node': EducationGroupHierarchy(self.parent, tab_to_show='not_existing'),
             'correct_url': reverse('education_group_read',
                                    args=[self.parent.pk, self.parent.pk]) + "?group_to_parent=0"},
        ]

        for case in test_cases:
            with self.subTest(type=case['name']):
                self.assertEqual(case['correct_url'], case['node'].get_url())

    def test_tree_luy_has_prerequisite(self):
        # self.learning_unit_year_1 has prerequisite
        PrerequisiteItemFactory(
            prerequisite=PrerequisiteFactory(
                learning_unit_year=self.learning_unit_year_1,
                education_group_year=self.parent
            )
        )

        node = EducationGroupHierarchy(self.parent)
        json = node.to_json()

        self.assertEqual(
            json['children'][1]['children'][0]['a_attr']['title'],
            "{}\n{}".format(self.learning_unit_year_1.complete_title, _("The learning unit has prerequisites"))
        )
        self.assertEqual(
            json['children'][1]['children'][0]['icon'],
            'fa fa-arrow-left'
        )

    def test_tree_luy_is_prerequisite(self):
        # self.learning_unit_year_1 is prerequisite
        PrerequisiteItemFactory(
            learning_unit=self.learning_unit_year_1.learning_unit,
            prerequisite=PrerequisiteFactory(education_group_year=self.parent)
        )

        node = EducationGroupHierarchy(self.parent)
        json = node.to_json()

        self.assertEqual(
            json['children'][1]['children'][0]['a_attr']['title'],
            "{}\n{}".format(self.learning_unit_year_1.complete_title, _("The learning unit is a prerequisite"))
        )
        self.assertEqual(
            json['children'][1]['children'][0]['icon'],
            'fa fa-arrow-right'
        )

    def test_tree_luy_has_and_is_prerequisite(self):
        # self.learning_unit_year_1 is prerequisite
        PrerequisiteItemFactory(
            learning_unit=self.learning_unit_year_1.learning_unit,
            prerequisite=PrerequisiteFactory(education_group_year=self.parent)
        )
        # self.learning_unit_year_1 has prerequisite
        PrerequisiteItemFactory(
            prerequisite=PrerequisiteFactory(
                learning_unit_year=self.learning_unit_year_1,
                education_group_year=self.parent
            )
        )

        node = EducationGroupHierarchy(self.parent)
        json = node.to_json()

        self.assertEqual(
            json['children'][1]['children'][0]['a_attr']['title'],
            "{}\n{}".format(
                self.learning_unit_year_1.complete_title,
                _("The learning unit has prerequisites and is a prerequisite")
            )
        )
        self.assertEqual(
            json['children'][1]['children'][0]['icon'],
            'fa fa-exchange-alt'
        )

    def test_tree_to_json_a_attr(self):
        """In this test, we ensure that a attr contains some url for tree contextual menu"""
        node = EducationGroupHierarchy(self.parent)
        json = node.to_json()
        child = self.group_element_year_1.child_branch

        expected_modify_url = reverse('group_element_year_update', args=[
            self.parent.pk, child.pk, self.group_element_year_1.pk
        ])
        self.assertEqual(json['children'][0]['a_attr']['modify_url'], expected_modify_url)

        expected_attach_url = reverse('education_group_attach', args=[self.parent.pk, child.pk])
        self.assertEqual(json['children'][0]['a_attr']['attach_url'], expected_attach_url)

        expected_detach_url = reverse('group_element_year_delete', args=[
            self.parent.pk, child.pk, self.group_element_year_1.pk
        ])
        self.assertEqual(json['children'][0]['a_attr']['detach_url'], expected_detach_url)

    def test_build_tree_reference(self):
        """
        This tree contains a reference link.
        """
        self.group_element_year_1.link_type = LinkTypes.REFERENCE.name
        self.group_element_year_1.save()

        node = EducationGroupHierarchy(self.parent)

        self.assertEqual(node.children[0]._get_icon(), static('img/reference.jpg'))

        list_children = node.to_list()
        self.assertEqual(list_children, [
            self.group_element_year_1_1,
            self.group_element_year_2, [self.group_element_year_2_1]
        ])

    def test_node_to_list_flat(self):
        node = EducationGroupHierarchy(self.parent)
        list_children = node.to_list(flat=True)

        self.assertCountEqual(list_children, [
            self.group_element_year_1,
            self.group_element_year_1_1,
            self.group_element_year_2,
            self.group_element_year_2_1
        ])

    def test_node_to_list_with_pruning_function(self):
        """
        This test ensure that if the parameter pruning function is specified we only get the tree
        without node which has been pruned
        """
        node = EducationGroupHierarchy(self.parent)
        list_children = node.to_list(
            flat=True,
            pruning_function=lambda child: child.group_element_year.pk == self.group_element_year_2.pk
        )

        self.assertCountEqual(list_children, [self.group_element_year_2])

    @override_switch('luy_show_service_classes', active=True)
    def test_contains_luy_service(self):
        acronym = 'LTEST0022'
        GroupElementYearFactory(
            parent=self.group_element_year_2.child_branch,
            child_branch=None,
            child_leaf=LearningUnitYearFactory(acronym=acronym,
                                               learning_container_year__requirement_entity=self.MATH.entity,
                                               learning_container_year__allocation_entity=self.URBA.entity)
        )

        node = json.dumps(EducationGroupHierarchy(self.parent).to_json())
        str_expected_service = '|S| {}'.format(acronym)
        str_expected_not_service = '|S| LTEST0021'
        self.assertTrue(str_expected_service in node)
        self.assertTrue(str_expected_not_service not in node)

    @override_switch('luy_show_service_classes', active=True)
    def test_contains_luy_service_mobility(self):
        acronym = 'XTEST0022'
        eluy = ExternalLearningUnitYearFactory(learning_unit_year__acronym=acronym,
                                               learning_unit_year__academic_year=self.academic_year,
                                               mobility=True,
                                               co_graduation=False,
                                               learning_unit_year__learning_container_year__requirement_entity=
                                               self.MATH.entity,
                                               learning_unit_year__learning_container_year__allocation_entity=
                                               self.URBA.entity)
        luy = LearningUnitYear.objects.get(externallearningunityear=eluy)
        GroupElementYearFactory(
            parent=self.group_element_year_2.child_branch,
            child_branch=None,
            child_leaf=luy
        )

        node = json.dumps(EducationGroupHierarchy(self.parent).to_json())
        str_expected_service = '{}'.format(acronym)
        str_expected_not_service = '|S| {}'.format(acronym)
        self.assertTrue(str_expected_service in node)
        self.assertTrue(str_expected_not_service not in node)

    @override_switch('luy_show_service_classes', active=True)
    @override_switch('luy_show_borrowed_classes', active=True)
    def test_contains_luy_borrowed(self):
        acronym = 'LTEST0022'
        acronym2 = 'LTEST0023'
        GroupElementYearFactory(
            parent=self.group_element_year_2.child_branch,
            child_branch=None,
            child_leaf=LearningUnitYearFactory(acronym=acronym,
                                               academic_year=self.academic_year,
                                               learning_container_year__requirement_entity=self.BARC.entity)
        )
        GroupElementYearFactory(
            parent=self.group_element_year_2.child_branch,
            child_branch=None,
            child_leaf=LearningUnitYearFactory(acronym=acronym2,
                                               academic_year=self.academic_year,
                                               learning_container_year__requirement_entity=self.BARC.entity,
                                               learning_container_year__allocation_entity=self.MATH.entity)
        )

        node = json.dumps(EducationGroupHierarchy(self.parent).to_json())
        str_expected_borrowed = '|E| {}'.format(acronym)
        str_expected_borrowed2 = '|E|S| {}'.format(acronym2)
        str_expected_not_borrowed = '|E| LTEST0021'
        self.assertTrue(str_expected_borrowed in node)
        self.assertTrue(str_expected_borrowed2 in node)
        self.assertTrue(str_expected_not_borrowed not in node)

    @override_switch('luy_show_borrowed_classes', active=True)
    def test_contains_luy_borrowed_without_entity(self):
        acronym = 'LTEST0022'
        GroupElementYearFactory(
            parent=self.group_element_year_2.child_branch,
            child_branch=None,
            child_leaf=LearningUnitYearFactory(acronym=acronym)
        )

        node = json.dumps(EducationGroupHierarchy(self.parent).to_json())
        str_expected_not_borrowed = '|E| LTEST0022'
        self.assertTrue(acronym in node)
        self.assertTrue(str_expected_not_borrowed not in node)

    @override_switch('luy_show_borrowed_classes', active=True)
    def test_contains_luy_borrowed_school(self):
        acronym = 'LTEST0022'
        my_parent = EducationGroupYearFactory(acronym='LTEST0020',
                                              academic_year=self.academic_year,
                                              management_entity=self.EDDY.entity,
                                              administration_entity=self.EDDY.entity)
        GroupElementYearFactory(
            parent=my_parent,
            child_branch=None,
            child_leaf=LearningUnitYearFactory(acronym=acronym,
                                               learning_container_year__requirement_entity=self.MATH.entity)
        )

        node = json.dumps(EducationGroupHierarchy(my_parent).to_json())
        str_expected_borrowed = '|E| LTEST0022'
        self.assertTrue(str_expected_borrowed in node)

    @override_switch('luy_show_borrowed_classes', active=True)
    def test_contains_luy_borrowed_school_without_fac(self):
        acronym = 'LTEST0022'
        my_parent = EducationGroupYearFactory(acronym='LTEST0020',
                                              academic_year=self.academic_year,
                                              management_entity=self.E2DY.entity,
                                              administration_entity=self.E2DY.entity)
        GroupElementYearFactory(
            parent=my_parent,
            child_branch=None,
            child_leaf=LearningUnitYearFactory(acronym=acronym,
                                               learning_container_year__requirement_entity=self.MATH.entity)
        )

        node = json.dumps(EducationGroupHierarchy(my_parent).to_json())
        str_expected_borrowed = '|E| LTEST0022'
        self.assertFalse(str_expected_borrowed in node)

    @override_switch('luy_show_borrowed_classes', active=True)
    def test_contains_luy_borrowed_when_child_higher_entity_type_than_parent(self):
        acronym = 'LTEST0022'
        GroupElementYearFactory(
            parent=self.group_element_year_2.child_branch,
            child_branch=None,
            child_leaf=LearningUnitYearFactory(acronym=acronym,
                                               learning_container_year__requirement_entity=self.root.entity)
        )

        node = json.dumps(EducationGroupHierarchy(self.parent).to_json())
        str_expected_borrowed = '|E| {}'.format(acronym)
        self.assertTrue(str_expected_borrowed not in node)

    @override_switch('luy_show_borrowed_classes', active=True)
    def test_contains_luy_borrowed_mobility(self):
        acronym = 'XTEST0022'
        eluy = ExternalLearningUnitYearFactory(learning_unit_year__acronym=acronym,
                                               learning_unit_year__academic_year=self.academic_year,
                                               mobility=True,
                                               co_graduation=False,
                                               learning_unit_year__learning_container_year__requirement_entity=
                                               self.BARC.entity,
                                               learning_unit_year__learning_container_year__allocation_entity=
                                               self.BARC.entity)
        luy = LearningUnitYear.objects.get(externallearningunityear=eluy)
        GroupElementYearFactory(
            parent=self.group_element_year_2.child_branch,
            child_branch=None,
            child_leaf=luy
        )

        node = json.dumps(EducationGroupHierarchy(self.parent).to_json())
        str_expected_service = '{}'.format(acronym)
        str_expected_not_service = '|E| {}'.format(acronym)
        self.assertTrue(str_expected_service in node)
        self.assertTrue(str_expected_not_service not in node)

    @override_switch('luy_show_borrowed_classes', active=True)
    def test_contains_luy_borrowed_from_non_academic_entities(self):
        acronym = 'LTEST0022'
        GroupElementYearFactory(
            parent=self.parent_ILV,
            child_branch=None,
            child_leaf=LearningUnitYearFactory(acronym=acronym,
                                               academic_year=self.academic_year,
                                               learning_container_year__requirement_entity=self.BARC.entity)
        )

        node = json.dumps(EducationGroupHierarchy(self.parent_ILV).to_json())
        str_expected_borrowed = '|E| {}'.format(acronym)
        self.assertTrue(str_expected_borrowed in node)

    @override_switch('egy_show_borrowed_classes', active=True)
    def test_contains_egy_borrowed(self):
        acronym = 'LTEST0022'
        group = GroupElementYearFactory(
            parent=self.group_element_year_2.child_branch,
            child_branch=EducationGroupYearFactory(acronym=acronym,
                                                   academic_year=self.academic_year,
                                                   management_entity=self.URBA.entity, ),
            child_leaf=None
        )

        node = json.dumps(EducationGroupHierarchy(self.parent).to_json())
        str_expected_borrowed = '|E| {}'.format(group.child_branch.verbose)
        self.assertTrue(str_expected_borrowed in node)

    @override_switch('egy_show_borrowed_classes', active=True)
    def test_contains_egy_borrowed_without_entity(self):
        acronym = 'LTEST0022'
        group = GroupElementYearFactory(
            parent=self.group_element_year_2.child_branch,
            child_branch=EducationGroupYearFactory(acronym=acronym,
                                                   academic_year=self.academic_year,
                                                   management_entity=None),
            child_leaf=None
        )

        node = json.dumps(EducationGroupHierarchy(self.parent).to_json())
        str_expected_not_borrowed = '|E| {}'.format(group.child_branch.verbose)
        self.assertTrue(group.child_branch.verbose in node)
        self.assertTrue(str_expected_not_borrowed not in node)

    @override_switch('egy_show_borrowed_classes', active=True)
    def test_contains_egy_borrowed_school(self):
        acronym = 'LTEST0022'
        my_parent = EducationGroupYearFactory(acronym='LTEST0020',
                                              academic_year=self.academic_year,
                                              management_entity=self.EDDY.entity,
                                              administration_entity=self.EDDY.entity)
        group = GroupElementYearFactory(
            parent=my_parent,
            child_branch=EducationGroupYearFactory(acronym=acronym,
                                                   academic_year=self.academic_year,
                                                   management_entity=self.PHYS.entity, ),
            child_leaf=None
        )

        node = json.dumps(EducationGroupHierarchy(my_parent).to_json())
        str_expected_borrowed = '|E| {}'.format(group.child_branch.verbose)
        self.assertTrue(str_expected_borrowed in node)

    @override_switch('egy_show_borrowed_classes', active=True)
    def test_contains_egy_borrowed_school_without_fac(self):
        acronym = 'LTEST0022'
        my_parent = EducationGroupYearFactory(acronym='LTEST0020',
                                              academic_year=self.academic_year,
                                              management_entity=self.E2DY.entity,
                                              administration_entity=self.E2DY.entity)
        group = GroupElementYearFactory(
            parent=my_parent,
            child_branch=EducationGroupYearFactory(acronym=acronym,
                                                   academic_year=self.academic_year,
                                                   management_entity=self.URBA.entity, ),
            child_leaf=None
        )

        node = json.dumps(EducationGroupHierarchy(my_parent).to_json())
        str_expected_borrowed = '|E| {}'.format(group.child_branch.verbose)
        self.assertFalse(str_expected_borrowed in node)

    @override_switch('egy_show_borrowed_classes', active=True)
    def test_contains_egy_borrowed_when_child_higher_entity_type_than_parent(self):
        acronym = 'LTEST0022'
        group = GroupElementYearFactory(
            parent=self.group_element_year_2.child_branch,
            child_branch=EducationGroupYearFactory(acronym=acronym,
                                                   academic_year=self.academic_year,
                                                   management_entity=self.root.entity, ),
            child_leaf=None
        )

        node = json.dumps(EducationGroupHierarchy(self.parent).to_json())
        str_expected_borrowed = '|E| {}'.format(group.child_branch.verbose)
        self.assertTrue(str_expected_borrowed not in node)

    @override_switch('egy_show_borrowed_classes', active=True)
    def test_contains_egy_borrowed_from_non_academic_entities(self):
        acronym = 'LTEST0022'
        group = GroupElementYearFactory(
            parent=self.parent_ILV,
            child_branch=EducationGroupYearFactory(acronym=acronym,
                                                   academic_year=self.academic_year,
                                                   management_entity=self.BARC.entity, ),
            child_leaf=None
        )

        node = json.dumps(EducationGroupHierarchy(self.parent_ILV).to_json())
        str_expected_borrowed = '|E| {}'.format(group.child_branch.verbose)
        self.assertTrue(str_expected_borrowed in node)


class TestGetOptionList(TestCase):
    def setUp(self):
        self.academic_year = AcademicYearFactory(current=True)
        self.root = EducationGroupYearFactory(academic_year=self.academic_year)

    def test_get_option_list_case_no_result(self):
        node = EducationGroupHierarchy(self.root)
        self.assertListEqual(node.get_option_list(), [])

    def test_get_option_list_case_result_found(self):
        option_1 = EducationGroupYearFactory(
            academic_year=self.academic_year,
            education_group_type__name=MiniTrainingType.OPTION.name
        )
        GroupElementYearFactory(parent=self.root, child_branch=option_1)
        node = EducationGroupHierarchy(self.root)

        self.assertListEqual(node.get_option_list(), [option_1])

    def test_get_option_list_case_reference_link(self):
        """
          This test ensure that the tree will not be pruned when the link of child is reference
        """
        reference_group_child = EducationGroupYearFactory(
            academic_year=self.academic_year,
            education_group_type__name=GroupType.SUB_GROUP.name
        )
        GroupElementYearFactory(
            parent=self.root,
            child_branch=reference_group_child,
            link_type=LinkTypes.REFERENCE.name,
        )

        option_1 = EducationGroupYearFactory(
            academic_year=self.academic_year,
            education_group_type__name=MiniTrainingType.OPTION.name
        )
        GroupElementYearFactory(parent=reference_group_child, child_branch=option_1)
        node = EducationGroupHierarchy(self.root)

        self.assertListEqual(node.get_option_list(), [option_1])

    def test_get_option_list_case_multiple_result_found_on_different_children(self):
        list_option = []
        for _ in range(5):
            group_child = EducationGroupYearFactory(
                academic_year=self.academic_year,
                education_group_type__name=GroupType.SUB_GROUP.name
            )
            GroupElementYearFactory(parent=self.root, child_branch=group_child)

            option = EducationGroupYearFactory(
                academic_year=self.academic_year,
                education_group_type__name=MiniTrainingType.OPTION.name
            )
            list_option.append(option)
            GroupElementYearFactory(parent=group_child, child_branch=option)

        node = EducationGroupHierarchy(self.root)
        self.assertCountEqual(node.get_option_list(), list_option)

    def test_get_option_list_case_ignore_finality_list_choice(self):
        """
        This test ensure that the tree will be pruned when a child if type of finality list choice and option
        isn't considered as part of tree
        """
        option_1 = EducationGroupYearFactory(
            academic_year=self.academic_year,
            education_group_type__name=MiniTrainingType.OPTION.name
        )
        GroupElementYearFactory(parent=self.root, child_branch=option_1)

        for finality_type in [GroupType.FINALITY_120_LIST_CHOICE.name, GroupType.FINALITY_180_LIST_CHOICE.name]:
            finality_group = EducationGroupYearFactory(
                academic_year=self.academic_year,
                education_group_type__name=finality_type
            )
            GroupElementYearFactory(parent=self.root, child_branch=finality_group)
            GroupElementYearFactory(parent=finality_group, child_branch=EducationGroupYearFactory(
                academic_year=self.academic_year,
                education_group_type__name=MiniTrainingType.OPTION.name
            ))

        node = EducationGroupHierarchy(self.root)
        self.assertListEqual(node.get_option_list(), [option_1])


class TestGetFinalityList(TestCase):
    def setUp(self):
        self.academic_year = AcademicYearFactory(current=True)
        self.root = EducationGroupYearFactory(academic_year=self.academic_year)

    def test_get_finality_list_case_no_result(self):
        node = EducationGroupHierarchy(self.root)
        self.assertListEqual(node.get_finality_list(), [])

    def test_get_finality_list_case_result_found(self):
        finality_list = EducationGroupYearFactory(
            academic_year=self.academic_year,
            education_group_type__name=GroupType.FINALITY_120_LIST_CHOICE
        )
        finality_1 = EducationGroupYearFactory(
            academic_year=self.academic_year,
            education_group_type__name=TrainingType.MASTER_MS_120.name
        )
        GroupElementYearFactory(parent=self.root, child_branch=finality_list)
        GroupElementYearFactory(parent=finality_list, child_branch=finality_1)
        node = EducationGroupHierarchy(self.root)

        self.assertListEqual(node.get_finality_list(), [finality_1])

    def test_get_finality_list_case_reference_link(self):
        """
          This test ensure that the tree will not be pruned when the link of child is reference
        """
        reference_group_child = EducationGroupYearFactory(
            academic_year=self.academic_year,
            education_group_type__name=GroupType.SUB_GROUP.name
        )
        GroupElementYearFactory(
            parent=self.root,
            child_branch=reference_group_child,
            link_type=LinkTypes.REFERENCE.name,
        )

        finality_1 = EducationGroupYearFactory(
            academic_year=self.academic_year,
            education_group_type__name=TrainingType.MASTER_MS_120.name
        )

        GroupElementYearFactory(parent=reference_group_child, child_branch=finality_1)
        node = EducationGroupHierarchy(self.root)

        self.assertListEqual(node.get_finality_list(), [finality_1])

    def test_get_finality_list_case_multiple_result_found_on_different_children(self):
        list_finality = []
        for _ in range(5):
            group_child = EducationGroupYearFactory(
                academic_year=self.academic_year,
                education_group_type__name=GroupType.SUB_GROUP.name
            )
            GroupElementYearFactory(parent=self.root, child_branch=group_child)

            finality = EducationGroupYearFactory(
                academic_year=self.academic_year,
                education_group_type__name=TrainingType.MASTER_MS_120.name
            )
            list_finality.append(finality)
            GroupElementYearFactory(parent=group_child, child_branch=finality)

        node = EducationGroupHierarchy(self.root)
        self.assertCountEqual(node.get_finality_list(), list_finality)
