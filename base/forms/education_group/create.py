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
from django import forms

from base.forms.learning_unit.entity_form import EntitiesVersionChoiceField
from base.models import campus, education_group_type
from base.models.education_group import EducationGroup
from base.models.education_group_year import EducationGroupYear
from base.models.entity_version import find_main_entities_version
from base.models.enums import offer_year_entity_type, education_group_categories
from base.models.group_element_year import GroupElementYear
from base.models.offer_year_entity import OfferYearEntity
from django.utils.translation import ugettext_lazy as _


class CreateEducationGroupYearForm(forms.ModelForm):

    class Meta:
        model = EducationGroupYear
        fields = ("acronym", "partial_acronym", "education_group_type", "title", "title_english", "credits",
                  "main_teaching_campus", "academic_year", "remark", "remark_english", "min_credits", "max_credits")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["main_teaching_campus"].queryset = campus.find_main_campuses()
        self.fields["education_group_type"].queryset = \
            education_group_type.find_by_category(education_group_categories.GROUP)

    def save(self, parent=None):
        education_group_year = super().save(commit=False)
        education_group_year.education_group = self._create_education_group()
        education_group_year.save()

        if parent:
            self._create_group_element_year(parent, education_group_year)

        return education_group_year

    def _create_education_group(self):
        start_year = self.cleaned_data["academic_year"].year
        return EducationGroup.objects.create(start_year=start_year)

    @staticmethod
    def _create_group_element_year(parent, child):
        return GroupElementYear.objects.create(parent=parent, child_branch=child)


class CreateOfferYearEntityForm(forms.ModelForm):

    class Meta:
        model = OfferYearEntity
        fields = ("entity", )
        field_classes = {
            "entity": EntitiesVersionChoiceField
        }
        labels = {
            "entity": _("administration_entity")
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["entity"].queryset = find_main_entities_version()

    def save(self, education_group_year):
        offer_year_entity = super().save(commit=False)
        offer_year_entity.education_group_year = education_group_year
        offer_year_entity.type = offer_year_entity_type.ENTITY_ADMINISTRATION
        offer_year_entity.save()
        return offer_year_entity
