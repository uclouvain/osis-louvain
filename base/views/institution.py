##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.core import serializers
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, permission_required
from base import models as mdl
from base.enums import structure_type
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
def structures(request):
    return layout.render(request, "structures.html", {'init': "1",
                                                      'types': structure_type.TYPES})


@login_required
def structures_search(request):
    struct_type = None
    if request.GET['type_choices']:
        struct_type = request.GET['type_choices']  #otherwise type is a blank
    entities = mdl.structure.search(acronym=request.GET['acronym'],
                                    title=request.GET['title'],
                                    type=struct_type)

    return layout.render(request, "structures.html", {'entities': entities,
                                                      'types': structure_type.TYPES})


@login_required
def structure_read(request, structure_id):
    structure = mdl.structure.find_by_id(structure_id)
    offers_years = mdl.offer_year.find_by_structure(structure)
    return layout.render(request, "structure.html", {'structure': structure,
                                                     'offers_years': offers_years})

@login_required
def structure_diagram(request, parent_id):
    structure = mdl.structure.find_by_id(parent_id)
    return layout.render(request, "structure_organogram.html", {'structure': structure,
                                                                'structure_as_json': json.dumps(structure.serializable_object())})

@login_required
def structure_address(request, structure_id):
    structure = mdl.structure.find_by_id(structure_id)
    struct_address = mdl.structure_address.find_structure_address(structure)
    if struct_address:
        data = json.dumps({'entity': u'%s - %s' % (structure.acronym, structure.title),
                           'location': struct_address.location,
                           'city': struct_address.city,
                           'postal_code': struct_address.postal_code,
                           'country': struct_address.country.id,
                           'phone': struct_address.phone,
                           'fax': struct_address.fax,
                           'email': struct_address.email})
    else:
        data = json.dumps({'entity': u'%s - %s' % (structure.acronym, structure.title)})
    return HttpResponse(data, content_type='application/json')


@login_required
def academic_actors(request):
    return layout.render(request, "academic_actors.html", {})
