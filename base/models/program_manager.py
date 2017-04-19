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
from django.db import models
from django.contrib import admin
from .learning_unit_enrollment import LearningUnitEnrollment
from django.core.exceptions import ObjectDoesNotExist


class ProgramManagerAdmin(admin.ModelAdmin):
    list_display = ('person', 'offer_year')
    raw_id_fields = ('person', 'offer_year')
    fieldsets = ((None, {'fields': ('person', 'offer_year')}),)
    search_fields = ['person__first_name', 'person__last_name', 'offer_year__acronym']
    list_filter = ('offer_year__academic_year',)


class ProgramManager(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True)
    person = models.ForeignKey('Person')
    offer_year = models.ForeignKey('OfferYear')

    @property
    def name(self):
        return self.__str__()

    def __str__(self):
        return u"%s - %s" % (self.person, self.offer_year)

    class Meta:
        unique_together = ('person', 'offer_year',)


def find_by_person(a_person):
    return ProgramManager.objects.select_related("offer_year").filter(person=a_person)


def is_program_manager(user, offer_year=None, learning_unit_year=None):
    """
    Args:
        user: an instance of auth.User
        offer_year: an annual offer to check whether the user is its program manager.
        learning_unit_year: an annual learning unit to check whether it is in the managed offers of the user.

    Returns: True if the user manage an offer. False otherwise.
    """
    if offer_year:
        try:
            programme_manager = ProgramManager.objects.filter(person__user=user, offer_year=offer_year)
            if programme_manager:
                return True
        except ObjectDoesNotExist:
            return False
    elif learning_unit_year:
        offers_user = ProgramManager.objects.filter(person__user=user).values('offer_year')
        enrollments = LearningUnitEnrollment.objects.filter(learning_unit_year=learning_unit_year)\
                                                    .filter(offer_enrollment__offer_year__in=offers_user)
        if enrollments:
            return True
        else:
            return False
    else:
        return ProgramManager.objects.filter(person__user=user).count() > 0


def find_by_offer_year(offer_yr):
    return ProgramManager.objects.filter(offer_year=offer_yr)\
                                 .order_by('person__last_name', 'person__first_name')


def find_by_user(user, academic_year=None):
    queryset = ProgramManager.objects
    if academic_year:
        queryset = queryset.filter(offer_year__academic_year=academic_year)

    return queryset.filter(person__user=user)


def find_by_id(an_id):
    try:
        return ProgramManager.objects.get(pk=an_id)
    except ObjectDoesNotExist:
        return None


def find_by_entity_administration_fac(structure_faculty, academic_yr):
    return ProgramManager.objects.filter(offer_year__entity_administration_fac=structure_faculty,
                                         offer_year__academic_year=academic_yr).distinct('person')


def delete_by_id(an_id):
    pgm_manager = ProgramManager.objects.get(pk=an_id)
    if pgm_manager:
        pgm_manager.delete()


def find_by_offer_year_list(offer_yr_list):
    return ProgramManager.objects.select_related("person").filter(offer_year__in=offer_yr_list)\
        .order_by('person__last_name', 'person__first_name')


def find_by_offer_year_list_person(a_person, offer_yr_list):
    return ProgramManager.objects.select_related("person").filter(person=a_person, offer_year__in=offer_yr_list)


def find_by_person_exclude_offer_list(a_person, offer_yr_list):
    return ProgramManager.objects.filter(person=a_person).exclude(offer_year__in=offer_yr_list)


def find_by_person_academic_year(a_person=None, an_academic_yr=None, entity_list=None, a_grade_type=None):
    queryset = ProgramManager.objects

    if a_person:
        queryset = queryset.filter(person=a_person)

    if an_academic_yr:
        queryset = queryset.filter(offer_year__academic_year=an_academic_yr)

    if entity_list:
        queryset = queryset.filter(offer_year__entity_administration__in=entity_list)

    if a_grade_type:
        queryset = queryset.filter(offer_year__grade_type=a_grade_type)

    return queryset.select_related("offer_year")

def find_by_offer_year_person(a_person, offer_yr):
    return ProgramManager.objects.select_related("person").filter(person=a_person, offer_year=offer_yr)
