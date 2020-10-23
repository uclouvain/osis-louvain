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
from django.core.validators import MinValueValidator
from django.db import models

from cms.enums.entity_name import ENTITY_NAME
from osis_common.models import osis_model_admin


class TextLabelAdmin(osis_model_admin.OsisModelAdmin):
    actions = None  # Remove ability to delete in Admin Interface
    list_display = ('parent', 'entity', 'label', 'order', 'published',)
    search_fields = ['label']
    ordering = ('entity',)
    list_filter = ('published',)

    def delete_selected(self, obj):
        for text_label in obj.all():
            text_label.delete()
            reorganise_order(text_label.parent)

    def has_delete_permission(self, request, obj=None):
        return False


class TextLabel(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.CASCADE)
    entity = models.CharField(max_length=25, choices=ENTITY_NAME)
    label = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    published = models.BooleanField(default=True)

    class Meta:
        unique_together = ('parent', 'order')

    def __str__(self):
        return "{} - {}".format(self.label, self.order)

    def save(self, *args, **kwargs):
        parent_db = None
        if self.pk is not None:
            self.check_circular_dependency()
            parent_db = (TextLabel.objects.get(pk=self.pk)).parent

        max_order = get_highest_order(self.parent)
        if max_order is None:
            self.order = 1
        elif max_order < self.order:
            self.order = max_order + 1
        else:
            shift_text_label(self.parent, self.order)

        super(TextLabel, self).save(*args, **kwargs)

        reorganise_order(parent_db)
        if parent_db == self.parent:
            self.refresh_from_db()

        return self

    def get_all_children(self, include_self=False):
        text_label_children = []
        if include_self:
            text_label_children.append(self)

        for child in TextLabel.objects.filter(parent=self):
            text_label_children += child.get_all_children(include_self=True)

        return text_label_children

    def check_circular_dependency(self):
        for child in self.get_all_children():
            if child == self.parent:
                raise ValueError('Circular dependency found')


def get_highest_order(parent=None):
    """Return the highest order value in the context of parent"""
    query = TextLabel.objects.filter(parent=parent) \
        .aggregate(models.Max('order'))
    return query.get('order__max', None)


def shift_text_label(parent, start_order):
    TextLabel.objects.filter(parent=parent, order__gte=start_order) \
        .order_by('-order') \
        .update(order=models.F('order') + 1)


def reorganise_order(parent):
    list_to_reorder = list(TextLabel.objects.filter(parent=parent).order_by('order'))
    for index, text_label in enumerate(list_to_reorder, 1):
        if text_label.order != index:
            text_label.order = index
            super(TextLabel, text_label).save()
