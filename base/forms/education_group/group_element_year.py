##############################################################################
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
##############################################################################
from django import forms

from base.models.group_element_year import GroupElementYear


class UpdateGroupElementYearForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(UpdateGroupElementYearForm, self).__init__(*args, **kwargs)
        self.fields['is_mandatory'].label = ""

    class Meta:
        model = GroupElementYear
        fields = [
            "relative_credits",
            "min_credits",
            "max_credits",
            "is_mandatory",
            "block",
            "quadrimester_derogation",
            "link_type",
            "comment",
            "comment_english",
        ]
        widgets = {
            "comment": forms.Textarea(attrs={'rows': 5}),
            "comment_english": forms.Textarea(attrs={'rows': 5}),

        }
