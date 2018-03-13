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

from django.utils.translation import ugettext_lazy as _

COURSE = "COURSE"
INTERNSHIP = "INTERNSHIP"
DISSERTATION = "DISSERTATION"
OTHER_COLLECTIVE = "OTHER_COLLECTIVE"
OTHER_INDIVIDUAL = "OTHER_INDIVIDUAL"
MASTER_THESIS = "MASTER_THESIS"
EXTERNAL = "EXTERNAL"

LEARNING_CONTAINER_YEAR_TYPES_MUST_HAVE_SAME_ENTITIES = [
    MASTER_THESIS,
    INTERNSHIP,
    DISSERTATION
]

LEARNING_CONTAINER_YEAR_TYPES = (
    (COURSE, _(COURSE)),
    (INTERNSHIP, _(INTERNSHIP)),
    (DISSERTATION, _(DISSERTATION)),
    (OTHER_COLLECTIVE, _(OTHER_COLLECTIVE)),
    (OTHER_INDIVIDUAL, _(OTHER_INDIVIDUAL)),
    (MASTER_THESIS, _(MASTER_THESIS)),
    (EXTERNAL, _(EXTERNAL)),
)

LEARNING_CONTAINER_YEAR_TYPES_FOR_FACULTY = (
    (OTHER_COLLECTIVE, _(OTHER_COLLECTIVE)),
    (OTHER_INDIVIDUAL, _(OTHER_INDIVIDUAL)),
    (MASTER_THESIS, _(MASTER_THESIS)),
)

LEARNING_CONTAINER_YEAR_TYPES_FOR_PROPOSAL_FACULTY = (
    (COURSE, _(COURSE)),
    (INTERNSHIP, _(INTERNSHIP)),
    (DISSERTATION, _(DISSERTATION)),
)
