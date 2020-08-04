import functools
from typing import List, Union, Dict

from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django.shortcuts import render
from django.views import View
from rules.contrib.views import LoginRequiredMixin

from education_group.ddd.business_types import *
from program_management.ddd.business_types import *

import education_group.ddd.service.read.get_multiple_groups_service
from base.models import entity_version, academic_year, campus
from base.views.common import display_success_messages, display_error_messages
from education_group.ddd import command
from education_group.ddd.service.write import update_group_service
from education_group.templatetags.academic_year_display import display_as_academic_year
from education_group.views.proxy.read import Tab
from learning_unit.ddd import command as command_learning_unit_year
from learning_unit.ddd.domain.learning_unit_year import LearningUnitYear
from education_group.ddd.domain.group import Group
from learning_unit.ddd.service.read import get_multiple_learning_unit_years_service
from program_management.ddd import command as command_program_management
from education_group.ddd.domain.exception import GroupNotFoundException, ContentConstraintTypeMissing, \
    ContentConstraintMinimumMaximumMissing, ContentConstraintMaximumShouldBeGreaterOrEqualsThanMinimum, \
    CreditShouldBeGreaterOrEqualsThanZero
from education_group.ddd.service.read import get_group_service
from education_group.forms.content import ContentFormSet
from education_group.forms.group import GroupUpdateForm
from education_group.models.group_year import GroupYear
from osis_role.contrib.views import PermissionRequiredMixin
from program_management.ddd.domain.program_tree import ProgramTree
from program_management.ddd.service.read import get_program_tree_service
from program_management.ddd.service.write import update_link_service
from program_management.models.enums.node_type import NodeType


class GroupUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    # PermissionRequiredMixin
    permission_required = 'base.change_educationgroup'
    raise_exception = True

    template_name = "education_group_app/group/upsert/update.html"

    def get(self, request, *args, **kwargs):
        group_form = GroupUpdateForm(
            user=self.request.user,
            group_type=self.get_group_obj().type.name,
            initial=self._get_initial_group_form()
        )
        content_formset = ContentFormSet(
            initial=self._get_initial_content_formset(),
            form_kwargs=[
                {'parent_obj': self.get_group_obj(), 'child_obj': child}
                for child in self.get_children_objs()
            ],
        )
        return render(request, self.template_name, {
            "group": self.get_group_obj(),
            "group_form": group_form,
            "type_text": self.get_group_obj().type.value,
            "content_formset": content_formset,
            "tabs": self.get_tabs(),
            "cancel_url": self.get_cancel_url()
        })

    def post(self, request, *args, **kwargs):
        group_form = GroupUpdateForm(
            request.POST,
            user=self.request.user,
            group_type=self.get_group_obj().type.name,
            initial=self._get_initial_group_form()
        )
        content_formset = ContentFormSet(
            request.POST,
            initial=self._get_initial_content_formset(),
            form_kwargs=[
                {'parent_obj': self.get_group_obj(), 'child_obj': child}
                for child in self.get_children_objs()
            ],
        )

        if group_form.is_valid():
            group_id = self.__send_update_group_cmd(group_form)
        if content_formset.is_valid():
            link_updated = self.__send_multiple_update_link_cmd(content_formset)

        if self.is_all_forms_valid(group_form, content_formset):
            display_success_messages(request, self.get_success_msg(group_id), extra_tags='safe')
            if link_updated:
                display_success_messages(request, self.get_link_success_msg(link_updated), extra_tags='safe')
            return HttpResponseRedirect(self.get_success_url(group_id))
        else:
            msg = _("Error(s) in form: The modifications are not saved")
            display_error_messages(request, msg)

        return render(request, self.template_name, {
            "group": self.get_group_obj(),
            "group_form": group_form,
            "type_text": self.get_group_obj().type.value,
            "content_formset": content_formset,
            "tabs": self.get_tabs(),
            "cancel_url": self.get_cancel_url()
        })

    def __send_update_group_cmd(self, group_form: GroupUpdateForm) -> 'GroupIdentity':
        cmd_update = command.UpdateGroupCommand(
            code=self.kwargs['code'],
            year=self.kwargs['year'],
            abbreviated_title=group_form.cleaned_data['abbreviated_title'],
            title_fr=group_form.cleaned_data['title_fr'],
            title_en=group_form.cleaned_data['title_en'],
            credits=group_form.cleaned_data['credits'],
            constraint_type=group_form.cleaned_data['constraint_type'],
            min_constraint=group_form.cleaned_data['min_constraint'],
            max_constraint=group_form.cleaned_data['max_constraint'],
            management_entity_acronym=group_form.cleaned_data['management_entity'],
            teaching_campus_name=group_form.cleaned_data['teaching_campus']['name'] if
            group_form.cleaned_data['teaching_campus'] else None,
            organization_name=group_form.cleaned_data['teaching_campus']['organization_name'] if
            group_form.cleaned_data['teaching_campus'] else None,
            remark_fr=group_form.cleaned_data['remark_fr'],
            remark_en=group_form.cleaned_data['remark_en'],
        )
        try:
            return update_group_service.update_group(cmd_update)
        except CreditShouldBeGreaterOrEqualsThanZero as e:
            group_form.add_error('credits', e.message)
        except ContentConstraintTypeMissing as e:
            group_form.add_error('constraint_type', e.message)
        except (ContentConstraintMinimumMaximumMissing, ContentConstraintMaximumShouldBeGreaterOrEqualsThanMinimum) \
                as e:
            group_form.add_error('min_constraint', e.message)
            group_form.add_error('max_constraint', '')

    def __send_multiple_update_link_cmd(self, content_formset: ContentFormSet) -> List['Link']:
        forms_changed = [form for form in content_formset.forms if form.has_changed()]
        if not forms_changed:
            return []

        update_link_cmds = []
        for form in forms_changed:
            cmd_update_link = command_program_management.UpdateLinkCommand(
                child_node_code=form.child_obj.code if isinstance(form.child_obj, Group) else form.child_obj.acronym,
                child_node_year=form.child_obj.year,

                access_condition=form.cleaned_data.get('access_condition', False),
                is_mandatory=form.cleaned_data.get('is_mandatory', True),
                block=form.cleaned_data.get('block'),
                link_type=form.cleaned_data.get('link_type'),
                comment=form.cleaned_data.get('comment_fr'),
                comment_english=form.cleaned_data.get('comment_en'),
                relative_credits=form.cleaned_data.get('relative_credits'),
            )
            update_link_cmds.append(cmd_update_link)

        cmd_bulk = command_program_management.BulkUpdateLinkCommand(
            parent_node_code=self.kwargs['code'],
            parent_node_year=self.kwargs['year'],
            update_link_cmds=update_link_cmds
        )
        return update_link_service.bulk_update_links(cmd_bulk)

    def is_all_forms_valid(self, group_form, content_formset):
        return not any([group_form.errors, content_formset.total_error_count()])

    @functools.lru_cache()
    def get_group_obj(self) -> 'Group':
        try:
            get_cmd = command.GetGroupCommand(code=self.kwargs['code'], year=self.kwargs['year'])
            return get_group_service.get_group(get_cmd)
        except GroupNotFoundException:
            raise Http404

    @functools.lru_cache()
    def get_program_tree_obj(self) -> ProgramTree:
        get_pgrm_tree_cmd = command_program_management.GetProgramTree(
            code=self.kwargs['code'],
            year=self.kwargs['year']
        )
        return get_program_tree_service.get_program_tree(get_pgrm_tree_cmd)

    @functools.lru_cache()
    def get_children_objs(self) -> List[Union['Group', LearningUnitYear]]:
        children_objs = self.__get_children_group_obj() + self.__get_children_learning_unit_year_obj()
        return sorted(
            children_objs,
            key=lambda child_obj: next(
                order for order, node in enumerate(self.get_program_tree_obj().root_node.get_direct_children_as_nodes())
                if (isinstance(child_obj, Group) and node.code == child_obj.code) or
                   (isinstance(child_obj, LearningUnitYear) and node.code == child_obj.acronym)
            )
        )

    def __get_children_group_obj(self) -> List['Group']:
        get_group_cmds = [
            command.GetGroupCommand(code=node.code, year=node.year)
            for node in self.get_program_tree_obj().root_node.get_direct_children_as_nodes(
                ignore_children_from={NodeType.LEARNING_UNIT}
            )
        ]
        if get_group_cmds:
            return education_group.ddd.service.read.get_multiple_groups_service.get_multiple_groups(get_group_cmds)
        return []

    def __get_children_learning_unit_year_obj(self) -> List[LearningUnitYear]:
        get_learning_unit_cmds = [
            command_learning_unit_year.GetLearningUnitYearCommand(code=node.code, year=node.year)
            for node in self.get_program_tree_obj().root_node.get_direct_children_as_nodes(
                take_only={NodeType.LEARNING_UNIT}
            )
        ]
        if get_learning_unit_cmds:
            return get_multiple_learning_unit_years_service.get_multiple_learning_unit_years(get_learning_unit_cmds)
        return []

    def get_cancel_url(self) -> str:
        url = reverse('element_identification', kwargs={'code': self.kwargs['code'], 'year': self.kwargs['year']})
        if self.request.GET.get('path'):
            url += "?path={}".format(self.request.GET.get('path'))
        return url

    def get_success_msg(self, group_id: 'GroupIdentity') -> str:
        return _("Group <a href='%(link)s'> %(code)s (%(academic_year)s) </a> successfully updated.") % {
            "link": self.get_success_url(group_id),
            "code": group_id.code,
            "academic_year": display_as_academic_year(group_id.year),
        }

    def get_link_success_msg(self, link_updated: List['Link']) -> str:
        return "{} : <ul><li>{}</li></ul>".format(
            _("The following links has been updated"),
            "</li><li>".join([
                " - ".join([link.child.code, display_as_academic_year(link.child.year)])
                if link.child.is_learning_unit() else
                " - ".join([link.child.code, link.child.title, display_as_academic_year(link.child.year)])
                for link in link_updated
            ])
        )

    def get_success_url(self, group_id: 'GroupIdentity') -> str:
        url = reverse('element_identification', kwargs={'code': group_id.code, 'year': group_id.year})
        if self.request.GET.get('path'):
            url += "?path={}".format(self.request.GET.get('path'))
        return url

    def _get_initial_group_form(self) -> Dict:
        group_obj = self.get_group_obj()
        return {
            'code': group_obj.code,
            'academic_year': getattr(academic_year.find_academic_year_by_year(year=group_obj.year), 'pk', None),
            'abbreviated_title': group_obj.abbreviated_title,
            'title_fr': group_obj.titles.title_fr,
            'title_en': group_obj.titles.title_en,
            'credits': group_obj.credits,
            'constraint_type': group_obj.content_constraint.type.name if group_obj.content_constraint.type else None,
            'min_constraint': group_obj.content_constraint.minimum,
            'max_constraint': group_obj.content_constraint.maximum,
            'management_entity': entity_version.find(group_obj.management_entity.acronym),
            'teaching_campus': campus.find_by_name_and_organization_name(
                name=group_obj.teaching_campus.name,
                organization_name=group_obj.teaching_campus.university_name
            ),
            'remark_fr': group_obj.remark.text_fr,
            'remark_en': group_obj.remark.text_en
        }

    def _get_initial_content_formset(self) -> List[Dict]:
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

    def get_tabs(self) -> List:
        return [
            {
                "id": "identification",
                "text": _("Identification"),
                "active": not self.is_content_active_tab(),
                "display": True,
                "include_html": "education_group_app/group/upsert/identification_form.html"
            },
            {
                "id": "content",
                "text": _("Content"),
                "active": self.is_content_active_tab(),
                "display": bool(self.get_program_tree_obj().root_node.get_all_children()),
                "include_html": "education_group_app/group/upsert/content_form.html"
            }
        ]

    def is_content_active_tab(self):
        return self.request.GET.get('tab') == str(Tab.CONTENT.value)

    def get_permission_object(self) -> Union[GroupYear, None]:
        try:
            return GroupYear.objects.select_related(
                'academic_year', 'management_entity'
            ).get(partial_acronym=self.kwargs['code'], academic_year__year=self.kwargs['year'])
        except GroupYear.DoesNotExist:
            return None
