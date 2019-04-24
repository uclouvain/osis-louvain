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
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.views.generic import DetailView
from reversion.models import Version

from base.business.learning_unit import get_organization_from_learning_unit_year, get_all_attributions, \
    get_components_identification
from base.business.learning_unit_proposal import get_difference_of_proposal
from base.business.learning_units.perms import is_eligible_to_create_partim, learning_unit_year_permissions, \
    learning_unit_proposal_permissions, is_eligible_for_modification
from base.models.academic_year import current_academic_year
from base.models.entity_version import get_by_entity_and_date
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import Person
from base.models.proposal_learning_unit import ProposalLearningUnit
from base.models.utils.utils import get_object_or_none


class DetailLearningUnitYearView(PermissionRequiredMixin, DetailView):
    permission_required = 'base.can_access_learningunit'
    raise_exception = True

    template_name = "learning_unit/identification.html"

    pk_url_kwarg = "learning_unit_year_id"
    context_object_name = "learning_unit_year"

    model = LearningUnitYear

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Change template and permissions for external learning units.
        if self.object.is_external():
            self.permission_required = "base.can_access_externallearningunityear"
            self.template_name = "learning_unit/external/read.html"

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # Get does not need to fetch self.object again
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    @cached_property
    def person(self):
        return get_object_or_404(Person.objects.select_related('user'), user=self.request.user)

    def get_queryset(self):
        return super().get_queryset().select_related(
            'learning_container_year__academic_year',
            'academic_year', 'learning_unit',
            'campus__organization', 'externallearningunityear'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['current_academic_year'] = current_academic_year()
        context['is_person_linked_to_entity'] = self.person.is_linked_to_entity_in_charge_of_learning_unit_year(
            self.object)

        context['warnings'] = self.object.warnings

        context['learning_container_year_partims'] = self.object.get_partims_related()
        context['experimental_phase'] = True
        context.update(get_all_attributions(self.object))
        components = get_components_identification(self.object)

        context['components'] = components.get('components')
        context['REQUIREMENT_ENTITY'] = components.get('REQUIREMENT_ENTITY')
        context['ADDITIONAL_REQUIREMENT_ENTITY_1'] = components.get('ADDITIONAL_REQUIREMENT_ENTITY_1')
        context['ADDITIONAL_REQUIREMENT_ENTITY_2'] = components.get('ADDITIONAL_REQUIREMENT_ENTITY_2')

        proposal = get_object_or_none(ProposalLearningUnit, learning_unit_year__learning_unit=self.object.learning_unit)
        context['proposal'] = proposal

        context['proposal_folder_entity_version'] = get_by_entity_and_date(
            proposal.entity, None) if proposal else None
        context['differences'] = get_difference_of_proposal(proposal, self.object) \
            if proposal and proposal.learning_unit_year == self.object else {}

        context.update(self.get_context_permission(proposal))
        context["versions"] = self.get_versions()
        return context

    def get_context_permission(self, proposal):
        context = {
            "can_create_partim": is_eligible_to_create_partim(self.object, self.person),
            'can_manage_volume': is_eligible_for_modification(self.object, self.person),
        }

        # append permissions
        context.update(learning_unit_year_permissions(self.object, self.person))
        context.update(learning_unit_proposal_permissions(proposal, self.person, self.object))

        return context

    def get_versions(self):
        """ Fetch all versions related to the learning unit year """
        versions = Version.objects.get_for_object(self.object)
        versions |= Version.objects.get_for_object(self.object.learning_container_year)
        versions |= Version.objects.get_for_object(self.object.learning_unit)

        if self.object.is_external():
            versions |= Version.objects.get_for_object(self.object.externallearningunityear)

        for component in self.object.learningcomponentyear_set.all():
            versions |= Version.objects.get_for_object(component)
            for entity_component in component.entitycomponentyear_set.all():
                versions |= Version.objects.get_for_object(entity_component)

        return versions.order_by('-revision__date_created').distinct('revision__date_created'
                                                                     ).select_related('revision__user__person')
