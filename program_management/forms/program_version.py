##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from operator import attrgetter
from django import forms
from django.urls import reverse


class ProgramVersionForm(forms.Form):

    # Unfull to simplify usage of version in view/template
    version_label = None    # Used in dropdown in interface
    is_standard = False     # Used to define version_label and order for displaying version_label in interface
    version_name = None

    version_title_complement = None
    version_list_for_url = None
    additional_title = None

    def __init__(self, *args, **kwargs):
        self.version_name = kwargs.pop('version_name')
        self.transition = kwargs.pop('transition')
        self.version_view = kwargs.pop('list_of_versions')
        offer_id = kwargs.pop('offer_id')
        self.version_list_for_url = []

        self.version_list = ordered_list(self.version_view)

        for a_version in self.version_list:
            is_current = _is_current(a_version,
                                     self.version_name,
                                     self.transition)

            self.version_list_for_url.append({
                'url': _compute_url(a_version, offer_id),
                'version_name': '-' if a_version.version_name == '' else a_version.version_name,
                'transition': 'transition' if a_version.is_transition else '-',
                'version_label': 'Standard' if a_version.version_label == '' else a_version.version_label,
                'selected': 'selected' if is_current else ''})
            if is_current:
                if a_version.is_transition and a_version.version_name == '':
                    self.additional_title = 'Transition'
                else:
                    self.additional_title = a_version.version_label

        self.is_standard = True if self.version_name == '' else False

        super().__init__(*args, **kwargs)


def ordered_list(version_list):
    # List has to be ordered like this
    # Standard version first
    # Transition version second
    # and the particular versions ordered by version_label
    standard_vers = []
    particular_vers = []
    for version in version_list:
        if version.is_standard:
            standard_vers.append(version)
        else:
            particular_vers.append(version)

    return sorted(standard_vers, key=attrgetter("version_label")) + sorted(particular_vers,
                                                                           key=attrgetter("version_label"))


def find_version(current_version_name: str, current_transition: bool, list_of_version):

    for a_version in list_of_version:
        if a_version.version_name == current_version_name:
            if current_transition:
                if not a_version.is_standard:
                    return a_version.version_label
            else:
                if a_version.is_standard:
                    return a_version.version_label
    return None


def _is_current(a_version, form_version_name, form_transition):
    is_current = True if a_version.version_name == form_version_name and a_version.is_transition == form_transition else False
    return is_current


def _compute_url(a_version, offer_id):
    kwargs = {'education_group_year_id': offer_id}
    url_name = 'education_group_read'
    if a_version.is_transition:
        url_name = 'education_group_read_transition'

    if a_version.version_name:
        kwargs.update({'version_name': a_version.version_name})

    return reverse(url_name, kwargs=kwargs)
