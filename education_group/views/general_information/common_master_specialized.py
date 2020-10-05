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
from enum import Enum

from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView
from django.utils.translation import gettext_lazy as _

from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import TrainingType
from education_group.views.general_information.update_common_condition import UpdateCommonCondition
from osis_role.contrib.views import PermissionRequiredMixin


class Tab(Enum):
    ADMISSION_CONDITION = 0


class CommonMasterSpecializedAdmissionCondition(PermissionRequiredMixin, TemplateView):
    # PermissionRequiredMixin
    permission_required = 'base.view_educationgroup'
    raise_exception = True
    template_name = "education_group_app/general_information/common_master_specialized.html"

    def get_context_data(self, **kwargs):
        object = self.get_object()
        return {
            **super().get_context_data(**kwargs),
            "object": object,
            "admission_condition": object.admissioncondition,
            "tab_urls": self.get_tab_urls(),
            "can_edit_information": self.request.user.has_perm(
                "base.change_commonadmissioncondition", self.get_object()
            ),
            "update_text_url": self.get_update_text_url(),
            "publish_url": self.get_publish_url()
        }

    def get_tab_urls(self):
        return {
            Tab.ADMISSION_CONDITION: {
                'text': _('Conditions'),
                'active': True,
                'display': True,
                'url': reverse('common_master_specialized_admission_condition', kwargs={'year': self.kwargs['year']})
            }
        }

    def get_object(self) -> EducationGroupYear:
        try:
            return EducationGroupYear.objects.look_for_common(
                academic_year__year=self.kwargs['year'],
                education_group_type__name=TrainingType.MASTER_MC.name,
                admissioncondition__isnull=False
            ).select_related('admissioncondition').get()
        except EducationGroupYear.DoesNotExist:
            raise Http404

    def get_publish_url(self):
        return reverse('publish_common_master_specialized_admission_condition', kwargs={'year': self.kwargs['year']})

    def get_update_text_url(self) -> str:
        return reverse(
            'update_common_master_specialized_admission_condition',
            kwargs={
                'year': self.kwargs['year'],
            }
        )


class UpdateCommonMasterSpecializedAdmissionCondition(UpdateCommonCondition):
    def get_admission_condition(self):
        common = EducationGroupYear.objects.look_for_common(
            academic_year__year=self.kwargs['year'],
            education_group_type__name=TrainingType.MASTER_MC.name,
            admissioncondition__isnull=False
        ).select_related('admissioncondition').get()
        return common.admissioncondition

    def get_success_url(self) -> str:
        return reverse('common_master_specialized_admission_condition', kwargs={'year': self.kwargs['year']})
