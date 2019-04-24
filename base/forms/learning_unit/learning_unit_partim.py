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
from django.http import QueryDict
from django.utils.translation import gettext_lazy as _

from base.business.utils.model import merge_two_dicts
from base.forms.learning_unit.edition_volume import SimplifiedVolumeManagementForm
from base.forms.learning_unit.entity_form import EntityContainerBaseForm
from base.forms.learning_unit.learning_unit_create import LearningUnitYearModelForm, \
    LearningContainerYearModelForm, LearningContainerModelForm, \
    LearningUnitModelForm
from base.forms.learning_unit.learning_unit_create_2 import LearningUnitBaseForm
from base.forms.utils.acronym_field import split_acronym
from base.forms.utils.choice_field import add_blank
from base.models.academic_year import current_academic_year, LEARNING_UNIT_CREATION_SPAN_YEARS
from base.models.entity_container_year import EntityContainerYear
from base.models.enums import learning_unit_year_subtypes
from base.models.enums.learning_unit_year_subtypes import FULL
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_unit import LearningUnit

PARTIM_FORM_READ_ONLY_FIELD = {
    'acronym_0', 'acronym_1', 'common_title', 'common_title_english',
    'requirement_entity', 'allocation_entity',
    'academic_year', 'container_type', 'internship_subtype',
    'additional_requirement_entity_1', 'additional_requirement_entity_2'
}


class YearChoiceField(forms.ChoiceField):
    def __init__(self, *args, start_year=None, end_year=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not start_year:
            start_year = current_academic_year().year

        if not end_year:
            end_year = start_year + LEARNING_UNIT_CREATION_SPAN_YEARS

        self.choices = [(year, self.academic_year_str(year)) for year in range(start_year, end_year + 1)]
        self.choices = add_blank(self.choices)

    @staticmethod
    def academic_year_str(year):
        return "{}-{}".format(year, str(year + 1)[-2:])

    def clean(self, value):
        value = super().clean(value)
        #
        return value if value else None


class LearningUnitPartimModelForm(LearningUnitModelForm):
    def __init__(self, *args, start_year, max_end_year, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['end_year'] = YearChoiceField(start_year=start_year, end_year=max_end_year, required=False,
                                                  label=_('End year'))

    class Meta(LearningUnitModelForm.Meta):
        fields = ('faculty_remark', 'other_remark', 'end_year')


def merge_data(data, inherit_lu_values):
    if isinstance(data, QueryDict):
        data = data.dict()
    return merge_two_dicts(data, inherit_lu_values) if data else None


class PartimForm(LearningUnitBaseForm):
    subtype = learning_unit_year_subtypes.PARTIM

    form_cls = [
        LearningUnitPartimModelForm,
        LearningUnitYearModelForm,
        LearningContainerModelForm,
        LearningContainerYearModelForm,
        EntityContainerBaseForm,
        SimplifiedVolumeManagementForm
    ]

    form_cls_to_validate = [LearningUnitPartimModelForm, LearningUnitYearModelForm, SimplifiedVolumeManagementForm]

    def __init__(self, person, learning_unit_full_instance, academic_year, learning_unit_instance=None,
                 data=None, *args, **kwargs):
        if not isinstance(learning_unit_full_instance, LearningUnit):
            raise AttributeError('learning_unit_full arg should be an instance of {}'.format(LearningUnit))
        if learning_unit_instance is not None and not isinstance(learning_unit_instance, LearningUnit):
            raise AttributeError('learning_unit_partim_instance arg should be an instance of {}'.format(LearningUnit))
        self.person = person
        self.academic_year = academic_year
        self.learning_unit_full_instance = learning_unit_full_instance
        self.learning_unit_instance = learning_unit_instance

        self.learning_unit_year_full = self.learning_unit_full_instance.learningunityear_set.filter(
            academic_year=self.academic_year,
            subtype=FULL,
        ).get()

        # Inherit values cannot be changed by user
        inherit_luy_values = self._get_inherit_learning_unit_year_full_value()
        instances_data = self._build_instance_data(data, inherit_luy_values)

        super().__init__(instances_data, *args, **kwargs)
        self.disable_fields(PARTIM_FORM_READ_ONLY_FIELD)

    @property
    def learning_unit_form(self):
        return self.forms[LearningUnitPartimModelForm]

    def _build_instance_data(self, data, inherit_luy_values):
        return {
            LearningUnitPartimModelForm: self._build_instance_data_learning_unit(data),
            LearningUnitYearModelForm: self._build_instance_data_learning_unit_year(data, inherit_luy_values),
            # Cannot be modify by user [No DATA args provided]
            LearningContainerModelForm: {
                'instance': self.learning_unit_year_full.learning_container_year.learning_container,
            },
            LearningContainerYearModelForm: {
                'instance': self.learning_unit_year_full.learning_container_year,
                'person': self.person
            },
            EntityContainerBaseForm: {
                'learning_container_year': self.learning_unit_year_full.learning_container_year,
                'person': self.person
            },
            SimplifiedVolumeManagementForm: {
                'data': data,
                'queryset': LearningComponentYear.objects.filter(
                    learning_unit_year=self.instance)
                if self.instance else LearningComponentYear.objects.none(),
                'person': self.person,
            }
        }

    def _build_instance_data_learning_unit_year(self, data, inherit_luy_values):
        return {
            'data': merge_data(data, inherit_luy_values),
            'instance': self.instance,
            'initial': self._get_initial_learning_unit_year_form() if not self.instance else None,
            'person': self.person,
            'subtype': self.subtype
        }

    def _build_instance_data_learning_unit(self, data):
        return {
            'data': data,
            'instance': self.instance.learning_unit if self.instance else None,
            'start_year': self.learning_unit_year_full.academic_year.year,
            'max_end_year': self.learning_unit_year_full.learning_unit.max_end_year
        }

    def _get_inherit_learning_unit_year_full_value(self):
        """This function will return the inherit value come from learning unit year FULL"""
        return {field: value for field, value in self._get_initial_learning_unit_year_form().items()
                if field in PARTIM_FORM_READ_ONLY_FIELD}

    def _get_initial_learning_unit_year_form(self):
        acronym = self.instance.acronym if self.instance else self.learning_unit_year_full.acronym
        initial_learning_unit_year = {
            'acronym': acronym,
            'academic_year': self.learning_unit_year_full.academic_year.id,
            'internship_subtype': self.learning_unit_year_full.internship_subtype,
            'attribution_procedure': self.learning_unit_year_full.attribution_procedure,
            'subtype': self.subtype,
            'credits': self.learning_unit_year_full.credits,
            'session': self.learning_unit_year_full.session,
            'quadrimester': self.learning_unit_year_full.quadrimester,
            'status': self.learning_unit_year_full.status,
            'specific_title': self.learning_unit_year_full.specific_title,
            'specific_title_english': self.learning_unit_year_full.specific_title_english,
            'language': self.learning_unit_year_full.language,
            'campus': self.learning_unit_year_full.campus,
            'periodicity': self.learning_unit_year_full.periodicity
        }
        acronym_splited = split_acronym(acronym)
        initial_learning_unit_year.update({
            "acronym_{}".format(idx): acronym_part for idx, acronym_part in enumerate(acronym_splited)
        })
        return initial_learning_unit_year

    def save(self, commit=True):
        start_year = self.instance.learning_unit.start_year if self.instance else \
            self.learning_unit_full_instance.start_year

        lcy = self.learning_unit_year_full.learning_container_year
        # Save learning unit
        learning_unit = self.learning_unit_form.save(
            start_year=start_year,
            learning_container=lcy.learning_container,
            commit=commit
        )

        # Save learning unit year
        learning_unit_yr = self.learning_unit_year_form.save(
            learning_container_year=lcy,
            learning_unit=learning_unit,
            commit=commit
        )

        self.simplified_volume_management_form.save_all_forms(
            learning_unit_yr,
            EntityContainerYear.objects.filter(learning_container_year=lcy),
            commit=commit
        )

        return learning_unit_yr

    def _get_entity_container_year(self):
        return self.learning_unit_year_full.learning_container_year.entitycontaineryear_set.all()
