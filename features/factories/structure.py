import random

from base.models.entity_version import EntityVersion
from base.models.enums import entity_type
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity_version import MainEntityVersionFactory
from base.tests.factories.organization import MainOrganizationFactory


class StructureGenerator:
    def __init__(self):
        self.entity_tree = EntityVersionTreeGenerator()
        self.campuses = CampusGenerator()


class EntityVersionTreeGenerator:

    class Node:
        def __init__(self, element: EntityVersion):
            self.element = element
            self.children = []

    def __init__(self):
        self.root = self.Node(MainEntityVersionFactory(parent=None, entity_type=""))
        self.nodes = [self.root]
        self._genererate_tree(self.root)

    def _genererate_tree(self, parent: Node):
        number_nodes_to_generate = random.randint(1, 6)
        for _ in range(number_nodes_to_generate):
            child_entity_type = self.entity_type_to_generate(parent.element.entity_type)
            if child_entity_type is None:
                continue

            child = self.Node(
                MainEntityVersionFactory(parent=parent.element.entity, entity_type=child_entity_type)
            )
            parent.children.append(child)
            self.nodes.append(child)

            self._genererate_tree(child)

    def entity_type_to_generate(self, parent_entity_type):
        type_based_on_parent_type = {
            entity_type.SECTOR: (entity_type.FACULTY, entity_type.LOGISTICS_ENTITY),
            entity_type.FACULTY: (entity_type.PLATFORM, entity_type.SCHOOL, entity_type.INSTITUTE),
            entity_type.LOGISTICS_ENTITY: (entity_type.INSTITUTE, ),
            entity_type.SCHOOL: (None, ),
            entity_type.INSTITUTE: (None, entity_type.POLE, entity_type.PLATFORM),
            entity_type.POLE: (None, ),
            entity_type.DOCTORAL_COMMISSION: (None, ),
            entity_type.PLATFORM: (None, ),
        }
        return random.choice(
            type_based_on_parent_type.get(parent_entity_type, (entity_type.SECTOR, ))
        )


class CampusGenerator:
    def __init__(self):
        main_organization = MainOrganizationFactory()
        self.main_campuses = CampusFactory.create_batch(5, organization=main_organization)
