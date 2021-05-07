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
from base.business.education_groups.general_information_sections import can_postpone_general_information
from cms.contrib.views import UpdateCmsView
from cms.enums import entity_name
from education_group.models.group_year import GroupYear
from education_group.views.group.common_read import Tab, GroupRead


class GroupUpdateGeneralInformation(GroupRead, UpdateCmsView):
    active_tab = Tab.GENERAL_INFO
    permission_required = 'base.change_group_pedagogyinformation'

    def get_success_url(self):
        return ""

    def get_entity(self):
        return entity_name.GROUP_YEAR

    def get_reference(self):
        return self.get_group_year().id

    def get_references(self):
        return GroupYear.objects.filter(
            group=self.get_group_year().group,
            academic_year__year__gte=self.get_group_year().academic_year.year
        ).values_list(
            'id',
            flat=True
        )

    def can_postpone(self) -> bool:
        return can_postpone_general_information(self.get_group_year())
