##############################################################################
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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import attr

from osis_common.ddd import interface


@attr.s(frozen=True, slots=True)
class CreateLearningUnitCommand(interface.CommandRequest):
    code = attr.ib(type=str)
    academic_year = attr.ib(type=int)
    type = attr.ib(type=str)
    common_title_fr = attr.ib(type=str)
    specific_title_fr = attr.ib(type=str)
    common_title_en = attr.ib(type=str)
    specific_title_en = attr.ib(type=str)
    credits = attr.ib(type=int)
    internship_subtype = attr.ib(type=str)
    responsible_entity_code = attr.ib(type=str)
    periodicity = attr.ib(type=str)
    iso_code = attr.ib(type=str)
    remark_faculty = attr.ib(type=str)
    remark_publication_fr = attr.ib(type=str)
    remark_publication_en = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class CreatePartimCommand(interface.CommandRequest):
    learning_unit_code = attr.ib(type=str)
    learning_unit_year = attr.ib(type=int)
    subdivision = attr.ib(type=int)
    title_fr = attr.ib(type=str)
    title_en = attr.ib(type=str)
    credits = attr.ib(type=int)
    periodicity = attr.ib(type=str)
    iso_code = attr.ib(type=str)
    remark_faculty = attr.ib(type=str)
    remark_publication_fr = attr.ib(type=str)
    remark_publication_en = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class DeleteLearningUnitCommand(interface.CommandRequest):
    code = attr.ib(type=str)
    academic_year = attr.ib(type=int)


@attr.s(frozen=True, slots=True)
class CopyLearningUnitToNextYearCommand(interface.CommandRequest):
    copy_from_code = attr.ib(type=str)
    copy_from_year = attr.ib(type=int)


@attr.s(frozen=True, slots=True)
class CreateCommand(interface.CommandRequest):
    copy_from_code = attr.ib(type=str)
    copy_from_year = attr.ib(type=int)


@attr.s(frozen=True, slots=True)
class LearningUnitSearchCommand(interface.CommandRequest):
    code = attr.ib(type=str)
    year = attr.ib(type=int)
    type = attr.ib(type=str)
    full_title = attr.ib(type=str)
    responsible_entity_code = attr.ib(type=str)
