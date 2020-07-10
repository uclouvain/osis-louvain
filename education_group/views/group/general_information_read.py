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
from django.shortcuts import redirect
from django.urls import reverse

from education_group.views import serializers
from education_group.views.group.common_read import Tab, GroupRead


class GroupReadGeneralInformation(GroupRead):
    template_name = "education_group_app/group/general_informations_read.html"
    active_tab = Tab.GENERAL_INFO

    def get(self, request, *args, **kwargs):
        result = super().get(request, *args, **kwargs)
        if not self.have_general_information_tab():
            return redirect(reverse('group_identification', kwargs=self.kwargs) + "?path={}".format(self.get_path()))
        return result

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "sections": self.get_sections(),
            "update_label_url": self.get_update_label_url(),
            "publish_url": self.get_publish_url(),
            "can_edit_information": self.request.user.has_perm("base.change_pedagogyinformation", self.get_group_year())
        }

    def get_sections(self):
        return serializers.general_information.get_sections(self.get_object(), self.request.LANGUAGE_CODE)

    def get_update_label_url(self):
        node = self.get_object()
        return reverse('group_general_information_update', args=[node.year, node.code]) + "?path={}".format(
            self.get_path())

    def get_publish_url(self):
        node = self.get_object()
        return reverse('publish_general_information', args=[node.year, node.code]) + "?path={}".format(self.get_path())
