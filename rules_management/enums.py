##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.translation import gettext_lazy as _

TRAINING_DAILY_MANAGEMENT = 'TRAINING_DAILY_MANAGEMENT'
TRAINING_PROPOSAL_MANAGEMENT = 'TRAINING_PROPOSAL_MANAGEMENT'
TRAINING_PGRM_ENCODING_PERIOD = 'TRAINING_PGRM_ENCODING_PERIOD'
MINI_TRAINING_DAILY_MANAGEMENT = 'MINI_TRAINING_DAILY_MANAGEMENT'
MINI_TRAINING_PROPOSAL_MANAGEMENT = 'MINI_TRAINING_PROPOSAL_MANAGEMENT'
MINI_TRAINING_PGRM_ENCODING_PERIOD = 'MINI_TRAINING_PGRM_ENCODING_PERIOD'
GROUP_DAILY_MANAGEMENT = 'GROUP_DAILY_MANAGEMENT'
GROUP_PROPOSAL_MANAGEMENT = 'GROUP_PROPOSAL_MANAGEMENT'
GROUP_PGRM_ENCODING_PERIOD = 'GROUP_PGRM_ENCODING_PERIOD'


CONTEXT_CHOICES = (
    (TRAINING_DAILY_MANAGEMENT, _('Training management day-to-day')),
    (TRAINING_PROPOSAL_MANAGEMENT, _('Training management during proposal stage')),
    (TRAINING_PGRM_ENCODING_PERIOD, _('Training management during program type encoding period')),
    (MINI_TRAINING_DAILY_MANAGEMENT, _('Mini-training management day-to-day')),
    (MINI_TRAINING_PROPOSAL_MANAGEMENT, _('Mini-training management during proposal stage')),
    (MINI_TRAINING_PGRM_ENCODING_PERIOD, _('Mini-training management during program type encoding period')),
    (GROUP_DAILY_MANAGEMENT, _('Group management day-to-day')),
    (GROUP_PROPOSAL_MANAGEMENT, _('Group management during proposal stage')),
    (GROUP_PGRM_ENCODING_PERIOD, _('Group management during program type encoding period')),
)
