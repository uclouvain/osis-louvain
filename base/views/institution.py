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
import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from base import models as mdl
from base.business import event_perms
from base.business.institution import find_summary_course_submission_dates_for_entity_version
from base.business.perms import view_academicactors
from base.forms.entity import EntityVersionFilter
from base.models import entity_version as entity_version_mdl
from base.models.entity_version import EntityVersion
from base.views.common import paginate_queryset

logger = logging.getLogger(settings.DEFAULT_LOGGER)


@login_required
@permission_required('base.is_institution_administrator', raise_exception=True)
def institution(request):
    context = {
        'section': 'institution',
        'view_academicactors': view_academicactors(request.user)
    }
    return render(request, "institution.html", context)


@login_required
@permission_required('base.can_access_mandate', raise_exception=True)
def mandates(request):
    return render(request, "mandates.html", {'section': 'mandates'})


@login_required
@user_passes_test(view_academicactors)
def academic_actors(request):
    return render(request, "academic_actors.html", {})


@login_required
def entities_search(request):
    order_by = request.GET.get('order_by', 'acronym')
    filter = EntityVersionFilter(request.GET or None)

    entities_version_list = filter.qs.select_related('entity__organization').order_by(order_by)
    entities_version_list = paginate_queryset(entities_version_list, request.GET)

    return render(request, "entities.html", {'entities_version': entities_version_list, 'form': filter.form})


@login_required
def entity_read(request, entity_version_id):
    entity_version = get_object_or_404(EntityVersion, id=entity_version_id)
    entity_parent = entity_version.get_parent_version()
    descendants = entity_version.descendants

    event_perm = event_perms.EventPermSummaryCourseSubmission()
    if event_perm.is_open():
        data_year = event_perm.get_academic_years().get()
    else:
        data_year = event_perm.get_previous_opened_calendar().data_year
    calendar_summary_course_submission = find_summary_course_submission_dates_for_entity_version(
        entity_version=entity_version,
        ac_year=data_year
    )

    context = {
        'entity_version': entity_version,
        'entity_parent': entity_parent,
        'descendants': descendants,
        'calendar_summary_course_submission': calendar_summary_course_submission
    }
    return render(request, "entity/identification.html", context)


@login_required
def entities_version(request, entity_version_id):
    entity_version = mdl.entity_version.find_by_id(entity_version_id)
    entity_parent = entity_version.get_parent_version()
    entities_version = mdl.entity_version.search(entity=entity_version.entity) \
                                         .order_by('-start_date')
    return render(request, "entity/versions.html", locals())


@login_required
def entity_diagram(request, entity_version_id):
    entity_version = mdl.entity_version.find_by_id(entity_version_id)
    entities_version_as_json = json.dumps(entity_version.get_organigram_data())

    return render(
        request, "entity/organogram.html",
        {
            "entity_version": entity_version,
            "entities_version_as_json": entities_version_as_json,
        }
    )


@login_required
def get_entity_address(request, entity_version_id):
    version = entity_version_mdl.find_by_id(entity_version_id)
    entity = version.entity
    response = {
        'entity_version_exists_now': version.exists_now(),
        'recipient': '{} - {}'.format(version.acronym, version.title),
        'address': {}
    }
    if entity and entity.has_address():
        response['address'] = {
            'location': entity.location,
            'postal_code': entity.postal_code,
            'city': entity.city,
            'country_id': entity.country_id,
            'phone': entity.phone,
            'fax': entity.fax,
        }
    return JsonResponse(response)
