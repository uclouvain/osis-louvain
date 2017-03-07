##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.db import models


class MandateStructure(models.Model):
    assistant_mandate = models.ForeignKey('AssistantMandate')
    structure = models.ForeignKey('base.Structure')

    @property
    def name(self):
        return self.__str__()

    def __str__(self):
        return u"%s - %s" % (self.assistant_mandate.assistant, self.structure.acronym)


def find_by_mandate(mandate):
    return MandateStructure.objects.filter(assistant_mandate=mandate)


def find_by_mandate_and_structure(mandate, structure):
    return MandateStructure.objects.filter(assistant_mandate=mandate, structure=structure)


def find_by_mandate_and_type(mandate, type):
    return MandateStructure.objects.filter(assistant_mandate=mandate, structure__type=type)


def find_by_mandate_and_part_of_type(mandate, type):
    return MandateStructure.objects.filter(assistant_mandate=mandate, structure__part_of__type=type)


def find_by_mandate_and_part_of_struct(mandate, struct):
    return MandateStructure.objects.filter(assistant_mandate=mandate, structure__part_of=struct)


def find_by_structures_for_academic_year(structures, academic_year):
    return MandateStructure.objects.filter(structure__in=structures).\
        filter(assistant_mandate__academic_year=academic_year).distinct()
