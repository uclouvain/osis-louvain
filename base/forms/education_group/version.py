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

from base.business import event_perms
from base.forms.utils.choice_field import BLANK_CHOICE_DISPLAY
from base.models.academic_year import AcademicYear


class SpecificVersionForm(forms.Form):
    acronym = forms.CharField(max_length=15, required=True, label=_('Acronym of version'))
    title = forms.CharField(max_length=100, label=_('Full title of the french version'))
    title_english = forms.CharField(max_length=255, label=_('Full title of the english version'))
    end_year = forms.ModelChoiceField(queryset=AcademicYear.objects.none(), required=False,
                                      label=_('This version exists until'), empty_label=BLANK_CHOICE_DISPLAY)

    def __init__(self, max_year=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            event_perm = event_perms.generate_event_perm_creation_end_date_proposal(self.person)
            self.fields["end_year"].queryset = event_perm.get_academic_years()
        except ValueError:
            self.fields['end_year'].disabled = True
