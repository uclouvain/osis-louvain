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
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.db.models import Q, Prefetch
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import DetailView
from django_filters.views import FilterView

from base.forms.organization import OrganizationFilter
from base.forms.organization_address import OrganizationAddressForm
from base.models.campus import Campus
from base.models.organization import Organization
from base.models.organization_address import OrganizationAddress
from reference.models.country import Country


class OrganizationSearch(PermissionRequiredMixin, FilterView):
    model = Organization
    paginate_by = 20
    template_name = "organization/organizations.html"

    filterset_class = OrganizationFilter
    permission_required = 'base.can_access_organization'
    raise_exception = True

    def get_context_data(self, *, object_list=None, **kwargs):
        # Display the list even if the filter is not bound
        if not self.filterset.is_bound:
            object_list = self.filterset.qs
        return super().get_context_data(object_list=object_list, **kwargs)


class DetailOrganization(PermissionRequiredMixin, DetailView):
    model = Organization
    template_name = "organization/organization.html"
    permission_required = 'base.can_access_organization'
    raise_exception = True
    pk_url_kwarg = "organization_id"

    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            Prefetch(
                "organizationaddress_set",
                queryset=OrganizationAddress.objects.select_related("country")
            ),
            "campus_set",
        )


@login_required
@permission_required('base.can_access_organization', raise_exception=True)
def organization_address_read(request, organization_address_id):
    organization_address = get_object_or_404(
        OrganizationAddress.objects.select_related('organization', 'country'),
        id=organization_address_id
    )
    return render(request, "organization/organization_address.html", {
            'organization_address': organization_address,
        }
    )


@login_required
@permission_required('base.can_access_organization', raise_exception=True)
def organization_address_edit(request, organization_address_id):
    organization_address = get_object_or_404(
        OrganizationAddress.objects.select_related('organization'),
        id=organization_address_id
    )
    form = OrganizationAddressForm(request.POST or None, instance=organization_address)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse("organization_address_read", args=[organization_address.pk]))

    return render(request, "organization/organization_address_form.html", {
            'organization_address': organization_address,
            'form': form
        }
    )


@login_required
@require_POST
@permission_required('base.can_access_organization', raise_exception=True)
def organization_address_delete(request, organization_address_id):
    organization_address = get_object_or_404(
        OrganizationAddress.objects.select_related('organization'),
        id=organization_address_id
    )
    organization_address.delete()
    return HttpResponseRedirect(reverse("organization_read", args=[organization_address.organization.pk]))


class OrganizationAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Organization.objects.all()

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
        qs = Campus.objects.filter(organization__is_current_partner=True)

        country = self.forwarded.get('country_external_institution', None)

        if country:
            qs = qs.filter(organization__organizationaddress__country=country)

        if self.q:
            qs = qs.filter(Q(organization__name__icontains=self.q) | Q(name__icontains=self.q))

        return qs.select_related('organization').order_by('organization__name')

    def get_result_label(self, result):
        return "{} ({})".format(result.organization.name, result.name)
