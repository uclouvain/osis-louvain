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

from base.business.education_groups import perms as business_perms
from base.models.education_group_type import EducationGroupType
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_categories import Categories
from base.models.person import Person


def can_create_education_group(view_func):
    def f_can_create_education_group(request, *args, **kwargs):
        pers = get_object_or_404(Person, user=request.user)
        category = kwargs['category']  # Mandatory kwargs

        parent_id = kwargs.get("parent_id")
        parent = get_object_or_404(EducationGroupYear, pk=parent_id) if parent_id else None
        education_group_type_pk = kwargs.get("education_group_type_pk")
        education_group_type = get_object_or_404(EducationGroupType, pk=education_group_type_pk)
        if not business_perms._is_eligible_to_add_education_group(pers, parent, Categories[category],
                                                                  education_group_type=education_group_type,
                                                                  raise_exception=True):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return f_can_create_education_group


def can_change_education_group(user, education_group):
    pers = get_object_or_404(Person, user=user)
    if not business_perms.is_eligible_to_change_education_group(pers, education_group, raise_exception=True):
        raise PermissionDenied
    return True


def can_change_general_information(view_func):
    def f_can_change_general_information(request, *args, **kwargs):
        person = get_object_or_404(Person, user=request.user)
        education_group_year = get_object_or_404(EducationGroupYear, pk=kwargs['education_group_year_id'])
        if not business_perms.is_eligible_to_edit_general_information(
                person,
                education_group_year,
                raise_exception=True
        ):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return f_can_change_general_information


def can_change_admission_condition(view_func):
    def f_can_change_admission_condition(request, *args, **kwargs):
        person = get_object_or_404(Person, user=request.user)
        education_group_year = get_object_or_404(EducationGroupYear, pk=kwargs['education_group_year_id'])
        if not business_perms.is_eligible_to_edit_admission_condition(
                person,
                education_group_year,
                raise_exception=True
        ):
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
