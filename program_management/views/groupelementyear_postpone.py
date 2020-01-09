##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.http import JsonResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from base.views.common import display_success_messages, display_warning_messages, display_error_messages
from base.views.education_groups.detail import EducationGroupGenericDetailView
from base.views.education_groups.perms import can_change_education_group
from base.views.mixins import RulesRequiredMixin, AjaxTemplateMixin
from program_management.business.group_element_years.postponement import PostponeContent, NotPostponeError


class PostponeGroupElementYearView(RulesRequiredMixin, AjaxTemplateMixin, EducationGroupGenericDetailView):
    template_name = "group_element_year/confirm_postpone_content_inner.html"

    # FlagMixin
    flag = "education_group_update"

    # RulesRequiredMixin
    rules = [can_change_education_group]

    with_tree = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["warning_message"] = _("Are you sure you want to postpone the content in %(root)s?") % {
            "root": self.root
        }
        return context

    def post(self, request, **kwargs):
        try:
            postponer = PostponeContent(self.root.previous_year(), request.user.person)
            postponer.postpone()
            success = _("%(count_elements)s OF(s) and %(count_links)s link(s) have been postponed with success.") % {
                'count_elements': postponer.number_elements_created,
                'count_links': postponer.number_links_created
            }
            display_success_messages(request, success)
            display_warning_messages(request, postponer.warnings)

        except NotPostponeError as e:
            display_error_messages(request, str(e))

        return JsonResponse({
            'success_url': reverse(
                "education_group_read",
                args=[
                    kwargs["root_id"],
                    kwargs["education_group_year_id"]
                ]
            )})
