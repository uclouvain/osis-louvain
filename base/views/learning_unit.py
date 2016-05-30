##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
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
from base import models as mdl
from . import layout


def learning_units(request):
    academic_yr = None
    code = ""

    academic_years = mdl.academic_year.find_academic_years()
    academic_yr_calendar = mdl.academic_year.current_academic_year()

    if academic_yr_calendar:
        academic_yr = academic_yr_calendar.id
    return layout.render(request, "learning_units.html", {'academic_year': academic_yr,
                                                          'code': code,
                                                          'academic_years': academic_years,
                                                          'learning_units': [],
                                                          'init': "1"})


def learning_units_search(request):
    """
    Learning units search
    """
    # criteria
    academic_year = request.GET['academic_year']
    code = request.GET['code']
    if academic_year is None:
        academic_year_calendar = mdl.academic_year.current_academic_year()
        if academic_year_calendar:
            academic_year = academic_year_calendar.id

    learning_unts = mdl.learning_unit_year.search(academic_year_id=academic_year,acronym=code)
    academic_years = mdl.academic_year.find_academic_years()

    return layout.render(request, "learning_units.html", {'academic_year': int(academic_year),
                                                          'code': code,
                                                          'academic_years': academic_years,
                                                          'learning_units': learning_unts,
                                                          'init': "0"})


def learning_unit_read(request, learning_unit_year_id):
    learning_unit_year = mdl.learning_unit_year.find_by_id(learning_unit_year_id)
    attributions = mdl.attribution.search(learning_unit_id=learning_unit_year.learning_unit.id)

    return layout.render(request, "learning_unit.html", {'learning_unit_year': learning_unit_year,
                                                         'attributions': attributions})
