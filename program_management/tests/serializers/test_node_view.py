##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from urllib.parse import urlencode

import mock
from django.test import SimpleTestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from base.models.enums import link_type
from base.models.enums.proposal_type import ProposalType
from program_management.ddd.domain.link import Link
from program_management.models.enums.node_type import NodeType
from program_management.serializers.node_view import NodeViewAttributeSerializer, LeafViewAttributeSerializer, \
    NodeViewSerializer, LeafViewSerializer
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory


class TestNodeViewSerializer(SimpleTestCase):
    def setUp(self):
        self.root_node = NodeGroupYearFactory(node_id=1, acronym="LBIR100A", title="BIR1BA", year=2018)
        node_parent = NodeGroupYearFactory(node_id=2, acronym="LTROC250T", title="Tronc commun 2", year=2018)
        node_child = NodeGroupYearFactory(node_id=6, acronym="LSUBGR150G", title="Sous-groupe 2", year=2018)
        self.link = Link(parent=node_parent, child=node_child)

        self.context = {'path': '1|2|6', 'root': self.root_node}
        self.serializer = NodeViewSerializer(self.link, context=self.context)

    def test_serialize_node_ensure_text(self):
        expected_text = self.link.child.acronym
        self.assertEquals(self.serializer.data['text'], expected_text)

    def test_serialize_node_ensure_icon_case_concrete_link(self):
        self.link.link_type = None
        self.assertIsNone(self.serializer.data['icon'])

    def test_serialize_node_ensure_icon_case_reference_link(self):
        self.link.link_type = link_type.LinkTypes.REFERENCE.name

        expected_icon_path = 'img/reference.jpg'
        self.assertIn(expected_icon_path, self.serializer.data['icon'])


class TestNodeViewAttributeSerializer(SimpleTestCase):
    def setUp(self):
        self.root_node = NodeGroupYearFactory(node_id=1, acronym="LBIR100A", title="BIR1BA", year=2018)
        node_parent = NodeGroupYearFactory(node_id=2, acronym="LTROC250T", title="Tronc commun 2", year=2018)
        node_child = NodeGroupYearFactory(node_id=6, acronym="LSUBGR150G", title="Sous-groupe 2", year=2018)
        self.link = Link(parent=node_parent, child=node_child)

        self.context = {'path': '1|2|6', 'root': self.root_node}
        self.serializer = NodeViewAttributeSerializer(self.link, context=self.context)

    def test_serialize_node_attr_ensure_detach_url(self):
        expected_url = reverse('tree_detach_node', args=[self.root_node.pk]) + "?" + urlencode({
            'path': self.context['path']
        })
        self.assertEquals(self.serializer.data['detach_url'], expected_url)

    def test_serialize_node_attr_ensure_attach_url(self):
        expected_url = reverse('tree_attach_node', args=[self.root_node.pk]) + "?" + urlencode({
            'to_path': self.context['path']
        })
        self.assertEquals(self.serializer.data['attach_url'], expected_url)

    def test_serialize_node_attr_ensure_modify_url(self):
        expected_url = reverse('tree_update_link', args=[self.root_node.pk]) + "?" + urlencode({
            'path': self.context['path']
        })
        self.assertEquals(self.serializer.data['modify_url'], expected_url)

    def test_serializer_node_attr_ensure_search_url(self):
        expected_url = reverse('quick_search_education_group', args=[self.root_node.pk, self.link.child.pk])
        self.assertEquals(self.serializer.data['search_url'], expected_url)

    def test_serializer_node_attr_ensure_get_title(self):
        expected_title = self.link.child.acronym
        self.assertEquals(self.serializer.data['title'], expected_title)

    def test_serializer_node_attr_ensure_get_href(self):
        expected_url = reverse('education_group_read', args=[self.root_node.pk, self.link.child.pk])
        self.assertEquals(self.serializer.data['href'], expected_url)

    def test_serializer_node_attr_ensure_element_id(self):
        self.assertEquals(self.serializer.data['element_id'], self.link.child.pk)


class TestLeafViewSerializer(SimpleTestCase):
    def setUp(self):
        self.root_node = NodeGroupYearFactory(node_id=1, acronym="LBIR100A", title="BIR1BA", year=2018)
        node_parent = NodeGroupYearFactory(node_id=2, acronym="LTROC250T", title="Tronc commun 2", year=2018)
        leaf_child = NodeLearningUnitYearFactory(node_id=9, acronym="LSUBGR150G", title="Sous-groupe 2", year=2018)
        self.link = Link(parent=node_parent, child=leaf_child)

        self.context = {'path': '1|2|9', 'root': self.root_node}
        self.serializer = LeafViewSerializer(self.link, context=self.context)

    def test_serializer_leaf_ensure_text_case_leaf_have_same_year_of_root(self):
        expected_text = self.link.child.title
        self.assertEquals(self.serializer.data['text'], expected_text)

    def test_serializer_leaf_ensure_text_case_leaf_doesnt_have_same_year_of_root(self):
        self.link.child.year = self.root_node.year - 1
        expected_text = self.link.child.title + "|" + str(self.link.child.year)

        self.assertEquals(self.serializer.data['text'], expected_text)

    @mock.patch('program_management.ddd.domain.node.NodeLearningUnitYear.has_prerequisite',
                new_callable=mock.PropertyMock,
                return_value=True)
    @mock.patch('program_management.ddd.domain.node.NodeLearningUnitYear.is_prerequisite',
                new_callable=mock.PropertyMock,
                return_value=True)
    def test_serializer_leaf_ensure_get_icon_with_prerequisites_and_is_prerequisite(
            self,
            mock_is_prerequisite,
            mock_has_prerequisite,
    ):
        expected_icon = "fa fa-exchange-alt"
        self.assertEquals(self.serializer.data['icon'], expected_icon)

    @mock.patch('program_management.ddd.domain.node.NodeLearningUnitYear.has_prerequisite',
                new_callable=mock.PropertyMock,
                return_value=False)
    @mock.patch('program_management.ddd.domain.node.NodeLearningUnitYear.is_prerequisite',
                new_callable=mock.PropertyMock,
                return_value=True)
    def test_serializer_leaf_ensure_get_icon_no_prerequisite_but_is_prerequisite(
            self,
            mock_is_prerequisite,
            mock_has_prerequisite,
    ):
        expected_icon = "fa fa-arrow-right"
        self.assertEquals(self.serializer.data['icon'], expected_icon)

    @mock.patch('program_management.ddd.domain.node.NodeLearningUnitYear.has_prerequisite',
                new_callable=mock.PropertyMock,
                return_value=True)
    @mock.patch('program_management.ddd.domain.node.NodeLearningUnitYear.is_prerequisite',
                new_callable=mock.PropertyMock,
                return_value=False)
    def test_serializer_leaf_ensure_get_icon_with_prerequisites_but_is_not_prerequisite(
            self,
            mock_is_prerequisite,
            mock_has_prerequisite,
    ):
        expected_icon = "fa fa-arrow-left"
        self.assertEquals(self.serializer.data['icon'], expected_icon)

    @mock.patch('program_management.ddd.domain.node.NodeLearningUnitYear.has_prerequisite',
                new_callable=mock.PropertyMock,
                return_value=False)
    @mock.patch('program_management.ddd.domain.node.NodeLearningUnitYear.is_prerequisite',
                new_callable=mock.PropertyMock,
                return_value=False)
    def test_serializer_leaf_ensure_get_icon_no_prerequisites_and_is_not_prerequisite(
            self,
            mock_is_prerequisite,
            mock_has_prerequisite,
    ):
        expected_icon = "far fa-file"
        self.assertEquals(self.serializer.data['icon'], expected_icon)


class TestLeafViewAttributeSerializer(SimpleTestCase):
    def setUp(self):
        self.root_node = NodeGroupYearFactory(node_id=1, acronym="LBIR100A", title="BIR1BA", year=2018)
        node_parent = NodeGroupYearFactory(node_id=2, acronym="LTROC250T", title="Tronc commun 2", year=2018)
        leaf_child = NodeLearningUnitYearFactory(node_id=9, acronym="LSUBGR150G", title="Sous-groupe 2", year=2018)
        self.link = Link(parent=node_parent, child=leaf_child)

        self.context = {'path': '1|2|9', 'root': self.root_node}
        self.serializer = LeafViewAttributeSerializer(self.link, context=self.context)

    def test_ensure_serializer_is_subclass_of_node_view_serializer(self):
        self.assertTrue(isinstance(self.serializer, NodeViewAttributeSerializer))

    def test_serializer_node_attr_ensure_get_href(self):
        expected_url = reverse('learning_unit_utilization', args=[self.root_node.pk, self.link.child.pk])
        self.assertEquals(self.serializer.data['href'], expected_url)

    def test_serializer_node_attr_ensure_get_element_type(self):
        self.assertEquals(self.serializer.data['element_type'], NodeType.LEARNING_UNIT)

    @mock.patch('program_management.ddd.domain.node.NodeLearningUnitYear.has_prerequisite',
                new_callable=mock.PropertyMock,
                return_value=True)
    @mock.patch('program_management.ddd.domain.node.NodeLearningUnitYear.is_prerequisite',
                new_callable=mock.PropertyMock,
                return_value=True)
    def test_serializer_node_attr_ensure_get_title_with_prerequisites_and_is_prerequisite(
            self,
            mock_is_prerequisite,
            mock_has_prerequisite,
    ):
        expected_title = "%s\n%s" % (self.link.child.title,
                                     _("The learning unit has prerequisites and is a prerequisite"))
        self.assertEquals(self.serializer.data['title'], expected_title)

    @mock.patch('program_management.ddd.domain.node.NodeLearningUnitYear.has_prerequisite',
                new_callable=mock.PropertyMock,
                return_value=False)
    @mock.patch('program_management.ddd.domain.node.NodeLearningUnitYear.is_prerequisite',
                new_callable=mock.PropertyMock,
                return_value=True)
    def test_serializer_node_attr_ensure_get_title_no_prerequisite_but_is_prerequisite(
            self,
            mock_is_prerequisite,
            mock_has_prerequisite,
    ):
        expected_title = "%s\n%s" % (self.link.child.title, _("The learning unit is a prerequisite"))
        self.assertEquals(self.serializer.data['title'], expected_title)

    @mock.patch('program_management.ddd.domain.node.NodeLearningUnitYear.has_prerequisite',
                new_callable=mock.PropertyMock,
                return_value=True)
    @mock.patch('program_management.ddd.domain.node.NodeLearningUnitYear.is_prerequisite',
                new_callable=mock.PropertyMock,
                return_value=False)
    def test_serializer_node_attr_ensure_get_title_with_prerequisites_but_is_not_prerequisite(
            self,
            mock_is_prerequisite,
            mock_has_prerequisite,
    ):
        expected_title = "%s\n%s" % (self.link.child.title, _("The learning unit has prerequisites"))
        self.assertEquals(self.serializer.data['title'], expected_title)

    @mock.patch('program_management.ddd.domain.node.NodeLearningUnitYear.has_prerequisite',
                new_callable=mock.PropertyMock,
                return_value=False)
    @mock.patch('program_management.ddd.domain.node.NodeLearningUnitYear.is_prerequisite',
                new_callable=mock.PropertyMock,
                return_value=False)
    def test_serializer_node_attr_ensure_get_title_no_prerequisites_and_is_not_prerequisite(
            self,
            mock_is_prerequisite,
            mock_has_prerequisite,
    ):
        expected_title = self.link.child.title
        self.assertEquals(self.serializer.data['title'], expected_title)

    def test_serializer_node_attr_ensure_get_css_class_proposal_creation(self):
        self.link.child.proposal_type = ProposalType.CREATION.name
        expected_css_class = "proposal proposal_creation"

        self.assertEquals(self.serializer.data['css_class'], expected_css_class)

    def test_serializer_node_attr_ensure_get_css_class_proposal_modification(self):
        self.link.child.proposal_type = ProposalType.MODIFICATION.name
        expected_css_class = "proposal proposal_modification"

        self.assertEquals(self.serializer.data['css_class'], expected_css_class)

    def test_serializer_node_attr_ensure_get_css_class_proposal_transformation(self):
        self.link.child.proposal_type = ProposalType.TRANSFORMATION.name
        expected_css_class = "proposal proposal_transformation"

        self.assertEquals(self.serializer.data['css_class'], expected_css_class)

    def test_serializer_node_attr_ensure_get_css_class_proposal_transformation_modification(self):
        self.link.child.proposal_type = ProposalType.TRANSFORMATION_AND_MODIFICATION.name
        expected_css_class = "proposal proposal_transformation_modification"

        self.assertEquals(self.serializer.data['css_class'], expected_css_class)

    def test_serializer_node_attr_ensure_get_css_class_proposal_suppression(self):
        self.link.child.proposal_type = ProposalType.SUPPRESSION.name
        expected_css_class = "proposal proposal_suppression"

        self.assertEquals(self.serializer.data['css_class'], expected_css_class)

    def test_serializer_node_attr_ensure_get_css_class_no_proposal(self):
        self.link.child.proposal_type = None
        expected_css_class = ""

        self.assertEquals(self.serializer.data['css_class'], expected_css_class)
