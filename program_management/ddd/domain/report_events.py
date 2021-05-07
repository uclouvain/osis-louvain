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
from typing import List

import attr
from django.utils.translation import gettext_lazy as _

from education_group.ddd.domain.exception import common_postponement_consistency_message
from program_management.ddd.domain.academic_year import AcademicYear
from program_management.ddd.domain.report import ReportEvent
from program_management.ddd.business_types import *


@attr.s(frozen=True, slots=True)
class CopyLearningUnitNotExistForYearEvent(ReportEvent):
    code = attr.ib(type=str)
    copy_year = attr.ib(type=int)
    year = attr.ib(type=int)

    def __str__(self):
        return _("LU %(code)s does not exist in %(copy_year)s. LU is copied with %(year)s as year of reference.") % {
            "code": self.code,
            "copy_year": self.copy_year,
            "year": self.year
        }


@attr.s(frozen=True, slots=True)
class NotCopyTrainingMiniTrainingNotExistForYearEvent(ReportEvent):
    node = attr.ib(type='NodeGroupYear')
    end_year = attr.ib(type=AcademicYear)
    copy_year = attr.ib(type=AcademicYear)

    def __str__(self):
        return _(
            "Training/Mini-Training %(title)s is closed in %(end_year)s. "
            "This training/mini-training is not copied in %(copy_year)s."
        ) % {
            "title": self.node.full_code_acronym_representation(),
            "copy_year": self.copy_year,
            "end_year": self.end_year
        }


@attr.s(frozen=True, slots=True)
class NotCopyTrainingMiniTrainingNotExistingEvent(ReportEvent):
    node = attr.ib(type='NodeGroupYear')
    copy_year = attr.ib(type=AcademicYear)

    def __str__(self):
        return _(
            "Training/Mini-Training %(title)s is inconsistent."
            "This training/mini-training is not copied in %(copy_year)s."
        ) % {
            "title": self.node.full_code_acronym_representation(),
            "copy_year": self.copy_year,
        }


@attr.s(frozen=True, slots=True)
class CopyTransitionTrainingNotExistingEvent(ReportEvent):
    node = attr.ib(type='NodeGroupYear')
    root_node = attr.ib(type='NodeGroupYear')

    def __str__(self):
        return _(
            "The transition version [%(version)s] of the training %(title)s does not exist in %(academic_year)s"
        ) % {
            "version": self.root_node.version_label(),
            "title": self.node.full_code_acronym_representation(),
            "academic_year": self.root_node.academic_year,
        }


@attr.s(frozen=True, slots=True)
class CopyReferenceGroupEvent(ReportEvent):
    node = attr.ib(type='NodeGroupYear')

    def __str__(self):
        return _("The reference group %(title)s has not yet been copied. Its content is still empty.") % {
            "title": self.node.full_code_acronym_representation(),
        }


@attr.s(frozen=True, slots=True)
class CopyReferenceEmptyEvent(ReportEvent):
    node = attr.ib(type='NodeGroupYear')

    def __str__(self):
        return _("The reference element %(title)s is still empty.") % {
            "title": self.node.full_code_acronym_representation(),
        }


@attr.s(frozen=True, slots=True)
class NodeAlreadyCopiedEvent(ReportEvent):
    node = attr.ib(type='NodeGroupYear')
    copy_year = attr.ib(type=AcademicYear)

    def __str__(self):
        return _(
            "The element %(title)s has already been copied in %(copy_year)s in the context of an other training."
            "Its content may have changed."
        ) % {
            "title": self.node.full_code_acronym_representation(),
            "copy_year": self.copy_year
        }


@attr.s(frozen=True, slots=True)
class CannotCopyPrerequisiteAsLearningUnitNotPresent(ReportEvent):
    prerequisite_code = attr.ib(type=str)
    learning_unit_code = attr.ib(type=str)
    training_root_node = attr.ib(type='NodeGroupYear')
    copy_year = attr.ib(type=AcademicYear)

    def __str__(self):
        return _(
            "The prerequisite of %(prerequisite_code)s is not copied in %(copy_year)s: %(learning_unit_code)s "
            "does not exist anymore in %(training_title)s in %(copy_year)s."
        ) % {
            "prerequisite_code": self.prerequisite_code,
            "learning_unit_code": self.learning_unit_code,
            "copy_year": self.copy_year,
            "training_title": self.training_root_node.full_code_acronym_representation()
        }


@attr.s(frozen=True, slots=True)
class CannotPostponeLinkToNextYearAsConsistencyError(ReportEvent):
    year = attr.ib(type=int)
    fields = attr.ib(type=List[str])

    def __str__(self):
        return common_postponement_consistency_message(self.year, self.fields)
