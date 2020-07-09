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
from django.utils.translation import gettext_lazy as _, pgettext_lazy

MAIN = "MAIN"
ACADEMIC_PARTNER = "ACADEMIC_PARTNER"
EMBASSY = "EMBASSY"
RESEARCH_CENTER = "RESEARCH_CENTER"
ENTERPRISE = "ENTERPRISE"
HOSPITAL = "HOSPITAL"
NGO = "NGO"
OTHER = "OTHER"

ORGANIZATION_TYPE = (
    (MAIN, pgettext_lazy("female", "Main")),
    (ACADEMIC_PARTNER, _("Academic partner")),
    (EMBASSY, _("Embassy")),
    (RESEARCH_CENTER, _("Research center")),
    (ENTERPRISE, _("Enterprise")),
    (HOSPITAL, _("Hospital")),
    (NGO, _("Non-governmental organization")),
)
