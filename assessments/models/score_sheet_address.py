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
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import gettext_lazy

from assessments.models.enums import score_sheet_address_choices
from osis_common.models.osis_model_admin import OsisModelAdmin


class ScoreSheetAddressAdmin(OsisModelAdmin):
    list_display = ('offer_year', 'entity_address_choice', 'location', 'postal_code', 'city', 'phone', 'fax', 'email')
    search_fields = ['offer_year__acronym', 'location']
    list_filter = ('entity_address_choice',)
    raw_id_fields = ('offer_year',)


class ScoreSheetAddress(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    offer_year = models.OneToOneField('base.OfferYear', on_delete=models.CASCADE)
    # Info to find the address
    entity_address_choice = models.CharField(max_length=50, blank=True, null=True,
                                             choices=score_sheet_address_choices.CHOICES)
    # Address fields
    recipient = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)  # Address for scores sheets
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    country = models.ForeignKey(
        'reference.Country',
        blank=True, null=True,
        on_delete=models.CASCADE
    )
    phone = models.CharField(max_length=30, blank=True, null=True, verbose_name=gettext_lazy("Phone"))
    fax = models.CharField(max_length=30, blank=True, null=True, verbose_name=gettext_lazy("Fax"))
    email = models.EmailField(null=True, blank=True, verbose_name=gettext_lazy("Email"))

    @property
    def customized(self):
        return self.location and self.postal_code and self.city and not self.entity_address_choice

    def save(self, *args, **kwargs):
        if self.customized or self.entity_address_choice:
            super(ScoreSheetAddress, self).save(*args, **kwargs)
        else:
            raise Exception(
                "Please set either entity_address_choice nor location, postal_code, city... but not all of them.")

    def __str__(self):
        return "{0} - {1}".format(self.offer_year, self.entity_address_choice)


def get_from_offer_year(off_year):
    try:
        return ScoreSheetAddress.objects.get(offer_year=off_year)
    except ObjectDoesNotExist:
        return None
