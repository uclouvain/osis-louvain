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
from django.utils.translation import gettext_lazy as _
from django.views.generic import UpdateView

from education_group.forms.publication_contact import EducationGroupEntityPublicationContactForm
from base.models.education_group_year import EducationGroupYear
from education_group.views.publication_contact.common import CommonEducationGroupPublicationContactView


class UpdateEducationGroupPublicationContactView(CommonEducationGroupPublicationContactView, UpdateView):
    pk_url_kwarg = 'publication_contact_id'

    def get_success_message(self, cleaned_data):
        if self.to_postpone():
            return _("Contact has been updated (with postpone)")
        return _("Contact has been updated (without postpone)")


class UpdateEducationGroupEntityPublicationContactView(CommonEducationGroupPublicationContactView, UpdateView):
    model = EducationGroupYear
    context_object_name = "education_group_year"

    form_class = EducationGroupEntityPublicationContactForm
    pk_url_kwarg = "education_group_year_id"
    template_name = "education_group_app/publication_contact/entity_edit_inner.html"

    def get_success_message(self, cleaned_data):
        if self.to_postpone():
            return _("Entity has been updated (with postpone)")
        return _("Entity has been updated (without postpone)")
