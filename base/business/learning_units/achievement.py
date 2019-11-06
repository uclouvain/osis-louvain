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
from base.models.learning_achievement import find_previous_achievements

HTML_ANCHOR = "#anchor_"
UP = 'up'
DOWN = 'down'
DELETE = 'delete'
AVAILABLE_ACTIONS = [DELETE, UP, DOWN]


def get_previous_achievement(achievement_fr):
    return find_previous_achievements(achievement_fr.learning_unit_year, achievement_fr.language,
                                      achievement_fr.order).order_by('order').last()


def get_anchor_reference(operation_str, achievement_fr):
    if operation_str in AVAILABLE_ACTIONS:
        achievement_previous = get_previous_achievement(achievement_fr)
        if achievement_previous:
            return "{}{}".format(HTML_ANCHOR, achievement_previous.id)
    return ''
