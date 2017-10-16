##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required, permission_required
from base import models as mdl

from base.forms.education_groups import EducationGroupFilter, MAX_RECORDS
from base.models.enums import education_group_categories

from . import layout


@login_required
@permission_required('base.can_access_offer', raise_exception=True)
def education_groups(request):
    if request.GET:
        form = EducationGroupFilter(request.GET)
    else:
        current_academic_year = mdl.academic_year.current_academic_year()
        form = EducationGroupFilter(initial={'academic_year': current_academic_year,
                                             'category': education_group_categories.TRAINING})

    object_list = None
    if form.is_valid():
        object_list = form.get_object_list()
        if not _check_if_display_message(request, object_list):
            object_list = None

    context = {
        'form': form,
        'object_list': object_list,
        'experimental_phase': True
    }
    return layout.render(request, "education_groups.html", context)


def _check_if_display_message(request, an_education_groups):
    if not an_education_groups:
        messages.add_message(request, messages.WARNING, _('no_result'))
    elif len(an_education_groups) > MAX_RECORDS:
        messages.add_message(request, messages.WARNING, _('too_many_results'))
        return False
    return True


@login_required
@permission_required('base.can_access_offer', raise_exception=True)
def education_group_read(request, education_group_year_id):
    return _education_group_identification_tab(request, education_group_year_id)


def _education_group_identification_tab(request, education_group_year_id):
    education_group_year = mdl.education_group_year.find_by_id(education_group_year_id)

    coorganizations = []
    for coorganization in mdl.education_group_organization.search(education_group_year):
        coorganizations.append({'coorganization':coorganization,
                                'address' : mdl.organization_address.find_by_organization(coorganization.organization).first()})

    return layout.render(request, "education_group/tab_identification.html", locals())


def get_education_group_years(academic_yr, acronym, entity):
    if entity:
        education_group_year_entitys = []
        education_group_years = mdl.education_group_year.search(academic_yr=academic_yr, acronym=acronym)
        for education_group_yr in education_group_years:
            if education_group_yr.management_entity and\
                            education_group_yr.management_entity.acronym.upper() == entity.upper():
                education_group_year_entitys.append(education_group_yr)
        return education_group_year_entitys
    else:
        return mdl.education_group_year.search(academic_yr=academic_yr, acronym=acronym)


@login_required
@permission_required('base.can_access_offer', raise_exception=True)
def education_group_diplomas(request, education_group_year_id):
    return _education_group_diplomas_tab(request, education_group_year_id)


def _education_group_diplomas_tab(request, education_group_year_id):
    education_group_year = mdl.education_group_year.find_by_id(education_group_year_id)
    return layout.render(request, "education_group/tab_diplomas.html", locals())
