#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from base.business.education_groups.publication_contact import can_postpone_publication_contact
from base.models.education_group_publication_contact import EducationGroupPublicationContact
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_categories import Categories
from base.views.mixins import AjaxTemplateMixin
from education_group.forms.publication_contact import EducationGroupPublicationContactForm
from osis_role.contrib.views import PermissionRequiredMixin


class CommonEducationGroupPublicationContactView(PermissionRequiredMixin, AjaxTemplateMixin, SuccessMessageMixin):
    model = EducationGroupPublicationContact
    context_object_name = "publication_contact"

    form_class = EducationGroupPublicationContactForm
    template_name = "education_group_app/publication_contact/edit_inner.html"
    force_reload = True
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_postpone"] = can_postpone_publication_contact(self.education_group_year)
        return context

    def to_postpone(self) -> bool:
        return self.request.POST.get("to_postpone")

    @cached_property
    def person(self):
        return self.request.user.person

    @cached_property
    def education_group_year(self):
        return get_object_or_404(
            EducationGroupYear.objects.all().select_related('education_group_type'),
            partial_acronym=self.kwargs['code'],
            academic_year__year=self.kwargs['year']
        )

    def get_success_url(self):
        return ""

    def get_permission_object(self):
        return self.education_group_year

    def get_permission_required(self):
        if self.education_group_year.is_common:
            return ('base.change_commonpedagogyinformation',)
        elif self.education_group_year.education_group_type.category == Categories.TRAINING.name:
            return ('base.change_training_pedagogyinformation',)
        elif self.education_group_year.education_group_type.category == Categories.MINI_TRAINING.name:
            return ('base.change_minitraining_pedagogyinformation',)
        elif self.education_group_year.education_group_type.category == Categories.GROUP.name:
            return ('base.change_group_pedagogyinformation',)
        raise Exception("Unknown education group type")
