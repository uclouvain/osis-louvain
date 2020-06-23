from django.test import SimpleTestCase, RequestFactory, override_settings
from rest_framework.reverse import reverse

from base.models.enums import prerequisite_operator
from program_management.api.serializers.prerequisite import ProgramTreePrerequisitesSerializer, \
    NodeBaseSerializer
from program_management.ddd.domain import prerequisite
from program_management.ddd.domain.program_tree import ProgramTree
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory


@override_settings(LANGUAGES=[('fr', 'Français'), ], LANGUAGE_CODE='fr')
class TestEducationGroupPrerequisitesSerializer(SimpleTestCase):
    def setUp(self):
        """
        root_node
        |-----common_core
             |---- LDROI100A (UE) Prerequisites: LDROI1300 AND LAGRO2400
        |-----subgroup1
             |---- LDROI1300 (UE)
             |---- LAGRO2400 (UE)
        :return:
        """
        self.root_node = NodeGroupYearFactory(node_id=1, code="LBIR100B", title="Bachelier en droit", year=2018)
        self.common_core = NodeGroupYearFactory(node_id=2, code="LGROUP100A", title="Tronc commun", year=2018)
        self.subgroup1 = NodeGroupYearFactory(node_id=3, code="LGROUP101A", title="Sous-groupe 1", year=2018)
        self.ldroi100a = NodeLearningUnitYearFactory(node_id=4,
                                                     code="LDROI100A",
                                                     common_title_fr="Introduction",
                                                     specific_title_fr="Partie 1",
                                                     year=2018)

        self.ldroi1300 = NodeLearningUnitYearFactory(node_id=5,
                                                     code="LDROI1300",
                                                     common_title_fr="Introduction droit",
                                                     specific_title_fr="Partie 1",
                                                     year=2018)
        self.lagro2400 = NodeLearningUnitYearFactory(node_id=6,
                                                     code="LAGRO2400",
                                                     common_title_fr="Séminaire agro",
                                                     specific_title_fr="Partie 1",
                                                     year=2018)

        LinkFactory(parent=self.root_node, child=self.common_core)
        LinkFactory(parent=self.common_core, child=self.ldroi100a)
        LinkFactory(parent=self.root_node, child=self.subgroup1)
        LinkFactory(parent=self.subgroup1, child=self.ldroi1300)
        LinkFactory(parent=self.subgroup1, child=self.lagro2400)

        self.p_group = prerequisite.PrerequisiteItemGroup(operator=prerequisite_operator.AND)
        self.p_group.add_prerequisite_item('LDROI1300', 2018)
        self.p_group2 = prerequisite.PrerequisiteItemGroup(operator=prerequisite_operator.AND)
        self.p_group2.add_prerequisite_item('LAGRO2400', 2018)

        p_req = prerequisite.Prerequisite(main_operator=prerequisite_operator.AND)
        p_req.add_prerequisite_item_group(self.p_group)
        p_req.add_prerequisite_item_group(self.p_group2)
        self.ldroi100a.set_prerequisite(p_req)

        self.tree = ProgramTree(root_node=self.root_node)

        url = reverse('program_management_api_v1:training-prerequisites_official',
                      kwargs={'year': self.root_node.year, 'acronym': self.root_node.code})
        self.request = RequestFactory().get(url)
        self.serializer = ProgramTreePrerequisitesSerializer(self.ldroi100a, context={
            'request': self.request,
            'language': 'fr',
            'tree': self.tree
        })

    def test_contains_expected_fields(self):
        expected_fields = [
            'title',
            'url',
            'code',
            'prerequisites_string',
            'prerequisites',
        ]
        self.assertListEqual(expected_fields, list(self.serializer.data.keys()))

    def test_read_prerequisite_on_training(self):
        with self.subTest('title'):
            self.assertEqual(self.ldroi100a.common_title_fr + ' - ' + self.ldroi100a.specific_title_fr,
                             self.serializer.data.get('title'))

        with self.subTest('url'):
            url = reverse('learning_unit_api_v1:learningunits_read',
                          kwargs={'year': self.ldroi100a.year, 'acronym': self.ldroi100a.code},
                          request=self.request)
            self.assertEqual(url, self.serializer.data.get('url'))

        with self.subTest('code'):
            self.assertEqual(self.ldroi100a.code, self.serializer.data.get('code'))

        with self.subTest('prerequisites_string'):
            self.assertEqual(str(self.ldroi100a.prerequisite), self.serializer.data.get('prerequisites_string'))


class TestLearningUnitBaseSerializer(SimpleTestCase):
    def setUp(self):
        self.ldroi1300 = NodeLearningUnitYearFactory(node_id=7,
                                                     code="LDROI1300",
                                                     common_title_fr="Introduction droit",
                                                     specific_title_fr="Partie 1",
                                                     year=2018)

        url = reverse('program_management_api_v1:training-prerequisites_official',
                      kwargs={'year': 2018, 'acronym': 'LDROI1300'})
        self.request = RequestFactory().get(url)
        self.serializer = NodeBaseSerializer(self.ldroi1300, context={
            'request': self.request,
            'language': 'fr',
        })

    def test_title_with_only_common_title_if_no_specific(self):
        node_lu = NodeLearningUnitYearFactory(node_id=7,
                                              code="LDROI1302",
                                              common_title_fr="Introduction droit",
                                              year=2018)

        url = reverse('program_management_api_v1:training-prerequisites_official',
                      kwargs={'year': 2018, 'acronym': 'LDROI1302'})
        request = RequestFactory().get(url)
        serializer = NodeBaseSerializer(node_lu, context={
            'request': request,
            'language': 'fr',
        })
        self.assertEqual(serializer.data['title'], node_lu.common_title_fr)

    def test_contains_expected_fields(self):
        expected_fields = [
            'title',
            'url',
            'code',
        ]
        self.assertListEqual(expected_fields, list(self.serializer.data.keys()))

    def test_read(self):
        with self.subTest('title'):
            self.assertEqual(self.ldroi1300.common_title_fr + ' - ' + self.ldroi1300.specific_title_fr,
                             self.serializer.data.get('title'))

        with self.subTest('url'):
            url = reverse('learning_unit_api_v1:learningunits_read',
                          kwargs={'year': self.ldroi1300.year, 'acronym': self.ldroi1300.code},
                          request=self.request)
            self.assertEqual(url, self.serializer.data.get('url'))

        with self.subTest('code'):
            self.assertEqual(self.ldroi1300.code, self.serializer.data.get('code'))
