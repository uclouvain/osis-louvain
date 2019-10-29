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

from base.business.education_groups import shorten
from base.business.education_groups.postponement import PostponementEducationGroupYearMixin
from base.forms.education_group.common import CommonBaseForm, EducationGroupModelForm, EducationGroupYearModelForm
from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_categories
from base.models.enums.education_group_categories import Categories


class MiniTrainingYearModelForm(EducationGroupYearModelForm):
    category = Categories.MINI_TRAINING.name
    category_text = Categories.MINI_TRAINING.value

    class Meta(EducationGroupYearModelForm.Meta):
        model = EducationGroupYear
        fields = (
            "acronym", "partial_acronym",
            "education_group_type", "title", "title_english",
            "credits", "active", "main_teaching_campus",
            "academic_year", "remark", "remark_english",
            "min_constraint", "max_constraint", "constraint_type",
            "schedule_type", "management_entity", "keywords"
        )
        widgets = {
            "credits": forms.TextInput(),
            "min_constraint": forms.TextInput(),
            "max_constraint": forms.TextInput(),
        }


class MiniTrainingModelForm(EducationGroupModelForm):
    category = education_group_categories.MINI_TRAINING


class MiniTrainingForm(PostponementEducationGroupYearMixin, CommonBaseForm):
    education_group_year_form_class = MiniTrainingYearModelForm
    education_group_form_class = MiniTrainingModelForm

    def _post_save(self):
        education_group_instance = self.forms[EducationGroupModelForm].instance
        egy_deleted = []
        if education_group_instance.end_year:
            egy_deleted = shorten.start(education_group_instance, education_group_instance.end_year)

        return {
            'object_list_deleted': egy_deleted
        }
