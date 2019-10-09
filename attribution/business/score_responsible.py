##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.core.exceptions import PermissionDenied

from assessments.business import scores_responsible
from attribution import models as mdl_attr
from base.models.learning_unit_year import LearningUnitYear


def get_learning_unit_year_managed_by_user_from_id(user, learning_unit_year_id):
    qs = LearningUnitYear.objects.filter(pk=learning_unit_year_id)
    if scores_responsible.filter_learning_unit_year_according_person(qs, user.person).exists():
        return qs.get()
    raise PermissionDenied("User is not an entity manager of the requirement entity of the learning unit")


def get_attributions_data(user, learning_unit_year_id, responsibles_order):
    a_learning_unit_year = get_learning_unit_year_managed_by_user_from_id(user, learning_unit_year_id)
    return {
        'learning_unit_year': a_learning_unit_year,
        'attributions': mdl_attr.attribution.find_all_responsible_by_learning_unit_year(
            a_learning_unit_year, responsibles_order=responsibles_order),
        'academic_year': a_learning_unit_year.academic_year
    }
