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
import json
from typing import Dict, List

import factory.fuzzy

from base.models.authorized_relationship import AuthorizedRelationshipObject, AuthorizedRelationshipList
from base.models.enums import education_group_types
from base.models.enums.education_group_types import TrainingType
from program_management.models.enums import node_type


class AuthorizedRelationshipObjectFactory(factory.Factory):

    class Meta:
        model = AuthorizedRelationshipObject
        abstract = False

    parent_type = factory.fuzzy.FuzzyChoice(TrainingType)
    child_type = factory.fuzzy.FuzzyChoice(TrainingType)
    min_count_authorized = factory.fuzzy.FuzzyInteger(0, 10)
    max_count_authorized = factory.fuzzy.FuzzyInteger(0, 10)


class MandatoryRelationshipObjectFactory(AuthorizedRelationshipObjectFactory):
    min_count_authorized = 1
    max_count_authorized = 1


def generate_auth_relation(obj):
    return [AuthorizedRelationshipObjectFactory()]


class AuthorizedRelationshipListFactory(factory.Factory):

    class Meta:
        model = AuthorizedRelationshipList
        abstract = False

    authorized_relationships = factory.LazyAttribute(generate_auth_relation)

    @classmethod
    def load_from_fixture(cls) -> 'AuthorizedRelationshipList':
        fixture_path = "base/fixtures/authorized_relationship.json"
        with open(fixture_path, "r") as fixture_file:
            json_fixture = json.load(fixture_file)
            relationships = [cls._fixture_data_to_authorized_relationship_object(data) for data in json_fixture]
            relationships.extend(cls._generate_learning_unit_authorized_relationship_objects())
            return cls(authorized_relationships=relationships)

    @classmethod
    def _fixture_data_to_authorized_relationship_object(cls, fixture_data: Dict) -> 'AuthorizedRelationshipObject':
        return AuthorizedRelationshipObjectFactory(
            parent_type=cls._get_education_group_type(fixture_data["fields"]["parent_type"][0]),
            child_type=cls._get_education_group_type(fixture_data["fields"]["child_type"][0]),
            min_count_authorized=fixture_data["fields"]["min_count_authorized"],
            max_count_authorized=fixture_data["fields"]["max_count_authorized"]
        )

    @classmethod
    def _get_education_group_type(cls, name: str) -> education_group_types.EducationGroupTypesEnum:
        try:
            return education_group_types.TrainingType[name]
        except KeyError:
            pass
        try:
            return education_group_types.MiniTrainingType[name]
        except KeyError:
            pass
        return education_group_types.GroupType[name]

    @classmethod
    def _generate_learning_unit_authorized_relationship_objects(cls) -> List['AuthorizedRelationshipObject']:
        return [
            AuthorizedRelationshipObjectFactory(
                parent_type=education_group_types.GroupType.SUB_GROUP,
                child_type=node_type.NodeType.LEARNING_UNIT,
                min_count_authorized=0,
                max_count_authorized=None
            ),
            AuthorizedRelationshipObjectFactory(
                parent_type=education_group_types.GroupType.COMPLEMENTARY_MODULE,
                child_type=node_type.NodeType.LEARNING_UNIT,
                min_count_authorized=0,
                max_count_authorized=None
            ),
            AuthorizedRelationshipObjectFactory(
                parent_type=education_group_types.GroupType.COMMON_CORE,
                child_type=node_type.NodeType.LEARNING_UNIT,
                min_count_authorized=0,
                max_count_authorized=None
            )
        ]
