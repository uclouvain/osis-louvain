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
from django.views.generic import CreateView

from education_group.views.publication_contact.common import CommonEducationGroupPublicationContactView


class CreateEducationGroupPublicationContactView(CommonEducationGroupPublicationContactView, CreateView):
    def get_success_message(self, cleaned_data):
        if self.to_postpone():
            return _("Contact has been created (with postpone)")
        return _("Contact has been created (without postpone)")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return {
            'education_group_year': self.education_group_year,
            **kwargs
        }
