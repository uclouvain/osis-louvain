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

COORDINATOR = "COORDINATOR"
HOLDER = "HOLDER"
CO_HOLDER = "CO_HOLDER"
DEPUTY = "DEPUTY"
DEPUTY_AUTHORITY = "DEPUTY_AUTHORITY"
DEPUTY_SABBATICAL = "DEPUTY_SABBATICAL"
DEPUTY_TEMPORARY = "DEPUTY_TEMPORARY"
PROFESSOR = "PROFESSOR"  # To remove afterwards.
INTERNSHIP_SUPERVISOR = "INTERNSHIP_SUPERVISOR"
INTERNSHIP_CO_SUPERVISOR = "INTERNSHIP_CO_SUPERVISOR"


class Functions(ChoiceEnum):
    COORDINATOR = _("Coordinator")
    HOLDER = _("Holder")
    CO_HOLDER = _("Co-holder")
    DEPUTY = _("Deputy")
    DEPUTY_AUTHORITY = _("Deputy authority")
    DEPUTY_SABBATICAL = _("Deputy sabbatical")
    DEPUTY_TEMPORARY = _("Deputy temporary")
    PROFESSOR = _("Professor")
    INTERNSHIP_SUPERVISOR = _("Internship supervisor")
    INTERNSHIP_CO_SUPERVISOR = _("Internship co-supervisor")
