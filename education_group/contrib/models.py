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
from django.db import models

from base.models.education_group import EducationGroup
from base.models.education_group_year import EducationGroupYear
from osis_role.contrib.models import RoleModel


class EducationGroupRoleModel(RoleModel):
    education_group = models.ForeignKey(EducationGroup, on_delete=models.CASCADE)

    class Meta:
        abstract = True
        unique_together = ('person', 'education_group',)

    @classmethod
    def get_person_related_education_groups(cls, person):
        return cls.objects.filter(person=person).values_list('education_group_id', flat=True)


class EducationGroupYearRoleModel(RoleModel):
    education_group_year = models.ForeignKey(EducationGroupYear, on_delete=models.CASCADE)

    class Meta:
        abstract = True
        unique_together = ('person', 'education_group_year',)

    @classmethod
    def get_person_related_education_group_years(cls, person):
        return cls.objects.filter(person=person).values_list('education_group_year_id', flat=True)
