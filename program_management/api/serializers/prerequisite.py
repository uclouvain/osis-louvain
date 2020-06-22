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
from program_management.ddd.domain.node import Node


class NodeBaseSerializer(serializers.Serializer):
    title = serializers.SerializerMethodField()
    url = LearningUnitDDDHyperlinkedIdentityField(read_only=True)
    code = serializers.CharField(read_only=True)

    def get_title(self, obj: 'Node'):
        lang = self.context.get('language', 'fr').lower()
        lang = 'fr' if lang == 'fr-be' else lang
        specific_title = getattr(obj, 'specific_title_{}'.format(lang))
        common_title = getattr(obj, 'common_title_{}'.format(lang))

        complete_title = specific_title
        if common_title:
            complete_title = common_title + (' - ' + specific_title if specific_title else '')
        return complete_title


class ProgramTreePrerequisitesSerializer(NodeBaseSerializer):
    prerequisites_string = serializers.CharField(source='prerequisite', read_only=True)
    prerequisites = serializers.SerializerMethodField()

    def get_prerequisites(self, obj: 'Node'):
        list_nodes = []
        for prig in obj.prerequisite.prerequisite_item_groups:
            for prerequisite in prig.prerequisite_items:
                node = self.context.get('tree').get_node_by_code_and_year(prerequisite.code, prerequisite.year)
                list_nodes.append(node)
        return NodeBaseSerializer(list_nodes, many=True, context=self.context).data
