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


ABSENCE_UNJUSTIFIED = "ABSENCE_UNJUSTIFIED"
ABSENCE_JUSTIFIED = "ABSENCE_JUSTIFIED"
CHEATING = "CHEATING"
SCORE_MISSING = "SCORE_MISSING"

# When the user inform 'A', we have to convert it to 'ABSENCE_UNJUSTIFIED'
# When exporting the data to EPC, we have to convert:
#    'ABSENCE_UNJUSTIFIED' => 'S'
#    'ABSENCE_JUSTIFIED'   => 'M'
#    'CHEATING'            => 'T'
JUSTIFICATION_TYPES = (
    (ABSENCE_UNJUSTIFIED, _('Absence unjustified')),  # A -> S
    (ABSENCE_JUSTIFIED, _('Absence justified')),      # M
    (CHEATING, _('Cheating')))                        # T
