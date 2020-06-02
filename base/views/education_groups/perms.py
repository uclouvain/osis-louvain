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
from django.contrib.auth.mixins import AccessMixin, ImproperlyConfigured
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from waffle.models import Flag

from base.models.education_group_year import EducationGroupYear
from osis_role.errors import get_permission_error


def can_change_education_group(user, education_group):
    perm = 'base.change_link_data'
    if not user.has_perm(perm, education_group):
        raise PermissionDenied(get_permission_error(user, perm))
    return True


def can_change_general_information(view_func):
    def f_can_change_general_information(request, *args, **kwargs):
        education_group_year = get_object_or_404(EducationGroupYear, pk=kwargs['education_group_year_id'])
        perm_name = 'base.change_commonpedagogyinformation' if education_group_year.is_common else \
            'base.change_pedagogyinformation'
        if not request.user.has_perm(perm_name, education_group_year):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return f_can_change_general_information


def can_change_admission_condition(view_func):
    def f_can_change_admission_condition(request, *args, **kwargs):
        education_group_year = get_object_or_404(EducationGroupYear, pk=kwargs['education_group_year_id'])
        perm_name = 'base.change_commonadmissioncondition' if education_group_year.is_common else \
            'base.change_admissioncondition'
        if not request.user.has_perm(perm_name, education_group_year):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return f_can_change_admission_condition


class FlagNotAuthorized(AccessMixin):

    flag_not_authorized = None

    def get_flag_not_authorized(self):
        if self.flag_not_authorized:
            if isinstance(self.flag_not_authorized, str):
                return Flag.objects.filter(name=self.flag_not_authorized).exists()
            else:
                raise ImproperlyConfigured(
                    '{0} flag_not_authorized is not correctly defined'.format(self.__class__.__name__)
                )

            return False

    def has_flag(self):
        return self.get_flag_not_authorized()

    def dispatch(self, request, *args, **kwargs):
        if self.has_flag():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
