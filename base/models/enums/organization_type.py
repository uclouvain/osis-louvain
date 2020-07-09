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
INDUSTRIAL_PARTNER = "INDUSTRIAL_PARTNER"
SERVICE_PARTNER = "SERVICE_PARTNER"
COMMERCE_PARTNER = "COMMERCE_PARTNER"
PUBLIC_PARTNER = "PUBLIC_PARTNER"

ORGANIZATION_TYPE = (
    (MAIN, pgettext_lazy("female", "Main")),
    (ACADEMIC_PARTNER, _("Academic partner")),
    (INDUSTRIAL_PARTNER, _("Industrial partner")),
    (SERVICE_PARTNER, _("Service partner")),
    (COMMERCE_PARTNER, _("Commerce partner")),
    (PUBLIC_PARTNER, _("Public partner")),
)
