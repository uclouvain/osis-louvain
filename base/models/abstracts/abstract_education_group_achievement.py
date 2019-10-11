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
from ckeditor.fields import RichTextField
from django.conf import settings
from django.db import models
from django.db.models import F
from django.utils.translation import ugettext_lazy as _
from ordered_model.admin import OrderedModelAdmin
from ordered_model.models import OrderedModel


class AbstractEducationGroupAchievementAdmin(OrderedModelAdmin):
    list_display = ('code_name', 'order', 'move_up_down_links')
    readonly_fields = ['order']
    search_fields = ['code_name', 'order']


class AbstractEducationGroupAchievementQuerySet(models.QuerySet):
    def annotate_text(self, language_code):
        return self.annotate(
            text=F('french_text') if language_code == settings.LANGUAGE_CODE_FR else F('english_text')
        )


class AbstractEducationGroupAchievement(OrderedModel):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    code_name = models.CharField(max_length=100, verbose_name=_('code'))

    english_text = RichTextField(null=True, verbose_name=_('text in English'))
    french_text = RichTextField(null=True, verbose_name=_('text in French'))

    class Meta:
        abstract = True

    objects = AbstractEducationGroupAchievementQuerySet.as_manager()
