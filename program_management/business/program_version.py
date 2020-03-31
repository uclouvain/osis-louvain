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


class ProgramVersion:
    # Unfull to simplify usage of version in view/template

    version_label = None    # Used in dropdown in interface
    is_standard = False     # Used to define version_label and order for displaying version_label in interface
    version_name = None
    offer = None

    transition_url = '-'    # Used to build url 'education_group_read' education_group_id version_name transition.
                            # Example : http://127.0.0.1:8000/educationgroups/40324/CEMS/transition/identification/
    version_name_url = '-'  # Used to build url 'education_group_read' education_group_id version_name transition

    def __init__(self, version_name: str, offer: int, is_transition: bool):
        self.offer = offer
        self.is_standard = True if version_name == '' else False
        self.transition_url = 'transition' if is_transition else '-'
        if self.is_standard:
            self.version_label = 'Transition'.format(version_name) if is_transition else 'Standard'
        else:
            self.version_label = '{}-Transition'.format(version_name) if is_transition else version_name

        self.version_name = version_name
        self.version_name_url = version_name if version_name != '' else '-'

    def __str__(self):
        "Convert to string, for str()."
        return "{} {}".format(self.version_name, self.version_label)


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


def build_list_from_ddd_version_list(ddd_version_list, offer):
    version_list = []
    for v in ddd_version_list:
        version_list.append(ProgramVersion(v.version_name, offer, v.is_transition))
    return version_list
