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
from datetime import datetime
from typing import List

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Prefetch
from django.views.generic import DetailView
from django_filters.views import FilterView

from base.forms.organization import OrganizationFilter
from base.models.entity_version import EntityVersion
from base.models.entity_version_address import EntityVersionAddress
from base.models.organization import Organization


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
        return super().get_queryset().prefetch_related("campus_set")

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "addresses": self.get_addresses()
        }

    def get_addresses(self) -> List[EntityVersionAddress]:
        root_entity_version = EntityVersion.objects.current(datetime.now()).filter(
            entity__organization=self.kwargs['organization_id']
        ).only_roots().prefetch_related(
            Prefetch(
                'entityversionaddress_set',
                queryset=EntityVersionAddress.objects.all().select_related('country')
            )
        ).first()
        if root_entity_version:
            return root_entity_version.entityversionaddress_set.all()
        return []
