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
from django.db import models
from django.utils.translation import gettext_lazy as _
from reversion.admin import VersionAdmin

from base.models.abstracts.abstract_achievement import AbstractAchievement, AbstractAchievementAdmin
from osis_common.utils.models import get_object_or_none


class LearningAchievementAdmin(VersionAdmin, AbstractAchievementAdmin):
    raw_id_fields = ('learning_unit_year',)
    list_filter = ('language', 'learning_unit_year__academic_year')

    def get_list_display(self, request):
        return ('learning_unit_year',) + super().get_list_display(request)

    def get_search_fields(self, request):
        return ['learning_unit_year__acronym'] + super().get_search_fields(request)


class LearningAchievement(AbstractAchievement):
    learning_unit_year = models.ForeignKey(
        'LearningUnitYear',
        verbose_name=_('learning unit year'),
        on_delete=models.CASCADE,
    )
    order_with_respect_to = ('learning_unit_year', 'language')

    class Meta(AbstractAchievement.Meta):
        unique_together = ("consistency_id", "learning_unit_year", "language")

    def __str__(self):

        return u'{} - {} (order {})'.format(self.learning_unit_year, self.code_name, self.order)


def find_by_learning_unit_year(learning_unit_yr):
    return LearningAchievement.objects.filter(learning_unit_year=learning_unit_yr) \
        .select_related('language') \
        .order_by('order', 'language__code')


def find_learning_unit_achievement(consistency_id, learning_unit_yr, a_language_code, position):
    return get_object_or_none(
        LearningAchievement,
        consistency_id=consistency_id,
        learning_unit_year=learning_unit_yr,
        language__code=a_language_code,
        order=position
    )


def search(learning_unit_yr=None, position=None):
    queryset = LearningAchievement.objects
    if learning_unit_yr:
        queryset = queryset.filter(learning_unit_year=learning_unit_yr)
    if position is not None:
        queryset = queryset.filter(order=position)
    return queryset


def find_previous_achievements(learning_unit_yr, a_language, position):
    return LearningAchievement.objects.filter(learning_unit_year=learning_unit_yr,
                                              language=a_language,
                                              order__lt=position)
