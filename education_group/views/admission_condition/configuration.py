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
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from base.models.education_group_year import EducationGroupYear
from base.utils.cache_keys import get_tab_lang_keys, CACHE_TIMEOUT
from education_group.ddd.domain.service.identity_search import TrainingIdentitySearch
from education_group.views.proxy.read import Tab


@login_required
def change_language(request, year: int, code: str, language: str):
    education_group_year = get_object_or_404(
        EducationGroupYear,
        partial_acronym=code,
        academic_year__year=year
    )
    cache.set(get_tab_lang_keys(request.user), language, timeout=CACHE_TIMEOUT)
    training_identity = TrainingIdentitySearch().get_from_education_group_year_id(education_group_year.id)
    return redirect(reverse(
        'education_group_read_proxy',
        args=[year, training_identity.acronym]
    ) + '?tab={}'.format(Tab.ADMISSION_CONDITION))
