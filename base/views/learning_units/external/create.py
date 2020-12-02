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
from django.shortcuts import get_object_or_404, render
from waffle.decorators import waffle_flag

from base.forms.learning_unit.learning_unit_postponement import LearningUnitPostponementForm
from base.models.academic_year import AcademicYear
from base.models.person import Person
from base.views.learning_units.create import _save_and_redirect


@login_required
@waffle_flag("learning_unit_external_create")
@permission_required('base.add_externallearningunityear', raise_exception=True)
def get_external_learning_unit_creation_form(request, academic_year):
    person = get_object_or_404(Person, user=request.user)

    if request.POST.get('academic_year'):
        academic_year = request.POST.get('academic_year')

    academic_year = get_object_or_404(AcademicYear, pk=academic_year)

    postponement_form = LearningUnitPostponementForm(
        person=person,
        start_postponement=academic_year,
        data=request.POST or None,
        external=True,
    )

    if postponement_form.is_valid():
        return _save_and_redirect(postponement_form, request)

    return render(request, "learning_unit/external/create.html", postponement_form.get_context())
