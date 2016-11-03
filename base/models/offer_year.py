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
from django.utils.translation import ugettext_lazy as _
from base.models import offer, program_manager, academic_year
from osis_common.models.serializable_model import SerializableModel


class OfferYearAdmin(admin.ModelAdmin):
    list_display = ('acronym', 'offer', 'parent', 'title', 'academic_year', 'changed')
    fieldsets = ((None, {'fields': ('offer', 'academic_year', 'entity_administration', 'entity_administration_fac',
                                    'entity_management', 'entity_management_fac', 'acronym', 'title', 'parent',
                                    'title_international', 'title_short', 'title_printable', 'grade', 'campus')}),)
    list_filter = ('academic_year__year',)
    raw_id_fields = ('offer', 'parent')
    search_fields = ['acronym']


GRADE_TYPES = (
    ('BACHELOR', _('bachelor')),
    ('MASTER', _('master')),
    ('DOCTORATE', _('ph_d')))


class OfferYear(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True)
    offer = models.ForeignKey('Offer')
    academic_year = models.ForeignKey('AcademicYear')
    acronym = models.CharField(max_length=15, db_index=True)
    title = models.CharField(max_length=255)
    title_international = models.CharField(max_length=255, blank=True, null=True)
    title_short = models.CharField(max_length=255, blank=True, null=True)
    title_printable = models.CharField(max_length=255, blank=True, null=True)
    parent = models.ForeignKey('self', blank=True, null=True, related_name='children', db_index=True)
    grade = models.CharField(max_length=20, blank=True, null=True, choices=GRADE_TYPES)
    entity_administration = models.ForeignKey('Structure', related_name='admministration', blank=True, null=True)
    entity_administration_fac = models.ForeignKey('Structure', related_name='admministration_fac', blank=True, null=True)
    entity_management = models.ForeignKey('Structure', related_name='management', blank=True, null=True)
    entity_management_fac = models.ForeignKey('Structure', related_name='management_fac', blank=True, null=True)
    recipient = models.CharField(max_length=255, blank=True, null=True)  # Recipient of scores cheets (Structure)
    location = models.CharField(max_length=255, blank=True, null=True)  # Address for scores cheets
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    country = models.ForeignKey('reference.Country', blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    fax = models.CharField(max_length=30, blank=True, null=True)
    campus = models.ForeignKey('Campus', blank=True, null=True)
    grade_type = models.ForeignKey('reference.GradeType', blank=True, null=True)

    def __str__(self):
        return u"%s - %s" % (self.academic_year, self.acronym)

    def related_entities(self):
        entities = []
        if self.entity_administration:
            entities.append(self.entity_administration)

        if self.entity_administration_fac and self.entity_administration_fac not in entities:
            entities.append(self.entity_administration_fac)

        if self.entity_management and self.entity_management not in entities:
            entities.append(self.entity_management)

        if self.entity_management_fac:
            entities.append(self.entity_management_fac)

        return entities

    @property
    def offer_year_children(self):
        """
        To find children
        """
        return OfferYear.objects.filter(parent=self)

    @property
    def offer_year_sibling(self):
        """
        To find other focuses
        """
        if self.parent:
            return OfferYear.objects.filter(parent=self.parent).exclude(id=self.id).exclude()
        return None

    @property
    def is_orientation(self):
        if self.orientation_sibling():
            return True
        else:
            return False

    @property
    def orientation_sibling(self):
        if self.offer:
            off = offer.find_by_id(self.offer.id)
            return OfferYear.objects.filter(offer=off, acronym=self.acronym,
                                            academic_year=self.academic_year).exclude(id=self.id)
        return None


def find_by_academic_year(academic_yr):
    return OfferYear.objects.filter(academic_year=academic_yr)


def find_by_structure(struct):
    return OfferYear.objects.filter(entity_management=struct).order_by('academic_year', 'acronym')


def find_by_id(offer_year_id):
    return OfferYear.objects.get(pk=offer_year_id)


def find_by_acronym(acronym):
    return OfferYear.objects.filter(acronym=acronym).first()


def search(entity=None, academic_yr=None, acronym=None):
    """
    Offers are organized hierarchically. This function returns only root offers.
    """
    out = None
    queryset = OfferYear.objects

    if entity:
        queryset = queryset.filter(entity_management__acronym__icontains=entity)

    if academic_yr:
        queryset = queryset.filter(academic_year=academic_yr)

    if acronym:
        queryset = queryset.filter(acronym__icontains=acronym)

    if entity or academic_yr or acronym:
        out = queryset.order_by('acronym')
               
    return out


def find_by_academicyear_acronym(academic_yr, acronym):
    return OfferYear.objects.filter(academic_year=academic_yr, acronym=acronym)


def find_by_user(user, academic_yr):
    """
    :param user: User from which we get the offerYears.
    :param academic_yr: The academic year (takes the current academic year by default).
    :return: All OfferYears where the user is a program manager for a given year.
    """
    if not academic_yr:
        academic_yr = academic_year.current_academic_year()
    program_manager_queryset = program_manager.find_by_user(user, academic_year=academic_yr)
    offer_year_ids = program_manager_queryset.values_list('offer_year', flat=True).distinct('offer_year')
    return OfferYear.objects.filter(pk__in=offer_year_ids).order_by('acronym')


def find_by_offer(offers):
    return OfferYear.objects.filter(offer__in=offers)
