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

from django.contrib.auth.decorators import login_required, permission_required
from base import models as mdl
from base.models.enums import structure_type, entity_type
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
    return layout.render(request, "entities.html", {'init': "1",
                                                    'types': entity_type.ENTITY_TYPES})


@login_required
def entities_search(request):
    entities_version = mdl.entity_version.search_entities(acronym=request.GET.get('acronym'),
                                                          title=request.GET.get('title'),
                                                          type=request.GET.get('type_choices'))
    return layout.render(request, "entities.html", {'entities_version': entities_version,
                                                    'types': structure_type.TYPES})


@login_required
def entity_read(request, entity_version_id):
    entity_version = mdl.entity_version.find_by_id(entity_version_id)
    entity_parent = entity_version.get_parent_version()
    if entity_parent:
        return layout.render(request, "entity.html", {'entity_version': entity_version,
                                                      'entity_parent': entity_parent})
    else:
        return layout.render(request, "entity.html", {'entity_version': entity_version})


@login_required
def entity_diagram(request, entity_version_id):
    entity_version = mdl.entity_version.find_by_id(entity_version_id)
    return layout.render(request, "entity_organogram.html", {'entity_version': entity_version,
                                                             'entities_version_as_json': json.dumps(entity_version.serializable_object())})
