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
from dal import autocomplete
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Subquery, OuterRef, BooleanField, Q, Value
from django.db.models.functions import Concat
from django.utils.html import format_html

from base.forms.learning_unit.entity_form import find_additional_requirement_entities_choices
from base.models.campus import Campus
from base.models.entity_version import find_pedagogical_entities_version
from base.models.enums.organization_type import ACADEMIC_PARTNER, MAIN
from base.models.organization import Organization
from base.models.person import Person
from reference.models.country import Country


class OrganizationAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Organization.objects.filter(type=ACADEMIC_PARTNER)

        country = self.forwarded.get('country', None)
        if country:
            qs = qs.filter(
                organizationaddress__is_main=True,
                organizationaddress__country=country,
            )

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs.distinct().order_by('name')

    def get_result_label(self, result):
        return result.name


class CountryAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Country.objects.filter(organizationaddress__isnull=False).distinct()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs.distinct().order_by('name')


class CampusAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Campus.objects.annotate(
            organization_is_current_partner=Subquery(
                Organization.objects.filter(
                    pk=OuterRef('organization_id'),
                    type=ACADEMIC_PARTNER,
                ).values('is_current_partner')[:1],
                output_field=BooleanField(),
            )
        ).filter(organization_is_current_partner=True)

        country = self.forwarded.get('country_external_institution', None)

        if country:
            qs = qs.filter(organization__organizationaddress__country=country)

        if self.q:
            qs = qs.filter(Q(organization__name__icontains=self.q) | Q(name__icontains=self.q))

        return qs.select_related('organization').order_by('organization__name').distinct()

    def get_result_label(self, result):
        return "{} ({})".format(result.organization.name, result.name)


class EntityAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        country = self.forwarded.get('country', None)
        qs = find_additional_requirement_entities_choices()
        if country:
            qs = qs.exclude(entity__organization__type=MAIN).order_by('title')
            if country != "all":
                qs = qs.filter(entity__country_id=country)
        else:
            qs = find_pedagogical_entities_version().order_by('acronym')
        if self.q:
            qs = qs.filter(Q(title__icontains=self.q) | Q(acronym__icontains=self.q))
        return qs

    def get_result_label(self, result):
        return format_html(result.verbose_title)


class AllocationEntityAutocomplete(EntityAutocomplete):
    def get_queryset(self):
        self.forwarded['country'] = self.forwarded.get('country_allocation_entity')
        return super(AllocationEntityAutocomplete, self).get_queryset()


class AdditionnalEntity1Autocomplete(EntityAutocomplete):
    def get_queryset(self):
        self.forwarded['country'] = self.forwarded.get('country_additional_entity_1')
        return super(AdditionnalEntity1Autocomplete, self).get_queryset()


class AdditionnalEntity2Autocomplete(EntityAutocomplete):
    def get_queryset(self):
        self.forwarded['country'] = self.forwarded.get('country_additional_entity_2')
        return super(AdditionnalEntity2Autocomplete, self).get_queryset()


class EntityRequirementAutocomplete(EntityAutocomplete):
    def get_queryset(self):
        return super(EntityRequirementAutocomplete, self).get_queryset()\
            .filter(entity__in=self.request.user.person.linked_entities)

    def get_result_label(self, result):
        return format_html(result.verbose_title)


class EmployeeAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Person.employees.annotate(
            fullname=Concat('last_name', Value(' '), 'first_name'),
            fullname_inverted=Concat('first_name', Value(' '), 'last_name'),
        )
        if self.q:
            qs = qs.filter(
                Q(last_name__icontains=self.q) |
                Q(first_name__icontains=self.q) |
                Q(middle_name__icontains=self.q) |
                Q(global_id__icontains=self.q) |
                Q(fullname__icontains=self.q) |
                Q(fullname_inverted__icontains=self.q)
            )
        return qs.order_by("last_name", "first_name")

    def get_result_label(self, result):
        return "{last_name} {first_name}".format(last_name=result.last_name.upper(), first_name=result.first_name)
