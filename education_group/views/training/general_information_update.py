#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.utils.translation import gettext_lazy as _

from base.business.education_groups.general_information_sections import can_postpone_general_information, \
    CMS_LABEL_PROGRAM_AIM, CMS_LABEL_ADDITIONAL_INFORMATION
from base.models.education_group_year import EducationGroupYear
from cms.contrib.views import UpdateCmsView
from cms.enums import entity_name
from education_group.views.training.common_read import TrainingRead, Tab


class TrainingUpdateGeneralInformation(TrainingRead, UpdateCmsView):
    active_tab = Tab.GENERAL_INFO
    permission_required = 'base.change_pedagogyinformation'

    def get_success_url(self):
        return ""

    def get_entity(self):
        return entity_name.OFFER_YEAR

    def get_reference(self):
        return self.education_group_version.offer_id

    def get_references(self):
        return EducationGroupYear.objects.filter(
            education_group=self.education_group_version.offer.education_group,
            academic_year__year__gte=self.education_group_version.offer.academic_year.year
        ).values_list(
            'id',
            flat=True
        )

    def get_success_message(self, to_postpone: bool):
        if self.label == CMS_LABEL_PROGRAM_AIM:
            return _("The program aim has been updated (with postpone)") if to_postpone\
                else _("The program aim has been updated (without postpone)")
        elif self.label == CMS_LABEL_ADDITIONAL_INFORMATION:
            return _("The additional informations has been updated (with postpone)") if to_postpone \
                else _("The additional informations has been updated (without postpone)")
        return super().get_success_message(to_postpone)

    def get_title(self) -> str:
        if self.label == CMS_LABEL_PROGRAM_AIM:
            return _("the program aims")
        elif self.label == CMS_LABEL_ADDITIONAL_INFORMATION:
            return _("additional informations")
        return super().get_title()

    def can_postpone(self) -> bool:
        return can_postpone_general_information(self.education_group_version.offer)
