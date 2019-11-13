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
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F
from django.utils.translation import gettext_lazy as _
from ordered_model.admin import OrderedModelAdmin
from ordered_model.models import OrderedModel
from reversion.admin import VersionAdmin

from base.models.enums.publication_contact_type import PublicationContactType

ROLE_REQUIRED_FOR_TYPES = (
    PublicationContactType.JURY_MEMBER.name,
    PublicationContactType.OTHER_CONTACT.name,
)


class EducationGroupPublicationQuerySet(models.QuerySet):
    def annotate_text(self, language_code):
        return self.annotate(
            role_text=F('role_fr') if language_code == settings.LANGUAGE_CODE_FR else F('role_en'),
        )


class EducationGroupPublicationContactAdmin(VersionAdmin, OrderedModelAdmin):
    list_display = ('education_group_year', 'type', 'role_fr', 'role_en', 'email', 'order', 'move_up_down_links',)
    readonly_fields = ['order']
    search_fields = ['education_group_year__acronym', 'role_fr', 'role_en', 'email']
    raw_id_fields = ('education_group_year', )


class EducationGroupPublicationContact(OrderedModel):
    role_fr = models.CharField(
        max_length=255,
        default='',
        blank=True,
        verbose_name=_('role (french)')
    )
    role_en = models.CharField(
        max_length=255,
        default='',
        blank=True,
        verbose_name=_('role (english)')
    )
    email = models.EmailField(
        verbose_name=_('email'),
    )
    description = models.CharField(
        max_length=255,
        default='',
        blank=True,
        verbose_name=_('Description')
    )
    type = models.CharField(
        max_length=100,
        choices=PublicationContactType.choices(),
        default=PublicationContactType.OTHER_CONTACT.name,
        verbose_name=_('type'),
    )
    education_group_year = models.ForeignKey('EducationGroupYear', on_delete=models.CASCADE)
    order_with_respect_to = ('education_group_year', 'type', )

    objects = EducationGroupPublicationQuerySet.as_manager()

    class Meta:
        ordering = ('education_group_year', 'type', 'order',)

    def clean(self):
        super().clean()

        if self.type in ROLE_REQUIRED_FOR_TYPES and not all([self.role_fr, self.role_en]):
            raise ValidationError({
                'role_fr': _("This field is required."),
                'role_en': _("This field is required.")
            })
        elif self.type not in ROLE_REQUIRED_FOR_TYPES:
            self.role_fr = self.role_en = ''
