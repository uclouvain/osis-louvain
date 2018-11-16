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
from django.utils.translation import ugettext_lazy as _

from base import models as mdl
from base.forms.utils.choice_field import add_blank
from base.models.entity_version import EntityVersion
from base.models.enums import entity_type


class EntitySearchForm(forms.Form):
    acronym = forms.CharField(label=_('Acronym'), required=False)
    title = forms.CharField(label=_('Title'), required=False)
    entity_type = forms.ChoiceField(label=_('type'), choices=add_blank(entity_type.ENTITY_TYPES), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['acronym'].widget.attrs['style'] = "text-transform:uppercase"

    def get_entities(self):
        if super().is_valid():
            return mdl.entity_version.search_entities(with_entity=True, **self.cleaned_data)
        else:
            return EntityVersion.objects.all()
