import functools
from typing import List, Dict, Union, Optional

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views import View

from base.utils.urls import reverse_with_get
from base.views.common import display_success_messages, display_error_messages
from education_group.ddd import command
from education_group.ddd.business_types import *
from education_group.ddd.domain import exception, group
from education_group.ddd.service.read import get_group_service, get_multiple_groups_service
from education_group.forms import content as content_forms
from education_group.templatetags.academic_year_display import display_as_academic_year
from learning_unit.ddd import command as command_learning_unit_year
from learning_unit.ddd.business_types import *
from learning_unit.ddd.domain import learning_unit_year
from learning_unit.ddd.service.read import get_multiple_learning_unit_years_service
from osis_role.contrib.views import PermissionRequiredMixin
from program_management.ddd import command as command_program_management
from program_management.ddd.business_types import *
from program_management.ddd.service.read import get_program_tree_service, get_program_tree_version_from_node_service
from program_management.ddd.service.write import update_link_service
from program_management.models.enums.node_type import NodeType
from program_management.ddd.domain import exception as program_exception


class ContentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'base.change_educationgroup'
    raise_exception = True

    template_name = "program_management/content/update.html"

    def get(self, request, *args, **kwargs):
        context = {
            "content_formset": self.content_formset,
            "tabs": self.get_tabs(),
            "group_obj": self.get_group_obj(),
            "cancel_url": self.get_cancel_url(),
            "version": self.get_version()
        }
        return render(request, self.template_name, context)

    def get_version(self) -> Optional['ProgramTreeVersion']:
        try:
            get_cmd = command_program_management.GetProgramTreeVersionFromNodeCommand(
                code=self.kwargs['code'],
                year=self.kwargs['year']
            )
            return get_program_tree_version_from_node_service.get_program_tree_version_from_node(get_cmd)
        except program_exception.ProgramTreeVersionNotFoundException:
            return None

    def get_tabs(self) -> List:
        return [
            {
                "text": _("Content"),
                "active": True,
                "display": True,
                "include_html": "program_management/content/block/panel_content.html"
            },
        ]

    def post(self, request, *args, **kwargs):
        if self.content_formset.is_valid():
            updated_links = self.update_links()

            success_messages = self.get_success_msg_updated_links(updated_links)
            display_success_messages(request, success_messages, extra_tags='safe')
            return HttpResponseRedirect(self.get_success_url())

        display_error_messages(self.request, self._get_default_error_messages())
        return self.get(request, *args, **kwargs)

    def get_success_url(self) -> str:
        get_data = {'path': self.request.GET['path_to']} if self.request.GET.get('path_to') else {}
        return reverse_with_get(
            'element_content',
            kwargs={'code': self.kwargs['code'], 'year': self.kwargs['year']},
            get=get_data
        )

    def get_cancel_url(self) -> str:
        return self.get_success_url()

    def update_links(self) -> List['Link']:
        update_link_commands = [
            self._convert_form_to_update_link_command(form) for form in self.content_formset.forms if form.has_changed()
        ]

        if not update_link_commands:
            return []

        cmd_bulk = command_program_management.BulkUpdateLinkCommand(
            parent_node_code=self.kwargs['code'],
            parent_node_year=self.kwargs['year'],
            update_link_cmds=update_link_commands
        )
        return update_link_service.bulk_update_links(cmd_bulk)

    def get_attach_path(self) -> Optional['Path']:
        return self.request.GET.get('path_to') or None

    @cached_property
    def content_formset(self) -> 'content_forms.ContentFormSet':
        return content_forms.ContentFormSet(
            self.request.POST or None,
            initial=self._get_content_formset_initial_values(),
            form_kwargs=[
                {'parent_obj': self.get_group_obj(), 'child_obj': child}
                for child in self.get_children_objs()
            ]
        )

    def get_group_obj(self) -> 'Group':
        try:
            get_cmd = command.GetGroupCommand(code=self.kwargs["code"], year=int(self.kwargs["year"]))
            return get_group_service.get_group(get_cmd)
        except exception.GroupNotFoundException:
            raise Http404

    @functools.lru_cache()
    def get_program_tree_obj(self) -> 'ProgramTree':
        get_cmd = command_program_management.GetProgramTree(code=self.kwargs['code'], year=self.kwargs['year'])
        return get_program_tree_service.get_program_tree(get_cmd)

    @functools.lru_cache()
    def get_children_objs(self) -> List[Union['Group', 'LearningUnitYear']]:
        children_objs = self.__get_children_group_objs() + self.__get_children_learning_unit_year_objs()
        return sorted(
            children_objs,
            key=lambda child_obj: next(
                order for order, node in enumerate(self.get_program_tree_obj().root_node.get_direct_children_as_nodes())
                if (isinstance(child_obj, group.Group) and node.code == child_obj.code) or
                (isinstance(child_obj, learning_unit_year.LearningUnitYear) and node.code == child_obj.acronym)
            )
        )

    def __get_children_group_objs(self) -> List['Group']:
        get_group_cmds = [
            command.GetGroupCommand(code=node.code, year=node.year)
            for node
            in self.get_program_tree_obj().root_node.get_direct_children_as_nodes(
                ignore_children_from={NodeType.LEARNING_UNIT}
            )
        ]
        if get_group_cmds:
            return get_multiple_groups_service.get_multiple_groups(get_group_cmds)
        return []

    def __get_children_learning_unit_year_objs(self) -> List['LearningUnitYear']:
        get_learning_unit_cmds = [
            command_learning_unit_year.GetLearningUnitYearCommand(code=node.code, year=node.year)
            for node in self.get_program_tree_obj().root_node.get_direct_children_as_nodes(
                take_only={NodeType.LEARNING_UNIT}
            )
        ]
        if get_learning_unit_cmds:
            return get_multiple_learning_unit_years_service.get_multiple_learning_unit_years(get_learning_unit_cmds)
        return []

    def get_success_msg_updated_links(self, links: List['Link']) -> List[str]:
        messages = []

        for link in links:
            msg = _("The link of %(code)s - %(acronym)s - %(year)s has been updated.") % {
                "acronym": link.child.title,
                "code": link.entity_id.child_code,
                "year": display_as_academic_year(link.entity_id.child_year)
            }
            messages.append(msg)

        return messages

    def _get_default_error_messages(self) -> str:
        return _("Error(s) in form: The modifications are not saved")

    def _get_content_formset_initial_values(self) -> List[Dict]:
        children_links = self.get_program_tree_obj().root_node.children
        return [{
            'relative_credits': link.relative_credits,
            'is_mandatory': link.is_mandatory,
            'link_type': link.link_type.name if link.link_type else None,
            'access_condition': link.access_condition,
            'block': link.block,
            'comment_fr': link.comment,
            'comment_en': link.comment_english
        } for link in children_links]

    def _convert_form_to_update_link_command(
            self,
            form: 'content_forms.LinkForm') -> command_program_management.UpdateLinkCommand:
        return command_program_management.UpdateLinkCommand(
            child_node_code=form.child_obj.code if isinstance(form.child_obj, group.Group) else form.child_obj.acronym,
            child_node_year=form.child_obj.year,
            access_condition=form.cleaned_data.get('access_condition', False),
            is_mandatory=form.cleaned_data.get('is_mandatory', True),
            block=form.cleaned_data.get('block'),
            link_type=form.cleaned_data.get('link_type'),
            comment=form.cleaned_data.get('comment_fr'),
            comment_english=form.cleaned_data.get('comment_en'),
            relative_credits=form.cleaned_data.get('relative_credits'),
        )
