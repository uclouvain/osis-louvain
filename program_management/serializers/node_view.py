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
from collections import namedtuple
from typing import List, Dict

from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from backoffice.settings.base import LANGUAGE_CODE_EN
from base.models.enums import link_type
from base.models.enums.proposal_type import ProposalType
from base.utils.urls import reverse_with_get
from program_management.ddd.business_types import *
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.domain.program_tree import PATH_SEPARATOR
from program_management.ddd.domain.service.identity_search import ProgramTreeIdentitySearch
from program_management.models.enums.node_type import NodeType

NodeViewContext = namedtuple('NodeViewContext', 'view_path root_node current_path')


def serialize_children(
        children: List['Link'],
        tree: 'ProgramTree',
        context: NodeViewContext,
) -> List[dict]:
    serialized_children = []
    for link in children:
        child_context = NodeViewContext(
            view_path=context.view_path,
            root_node=context.root_node,
            current_path=context.current_path + PATH_SEPARATOR + str(link.child.pk)
        )
        if link.child.is_learning_unit():
            serialized_node = _leaf_view_serializer(link, tree, child_context)
        else:
            serialized_node = _get_node_view_serializer(link, tree, child_context)
        serialized_children.append(serialized_node)
    return serialized_children


def _get_node_view_attribute_serializer(link: 'Link', tree: 'ProgramTree', context: NodeViewContext) -> dict:
    querystring_params = {"path": context.current_path, "redirect_path": context.view_path}

    return {
        'path': context.current_path,
        'href': reverse_with_get(
            'element_identification',
            args=[link.child.year, link.child.code],
            get={"path": context.current_path}
        ),
        'root': context.root_node.pk,
        'group_element_year': link.pk,
        'element_id': link.child.pk,
        'element_type': link.child.type.name,
        'element_code': link.child.code,
        'element_year': link.child.year,
        'title': link.child.code,
        'paste_url': reverse_with_get('tree_paste_node', get=querystring_params),
        'detach_url': reverse_with_get('tree_detach_node', get=querystring_params),
        'modify_url': reverse('tree_update_link', args=[
            link.parent.code,
            link.parent.year,
            link.child.code,
            link.child.year
        ]),
        'search_url': reverse_with_get(
            'quick_search_learning_unit' if tree.allows_learning_unit_child(
                link.child) else 'quick_search_education_group',
            args=[link.child.academic_year.year],
            get=querystring_params
        ),
    }


def _get_leaf_view_attribute_serializer(link: 'Link', tree: 'ProgramTree', context: NodeViewContext) -> dict:
    attrs = _get_node_view_attribute_serializer(link, tree, context)
    attrs.update({
        'path': context.current_path,
        'icon': None,
        'href': reverse_with_get(
            'learning_unit_utilization',
            args=[context.root_node.pk, link.child.pk],
            get={"path": context.current_path}
        ),
        'paste_url': None,
        'search_url': None,
        'has_prerequisite': tree.has_prerequisites(link.child),
        'is_prerequisite': tree.is_prerequisite(link.child),
        'class': __get_css_class(link),
        'element_type': NodeType.LEARNING_UNIT.name,
        'title': __get_title(tree, link),
    })
    return attrs


def __get_css_class(link: 'Link'):
    return {ProposalType.CREATION.name: "proposal proposal_creation",
            ProposalType.MODIFICATION.name: "proposal proposal_modification",
            ProposalType.TRANSFORMATION.name: "proposal proposal_transformation",
            ProposalType.TRANSFORMATION_AND_MODIFICATION.name: "proposal proposal_transformation_modification",
            ProposalType.SUPPRESSION.name: "proposal proposal_suppression"}.get(link.child.proposal_type) or ""


def __get_title(tree: 'ProgramTree', obj: 'Link') -> str:
    child_node = obj.child
    title = child_node.title
    has_prerequisite = tree.has_prerequisites(child_node)
    is_prerequisite = tree.is_prerequisite(child_node)
    if has_prerequisite and is_prerequisite:
        title = "%s\n%s" % (title, _("The learning unit has prerequisites and is a prerequisite"))
    elif has_prerequisite:
        title = "%s\n%s" % (title, _("The learning unit has prerequisites"))
    elif is_prerequisite:
        title = "%s\n%s" % (title, _("The learning unit is a prerequisite"))
    return title


def _get_node_view_serializer(
        link: 'Link',
        tree: 'ProgramTree',
        context: NodeViewContext,
) -> dict:

    return {
        'id': context.current_path,
        'path': context.current_path,
        'icon': _get_group_node_icon(link),
        'text': _format_node_group_text(link.child),
        'children': serialize_children(
            children=link.child.children,
            tree=tree,
            context=context,
        ),
        'a_attr': _get_node_view_attribute_serializer(link, tree, context),
    }


def _get_group_node_icon(obj: 'Link'):
    if obj.link_type == link_type.LinkTypes.REFERENCE:
        return static('img/reference.jpg')
    return None


def _leaf_view_serializer(link: 'Link', tree: 'ProgramTree', context: NodeViewContext) -> dict:
    return {
        'id': context.current_path,
        'path': context.current_path,
        'icon': __get_learning_unit_node_icon(tree, link),
        'text': __get_learning_unit_node_text(link, context),
        'a_attr': _get_leaf_view_attribute_serializer(link, tree, context),
    }


def __get_learning_unit_node_icon(tree: 'ProgramTree', link: 'Link') -> str:
    child_node = link.child
    has_prerequisite = tree.has_prerequisites(child_node)
    is_prerequisite = tree.is_prerequisite(child_node)
    if has_prerequisite and is_prerequisite:
        return "fa fa-exchange-alt"
    elif has_prerequisite:
        return "fa fa-arrow-left"
    elif is_prerequisite:
        return "fa fa-arrow-right"
    return "far fa-file"


def __get_learning_unit_node_text(link: 'Link', context: NodeViewContext):
    if context.root_node.year != link.child.year:
        return "|{}|{}".format(link.child.year, link.child.code)
    return link.child.code


def get_program_tree_version_name(node_identity: 'NodeIdentity', tree_versions: List['ProgramTreeVersion']):
    if tree_versions:
        program_tree_identity = ProgramTreeIdentitySearch().get_from_node_identity(node_identity)
        return next(
            (
                program_tree_version.version_label for program_tree_version in tree_versions
                if program_tree_version.program_tree_identity == program_tree_identity
            ),
            ''
        )
    return ''


def _format_node_group_text(node: 'NodeGroupYear') -> str:
    if node.version_name:
        return "{node.code} - {node.title}[{node.version_name}]".format(node=node)
    return "{node.code} - {node.title}".format(node=node)
