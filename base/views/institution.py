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
import operator
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from base import models as mdl
from django.utils.translation import ugettext_lazy as _
from functools import reduce
from django.db import models


@login_required
def institution(request):
    return render(request, "institution.html", {'section': 'institution'})


@login_required
def structures(request):
    return render(request, "structures.html", {'init': "1",
                                               'types': mdl.structure.ENTITY_TYPE})


@login_required
def structures_search(request):
    structure_type = None
    if request.GET['type_choices']:
        structure_type = request.GET['type_choices'] #otherwise type is a blank
    entities = mdl.structure.search(acronym=request.GET['acronym'],
                                    title=request.GET['title'],
                                    type=structure_type)

    return render(request, "structures.html", {'entities': entities,
                                               'types': mdl.structure.ENTITY_TYPE})


@login_required
def structure_read(request, structure_id):
    structure = mdl.structure.find_by_id(structure_id)
    offers_years = mdl.offer_year.find_offer_years_by_structure(structure)
    return render(request, "structure.html", {'structure': structure,
                                              'offers_years': offers_years})


def structure_read_by_acronym(request, name):
    structure = mdl.structure.find_by_acronym(name)
    return render(request, "structure.html", {'structure': structure})


def structure_diagram(request, organization_id):
    organization = mdl.organization.find_by_id(organization_id)
    structure = organization.find_structure()
    tags = organization.find_structure_tree()
    data = json.dumps(tags)
    return render(request, "structure_organogram.html", {'structure': structure,
                                                         'data': data})


def structure_diagram_by_parent(request, parent_id):
    structure = mdl.structure.find_by_id(parent_id)
    tags = mdl.structure.find_structure_hierarchy(structure)
    data = json.dumps(tags)
    return render(request, "structure_organogram.html", {'structure': structure,
                                                         'data': data})
