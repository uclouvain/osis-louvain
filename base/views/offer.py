##############################################################################
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

from base.models import academic_year
from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.entity_version import EntityVersion
from base.models.enums.education_group_categories import Categories


@login_required
@permission_required('base.can_access_offer', raise_exception=True)
def offers(request):
    return render(request, "offers.html", {'offers': [],
                                           'init': "1"})


@login_required
@permission_required('base.can_access_offer', raise_exception=True)
def offers_search(request):
    entity = request.GET['entity_acronym']

    acronym = request.GET['code']

    cte = EntityVersion.objects.with_parents(acronym__icontains=entity)
    entity_ids_with_children = cte.queryset().with_cte(cte).values_list('entity_id').distinct()

    offer_years = EducationGroupYear.objects.filter(
        management_entity_id__in=entity_ids_with_children,
        acronym__icontains=acronym,
        education_group_type__category=Categories.TRAINING.name,
    ).exclude(
        acronym__icontains="common-"
    ).select_related(
        'education_group',
        'management_entity',
        'academic_year',
    ).distinct('education_group').order_by('education_group', 'acronym')

    return render(request, "offers.html", {'entity_acronym': entity,
                                           'code': acronym,
                                           'educ_group_years': offer_years,
                                           'init': "0"})
