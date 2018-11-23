############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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

from base.models.learning_unit_year import LearningUnitYear
from base.models.person import Person
from base.views.learning_units.common import get_learning_unit_identification_context


class DetailLearningUnitYearView(PermissionRequiredMixin, DetailView):
    permission_required = 'base.can_access_learningunit'
    raise_exception = True

    template_name = "learning_unit/identification.html"

    pk_url_kwarg = "learning_unit_year_id"
    context_object_name = "learning_unit_year"

    model = LearningUnitYear

    def dispatch(self, request, *args, **kwargs):
        # Change template and permissions for external learning units.
        if self.get_object().is_external():
            self.permission_required = "base.can_access_externallearningunityear"
            self.template_name = "learning_unit/external/read.html"

        return super().dispatch(request, *args, **kwargs)

    @cached_property
    def person(self):
        return get_object_or_404(Person, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # TODO clean in the context params alredy given by the View.
        context.update(get_learning_unit_identification_context(
            self.kwargs['learning_unit_year_id'], self.person
        ))
        context["versions"] = self.get_versions()
        return context

    def get_versions(self):
        """ Fetch all versions related to the learning unit year """
        versions = Version.objects.get_for_object(self.object)
        versions |= Version.objects.get_for_object(self.object.learning_container_year)
        versions |= Version.objects.get_for_object(self.object.learning_unit)

        if self.object.is_external():
            versions |= Version.objects.get_for_object(self.object.externallearningunityear)

        for component in self.object.learning_component_years.all():
            versions |= Version.objects.get_for_object(component)
            for entity_component in component.entitycomponentyear_set.all():
                versions |= Version.objects.get_for_object(entity_component)

        return versions.order_by('-revision__date_created').distinct('revision__date_created')
