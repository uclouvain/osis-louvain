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
from base.forms.education_group.common import CommonBaseForm, EducationGroupModelForm, EducationGroupYearModelForm
from base.models.enums import education_group_categories
from django.utils.translation import ugettext_lazy as _

from base.models.enums.education_group_categories import Categories


class GroupYearModelForm(EducationGroupYearModelForm):
    category = Categories.GROUP.name
    category_text = Categories.GROUP.value

    class Meta(EducationGroupYearModelForm.Meta):
        fields = (
            "acronym",
            "partial_acronym",
            "education_group_type",
            "title",
            "title_english",
            "credits",
            "main_teaching_campus",
            "academic_year",
            "remark",
            "remark_english",
            "min_constraint",
            "max_constraint",
            "constraint_type",
            "management_entity"
        )


class GroupModelForm(EducationGroupModelForm):
    """ For groups, it is forbidden to update data about education_group """
    category = education_group_categories.GROUP


class GroupForm(CommonBaseForm):
    education_group_year_form_class = GroupYearModelForm
    education_group_form_class = GroupModelForm
