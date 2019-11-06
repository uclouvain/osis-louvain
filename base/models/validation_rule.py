############################################################################
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
############################################################################
from ckeditor.fields import RichTextField
from django.db import models
from django.utils.translation import gettext_lazy as _, get_language

from base.models.enums.field_status import FIELD_STATUS, NOT_REQUIRED
from base.models.enums.language_code import LanguageCodes
from osis_common.models.osis_model_admin import OsisModelAdmin


class ValidationRuleAdmin(OsisModelAdmin):
    list_display = ('field_reference', 'status_field', 'initial_value', 'regex_rule', 'placeholder')
    search_fields = ['field_reference']


class ValidationRule(models.Model):
    field_reference = models.CharField(
        max_length=255,
        verbose_name=_("field reference"),
        primary_key=True
    )

    status_field = models.CharField(
        max_length=20,
        choices=FIELD_STATUS,
        default=NOT_REQUIRED
    )

    initial_value = models.CharField(
        max_length=255,
        verbose_name=_("initial value"),
        blank=True
    )

    regex_rule = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("regex rule")
    )

    regex_error_message = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("regex error message")
    )

    help_text_en = RichTextField(
        blank=True,
        verbose_name=_("english help text")
    )

    help_text_fr = RichTextField(
        blank=True,
        verbose_name=_("french help text")
    )

    placeholder = models.CharField(max_length=25, verbose_name=_('Placeholder'), blank=True,)

    class Meta:
        verbose_name = _("validation rule")

    @property
    def help_text(self):
        if get_language() == LanguageCodes.EN.value:
            return self.help_text_en
        return self.help_text_fr
