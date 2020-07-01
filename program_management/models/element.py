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

from collections import Counter

from django.db import models
from django.utils.translation import gettext_lazy as _
from reversion.admin import VersionAdmin

from osis_common.models.osis_model_admin import OsisModelAdmin
from program_management.models.enums.node_type import NodeType


class ElementManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'education_group_year',
            'group_year',
            'learning_unit_year',
            'learning_class_year'
        )


class ElementAdmin(VersionAdmin, OsisModelAdmin):
    list_display = ('education_group_year', 'group_year', 'learning_unit_year', 'learning_class_year')
    search_fields = ('education_group_year__acronym',
                     'group_year__acronym',
                     'learning_unit_year__acronym',
                     'learning_class_year__acronym')


class Element(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)

    education_group_year = models.ForeignKey(
        'base.EducationGroupYear',
        blank=True, null=True,
        verbose_name=_('education group year'),
        on_delete=models.PROTECT
    )
    group_year = models.OneToOneField(
        'education_group.GroupYear',
        blank=True, null=True,
        verbose_name=_('group year'),
        on_delete=models.PROTECT
    )
    learning_unit_year = models.OneToOneField(
        'base.LearningUnitYear',
        blank=True, null=True,
        verbose_name=_('learning unit year'),
        on_delete=models.PROTECT,
    )
    learning_class_year = models.OneToOneField(
        'learning_unit.LearningClassYear',
        blank=True, null=True,
        verbose_name=_('learning class year'),
        on_delete=models.PROTECT,
    )

    objects = ElementManager()

    def __str__(self):
        field = {
            NodeType.EDUCATION_GROUP: self.education_group_year,
            NodeType.GROUP: self.group_year,
            NodeType.LEARNING_UNIT: self.learning_unit_year,
            NodeType.LEARNING_CLASS: self.learning_class_year,
        }[self.node_type]
        return str(field)

    def save(self, *args, **kwargs):

        if not any([self.education_group_year, self.group_year, self.learning_class_year, self.learning_unit_year]):
            raise AttributeError(
                _('At least an education group year, a group year, a learning unit year or a learning class year has '
                  'to be set')
            )
        resulted_counter = Counter([self.education_group_year,
                                    self.group_year,
                                    self.learning_class_year,
                                    self.learning_unit_year])

        if resulted_counter[None] < 3:
            raise AttributeError(
                _(
                    'Only one of the following has to be set : an education group year, a group year, '
                    'a learning unit year or a learning class')
            )

        super().save(*args, **kwargs)

    @property
    def node_type(self):
        if self.education_group_year:
            return NodeType.EDUCATION_GROUP
        elif self.group_year:
            return NodeType.GROUP
        elif self.learning_unit_year:
            return NodeType.LEARNING_UNIT
        elif self.learning_class_year:
            return NodeType.LEARNING_CLASS
