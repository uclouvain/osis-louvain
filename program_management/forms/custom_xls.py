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
from django import forms
from django.utils.translation import gettext_lazy as _


class CustomXlsForm(forms.Form):

    required_entity = forms.BooleanField(required=False, label=_('Requirement entity'))
    allocation_entity = forms.BooleanField(required=False, label=_('Attribution entity'))
    credits = forms.BooleanField(required=False, label=_('Credits'))
    periodicity = forms.BooleanField(required=False, label=_('Periodicity'))
    active = forms.BooleanField(required=False, label=_('Active'))
    quadrimester = forms.BooleanField(required=False, label=_('Quadrimester'))
    session_derogation = forms.BooleanField(required=False, label=_('Session derogation'))
    volume = forms.BooleanField(required=False, label=_('Volume'))
    teacher_list = forms.BooleanField(required=False, label=_('Tutors'))
    proposition = forms.BooleanField(required=False, label=_('Proposals'))
    english_title = forms.BooleanField(required=False, label=_('Title in English'))
    language = forms.BooleanField(required=False, label=_('Language'))
    specifications = forms.BooleanField(required=False, label=_('Specifications'))
    description_fiche = forms.BooleanField(required=False, label=_('Description fiche'))

    def get_optional_data(self):
        data = []
        if self.is_valid():
            for field in self.fields:
                if self.cleaned_data[field]:
                    data.append(field)
        return data
