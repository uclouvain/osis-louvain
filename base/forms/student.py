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
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from base.models.student import Student


class StudentSearchForm(forms.Form):
    registration_id = forms.CharField(max_length=10, required=False, label=_('Registration Id'))
    name = forms.CharField(max_length=20, required=False, label=_('Name'))

    def get_objects(self):
        registration_id = self.cleaned_data["registration_id"]
        name = self.cleaned_data["name"]
        qs = Student.objects.none()
        if registration_id:
            qs = Student.objects.filter(registration_id=registration_id)
        elif name:
            qs = Student.objects.all().order_by('person__last_name', 'person__first_name')
            for word in name.split():
                qs = qs.filter(Q(person__first_name__icontains=word) | Q(person__last_name__icontains=word))

        return qs.select_related("person")
