#############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#############################################################################

import functools
from typing import List, Dict, Optional

from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from rules.contrib.views import LoginRequiredMixin

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.models import entity_version, academic_year, campus
from base.views.common import display_success_messages, display_error_messages, check_formations_impacted_by_update
from education_group.ddd import command
from education_group.ddd.business_types import *
from education_group.ddd.domain.exception import GroupNotFoundException, ContentConstraintTypeMissing, \
    ContentConstraintMinimumMaximumMissing, ContentConstraintMaximumShouldBeGreaterOrEqualsThanMinimum, \
    CreditShouldBeGreaterOrEqualsThanZero, ContentConstraintMinimumInvalid, ContentConstraintMaximumInvalid
from education_group.ddd.domain.group import Group
from education_group.ddd.service.read import get_group_service
from education_group.ddd.service.write import update_group_service
from education_group.forms.group import GroupUpdateForm
from education_group.models.group_year import GroupYear
from education_group.templatetags.academic_year_display import display_as_academic_year
from osis_common.utils.models import get_object_or_none
from osis_role.contrib.views import PermissionRequiredMixin


class GroupUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    # PermissionRequiredMixin
    permission_required = 'base.change_group'
    raise_exception = True

    template_name = "education_group_app/group/upsert/update.html"

    def get(self, request, *args, **kwargs):
        group_form = GroupUpdateForm(
            user=self.request.user,
            group_type=self.get_group_obj().type.name,
            initial=self._get_initial_group_form()
        )
        return render(request, self.template_name, {
            "group": self.get_group_obj(),
            "group_form": group_form,
            "type_text": self.get_group_obj().type.value,
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

        if group_form.is_valid():
            group_id = self.__send_update_group_cmd(group_form)
            if group_form.is_valid():
                display_success_messages(request, self.get_success_msg(group_id), extra_tags='safe')
                check_formations_impacted_by_update(self.get_group_obj().code,
                                                    self.get_group_obj().year, request, self.get_group_obj().type)
                return HttpResponseRedirect(self.get_success_url(group_id))
        else:
            msg = _("Error(s) in form: The modifications are not saved")
            display_error_messages(request, msg)

        return render(request, self.template_name, {
            "group": self.get_group_obj(),
            "group_form": group_form,
            "type_text": self.get_group_obj().type.value,
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
            end_year=self.get_group_obj().end_year,
        )
        try:
            return update_group_service.update_group(cmd_update)
        except MultipleBusinessExceptions as multiple_exceptions:
            for e in multiple_exceptions.exceptions:
                if isinstance(e, CreditShouldBeGreaterOrEqualsThanZero):
                    group_form.add_error('credits', e.message)
                elif isinstance(e, ContentConstraintTypeMissing):
                    group_form.add_error('constraint_type', e.message)
                elif isinstance(e, ContentConstraintMinimumMaximumMissing) or \
                        isinstance(e, ContentConstraintMaximumShouldBeGreaterOrEqualsThanMinimum):
                    group_form.add_error('min_constraint', e.message)
                    group_form.add_error('max_constraint', '')
                elif isinstance(e, ContentConstraintMinimumInvalid):
                    group_form.add_error('min_constraint', e.message)
                elif isinstance(e, ContentConstraintMaximumInvalid):
                    group_form.add_error('max_constraint', e.message)
                else:
                    group_form.add_error(None, e.message)

    @functools.lru_cache()
    def get_group_obj(self) -> 'Group':
        try:
            get_cmd = command.GetGroupCommand(code=self.kwargs['code'], year=self.kwargs['year'])
            return get_group_service.get_group(get_cmd)
        except GroupNotFoundException:
            raise Http404

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

    def get_tabs(self) -> List:
        return [
            {
                "id": "identification",
                "text": _("Identification"),
                "active": True,
                "display": True,
                "include_html": "education_group_app/group/upsert/identification_form.html"
            }
        ]

    def get_permission_object(self) -> Optional[GroupYear]:
        return get_object_or_none(
            GroupYear.objects.select_related('academic_year', 'management_entity'),
            academic_year__year=self.kwargs['year'],
            partial_acronym=self.kwargs['code']
        )
