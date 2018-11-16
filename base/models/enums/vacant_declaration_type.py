##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.translation import ugettext_lazy as _

from base.models.utils.utils import ChoiceEnum

RESEVED_FOR_INTERNS = "RESEVED_FOR_INTERNS"
OPEN_FOR_EXTERNS = "OPEN_FOR_EXTERNS"
EXCEPTIONAL_PROCEDURE = "EXCEPTIONAL_PROCEDURE"
VACANT_NOT_PUBLISH = "VACANT_NOT_PUBLISH"
DO_NOT_ASSIGN = "DO_NOT_ASSIGN"

DECLARATION_TYPE = (
    (RESEVED_FOR_INTERNS, _("Reserved for interns")),
    (OPEN_FOR_EXTERNS, _("Open for externs")),
    (EXCEPTIONAL_PROCEDURE, _("Exceptional procedure")),
    (VACANT_NOT_PUBLISH, _("Vacant not publish")),
    (DO_NOT_ASSIGN, _("Do not assign"))
)


class VacantDeclarationType(ChoiceEnum):
    RESEVED_FOR_INTERNS = "RESEVED_FOR_INTERNS"
    OPEN_FOR_EXTERNS = "OPEN_FOR_EXTERNS"
    EXCEPTIONAL_PROCEDURE = "EXCEPTIONAL_PROCEDURE"
    VACANT_NOT_PUBLISH = "VACANT_NOT_PUBLISH"
    DO_NOT_ASSIGN = "DO_NOT_ASSIGN"
