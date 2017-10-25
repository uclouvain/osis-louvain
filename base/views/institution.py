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
import json
import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from base import models as mdl
from base.models import entity_version as entity_version_mdl
from base.models.enums import entity_type
from . import layout


@login_required
@permission_required('base.is_institution_administrator', raise_exception=True)
def institution(request):
    return layout.render(request, "institution.html", {'section': 'institution'})


@login_required
@permission_required('base.can_access_mandate', raise_exception=True)
def mandates(request):
    return layout.render(request, "mandates.html", {'section': 'mandates'})


@login_required
def academic_actors(request):
    return layout.render(request, "academic_actors.html", {})


@login_required
def entities(request):
    return layout.render(request, "entities.html", {'init': "0",
                                                    'types': entity_type.ENTITY_TYPES})


@login_required
def entities_search(request):
    entities_version = mdl.entity_version.search_entities(acronym=request.GET.get('acronym'),
                                                          title=request.GET.get('title'),
                                                          type=request.GET.get('type_choices'),
                                                          with_entity=True)
    return layout.render(request, "entities.html", {'entities_version': entities_version,
                                                    'init': "1",
                                                    'types': entity_type.ENTITY_TYPES})


@login_required
def entity_read(request, entity_version_id):
    entity_version = mdl.entity_version.find_by_id(entity_version_id)
    entity_parent = entity_version.get_parent_version()
    descendants = entity_version.descendants
    return layout.render(request, "entity/identification.html", locals())


@login_required
def entities_version(request, entity_version_id):
    entity_version = mdl.entity_version.find_by_id(entity_version_id)
    entity_parent = entity_version.get_parent_version()
    entities_version = mdl.entity_version.search(entity=entity_version.entity)\
                                         .order_by('-start_date')
    return layout.render(request, "entity/versions.html", locals())


@login_required
def entity_diagram(request, entity_version_id):
    entity_version = mdl.entity_version.find_by_id(entity_version_id)
    entities_version_as_json = json.dumps(entity_version.get_organogram_data(level=0))
    return layout.render(request, "entity/organogram.html", locals())


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
        response['address'] = {'location': entity.location,
                               'postal_code': entity.postal_code,
                               'city': entity.city,
                               'country_id': entity.country_id,
                               'phone': entity.phone,
                               'fax': entity.fax,
                               }
    return JsonResponse(response)
