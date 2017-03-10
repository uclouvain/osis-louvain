##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib import admin
from base.enums.entity_name import ENTITY_NAME
from base.models.exceptions import TxtLabelOrderMustExitsException


class TextLabelAdmin(admin.ModelAdmin):
    list_display = ('entity_name', 'part_of', 'label', 'order', 'published', 'children')
    fieldsets = ((None, {'fields': ('entity_name', 'part_of', 'label', 'order', 'published')}),)
    search_fields = ['acronym']


class TextLabel(models.Model):
    entity_name = models.CharField(max_length=25, choices=ENTITY_NAME)
    part_of = models.ForeignKey('self', blank=True, null=True)
    label = models.CharField(max_length=255)
    order = models.IntegerField(default=0)
    published = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.order:
            if self.part_of:
                txtlabelsamechildren = TextLabel.objects.filter(part_of=self.part_of).order_by('order')
                for txtlabelsamechild in txtlabelsamechildren:
                    if txtlabelsamechild.order >= self.order:
                        TextLabel.objects.filter(id=txtlabelsamechild.id).update(order=txtlabelsamechild.order+1)
            else:
                txtlabelsameparents = TextLabel.objects.filter(part_of=None).order_by('order')
                for txtlabelsameparent in txtlabelsameparents:
                    if txtlabelsameparent.order >= self.order:
                        TextLabel.objects.filter(id=txtlabelsameparent.id).update(order=txtlabelsameparent.order+1)
        else:
            raise TxtLabelOrderMustExitsException('A textlabel must have an order defined')
        super(TextLabel, self).save(*args, **kwargs)

    @property
    def children(self):
        return TextLabel.objects.filter(part_of=self.pk).order_by('order')

    def __str__(self):
        return self.label


def find_by_id(text_label_id):
    return TextLabel.objects.get(pk=text_label_id)
