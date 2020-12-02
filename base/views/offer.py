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
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from base import models as mdl
from base.models.academic_year import AcademicYear


@login_required
@permission_required('base.can_access_offer', raise_exception=True)
def offers(request):
    academic_yr = None
    academic_years = AcademicYear.objects.all()

    academic_year_calendar = mdl.academic_year.current_academic_year()

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

    offer_years = mdl.offer_year.search(entity=entity, academic_yr=academic_yr, acronym=acronym) \
        .select_related("entity_management", "academic_year")

    return render(request, "offers.html", {'academic_year': academic_yr,
                                           'entity_acronym': entity,
                                           'code': acronym,
                                           'academic_years': academic_years,
                                           'offer_years': offer_years,
                                           'init': "0"})
