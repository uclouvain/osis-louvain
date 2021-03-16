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
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from base.models import session_exam_calendar
from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.entity_version import EntityVersion
from base.models.enums.education_group_categories import Categories


@login_required
@permission_required('base.can_access_offer', raise_exception=True)
def offers(request):
    academic_yr = None
    academic_years = AcademicYear.objects.all()

    academic_year_calendar = session_exam_calendar.current_opened_academic_year()

    if academic_year_calendar:
        academic_yr = academic_year_calendar.id
    return render(request, "offers.html", {'academic_year': academic_yr,
                                           'academic_years': academic_years,
                                           'offers': [],
                                           'init': "1"})


@login_required
@permission_required('base.can_access_offer', raise_exception=True)
def offers_search(request):
    entity = request.GET['entity_acronym']

    academic_yr = None
    if request.GET.get('academic_year', None):
        academic_yr = int(request.GET['academic_year'])
    acronym = request.GET['code']

    academic_years = AcademicYear.objects.all()

    cte = EntityVersion.objects.with_parents(acronym__icontains=entity)
    entity_ids_with_children = cte.queryset().with_cte(cte).values_list('entity_id').distinct()

    offer_years = EducationGroupYear.objects.filter(
        management_entity_id__in=entity_ids_with_children,
        academic_year=academic_yr,
        acronym__icontains=acronym,
        education_group_type__category=Categories.TRAINING.name,
    ).exclude(
        acronym__icontains="common-"
    ).select_related(
        'education_group',
        'management_entity',
        'academic_year',
    ).order_by('acronym')

    return render(request, "offers.html", {'academic_year': academic_yr,
                                           'entity_acronym': entity,
                                           'code': acronym,
                                           'academic_years': academic_years,
                                           'educ_group_years': offer_years,
                                           'init': "0"})
