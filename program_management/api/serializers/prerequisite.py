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

from rest_framework import serializers

from learning_unit.api.serializers.utils import LearningUnitDDDHyperlinkedIdentityField
from program_management.ddd.business_types import *
from program_management.ddd.domain.node import Node


class NodeBaseSerializer(serializers.Serializer):
    title = serializers.SerializerMethodField()
    title_en = serializers.SerializerMethodField()
    url = LearningUnitDDDHyperlinkedIdentityField(read_only=True)
    code = serializers.CharField(read_only=True)

    def get_title(self, obj: 'Node'):
        specific_title = getattr(obj, 'specific_title_fr')
        common_title = getattr(obj, 'common_title_fr')

        return self._get_complete_title(common_title, specific_title)

    @staticmethod
    def _get_complete_title(common_title: str, specific_title: str) -> str:
        complete_title = specific_title
        if common_title:
            complete_title = common_title + (' - ' + specific_title if specific_title else '')
        return complete_title

    def get_title_en(self, obj: 'Node'):
        specific_title = getattr(obj, 'specific_title_en')
        common_title = getattr(obj, 'common_title_en')

        return self._get_complete_title(common_title, specific_title)


class ProgramTreePrerequisitesSerializer(NodeBaseSerializer):
    prerequisites_string = serializers.SerializerMethodField()
    prerequisites = serializers.SerializerMethodField()

    def get_prerequisites_string(self, obj: 'NodeLearningUnitYear'):
        prerequisites = self.context['tree'].get_prerequisite(obj)
        return prerequisites.get_prerequisite_expression(translate=False)

    def get_prerequisites(self, obj: 'NodeLearningUnitYear'):
        list_nodes = []
        for prig in self.context['tree'].get_prerequisite(obj).prerequisite_item_groups:
            for prerequisite in prig.prerequisite_items:
                node = self.context.get('tree').get_node_by_code_and_year(prerequisite.code, prerequisite.year)
                list_nodes.append(node)
        return NodeBaseSerializer(list_nodes, many=True, context=self.context).data
