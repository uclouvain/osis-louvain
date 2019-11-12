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

from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum

COURSE = "COURSE"
INTERNSHIP = "INTERNSHIP"
DISSERTATION = "DISSERTATION"
OTHER_COLLECTIVE = "OTHER_COLLECTIVE"
OTHER_INDIVIDUAL = "OTHER_INDIVIDUAL"
MASTER_THESIS = "MASTER_THESIS"
EXTERNAL = "EXTERNAL"

LEARNING_CONTAINER_YEAR_TYPES_FOR_FACULTY = (
    (OTHER_COLLECTIVE, _("Other collective")),
    (OTHER_INDIVIDUAL, _("Other individual")),
    (MASTER_THESIS, _("Thesis")),
)


class LearningContainerYearType(ChoiceEnum):
    COURSE = _("Course")
    INTERNSHIP = _("Internship")
    DISSERTATION = _("Dissertation")
    OTHER_COLLECTIVE = _("Other collective")
    OTHER_INDIVIDUAL = _("Other individual")
    MASTER_THESIS = _("Thesis")
    EXTERNAL = _("External")

    @classmethod
    def for_faculty(cls) -> tuple:
        return cls.OTHER_COLLECTIVE.name, cls.OTHER_INDIVIDUAL.name, cls.MASTER_THESIS.name, cls.INTERNSHIP.name


LEARNING_CONTAINER_YEAR_TYPES_CANT_UPDATE_BY_FACULTY = [COURSE, INTERNSHIP, DISSERTATION]

LEARNING_CONTAINER_YEAR_TYPES_WITHOUT_EXTERNAL = LearningContainerYearType.choices()[:-1]

CONTAINER_TYPE_WITH_DEFAULT_COMPONENT = [COURSE, MASTER_THESIS, OTHER_COLLECTIVE, INTERNSHIP, EXTERNAL]

TYPE_ALLOWED_FOR_ATTRIBUTIONS = (OTHER_COLLECTIVE, OTHER_INDIVIDUAL, MASTER_THESIS, INTERNSHIP, EXTERNAL, DISSERTATION)

CONTAINER_TYPES_CREATION_PROPOSAL = (
    (COURSE, _("Course")),
    (DISSERTATION, _("Dissertation")),
    (INTERNSHIP, _("Internship"))
)
