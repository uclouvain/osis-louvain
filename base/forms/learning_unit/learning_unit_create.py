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
import re

from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.utils.functional import lazy, cached_property
from django.utils.translation import gettext_lazy as _

from base.business.learning_units.edition import update_partim_acronym
from base.forms.learning_unit.entity_form import find_additional_requirement_entities_choices, \
    EntitiesVersionChoiceField
from base.forms.utils.acronym_field import AcronymField, PartimAcronymField, split_acronym
from base.forms.utils.choice_field import add_blank, add_all
from base.models.campus import find_main_campuses
from base.models.entity_version import find_pedagogical_entities_version, get_last_version
from base.models.enums import learning_unit_year_subtypes
from base.models.enums.entity_container_year_link_type import REQUIREMENT_ENTITIES
from base.models.enums.learning_container_year_types import LEARNING_CONTAINER_YEAR_TYPES_FOR_FACULTY, EXTERNAL, \
    LCY_TYPES_WITH_FIXED_ACRONYM
from base.models.enums.learning_container_year_types import LEARNING_CONTAINER_YEAR_TYPES_WITHOUT_EXTERNAL, INTERNSHIP
from base.models.enums.learning_unit_external_sites import LearningUnitExternalSite
from base.models.enums.learning_unit_year_subtypes import FULL, PARTIM
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_container import LearningContainer
from base.models.learning_container_year import LearningContainerYear
from base.models.learning_unit import LearningUnit, REGEX_BY_SUBTYPE
from base.models.learning_unit_year import LearningUnitYear, MAXIMUM_CREDITS
from osis_common.forms.widgets import DecimalFormatInput
from reference.models.country import Country
from reference.models.language import Language
from rules_management.mixins import PermissionFieldMixin

CRUCIAL_YEAR_FOR_CREDITS_VALIDATION = 2018


def _create_learning_container_year_type_list():
    return add_blank(LEARNING_CONTAINER_YEAR_TYPES_WITHOUT_EXTERNAL)


def _create_faculty_learning_container_type_list():
    return add_blank(LEARNING_CONTAINER_YEAR_TYPES_FOR_FACULTY)


class LearningUnitModelForm(forms.ModelForm):

    def save(self, **kwargs):
        self.instance.learning_container = kwargs.pop('learning_container')
        self.instance.start_year = kwargs.pop('start_year')
        self.instance.end_year = kwargs.pop('end_year', None)
        return super().save(**kwargs)

    class Meta:
        model = LearningUnit
        fields = ('faculty_remark', 'other_remark')
        widgets = {
            'faculty_remark': forms.Textarea(attrs={'rows': '5'}),
            'other_remark': forms.Textarea(attrs={'rows': '5'})
        }


# TODO Is it really useful ?
class LearningContainerModelForm(forms.ModelForm):
    class Meta:
        model = LearningContainer
        fields = ()


class LearningUnitYearModelForm(PermissionFieldMixin, forms.ModelForm):

    def __init__(self, data, person, subtype, *args, external=False, **kwargs):
        self.person = person
        self.user = self.person.user
        super().__init__(data, *args, **kwargs)

        self.external = external
        self.instance.subtype = subtype

        acronym = self.initial.get('acronym')
        if acronym:
            self.initial['acronym'] = split_acronym(acronym, subtype, instance=self.instance)

        if subtype == learning_unit_year_subtypes.PARTIM:
            type_str = _('Specific complement (Partim)')
            self.fields['acronym'] = PartimAcronymField()
            self.fields['specific_title'].label = type_str
            self.fields['specific_title_english'].label = type_str
        else:
            type_str = _('Specific complement (Full)')
            self.fields['specific_title'].label = type_str
            self.fields['specific_title_english'].label = type_str

        # Disabled fields when it's an update
        if self.instance.pk:
            self.fields['academic_year'].disabled = True

            # we cannot edit the internship subtype if the container_type is not internship
            if 'internship_subtype' in self.fields and \
                    self.instance.learning_container_year.container_type != INTERNSHIP:
                self.fields['internship_subtype'].disabled = True

        if not external:
            self.fields['campus'].queryset = find_main_campuses()
        self.fields['language'].queryset = Language.objects.all().order_by('name')

    class Meta:
        model = LearningUnitYear
        fields = ('academic_year', 'acronym', 'specific_title', 'specific_title_english', 'credits',
                  'session', 'quadrimester', 'status', 'internship_subtype', 'attribution_procedure',
                  'professional_integration', 'campus', 'language', 'periodicity')
        field_classes = {'acronym': AcronymField}
        error_messages = {
            'credits': {
                # Override unwanted DecimalField standard error messages
                'max_digits': _('Ensure this value is less than or equal to %(limit_value)s.') % {
                    'limit_value': MAXIMUM_CREDITS
                },
                'max_whole_digits': _('Ensure this value is less than or equal to %(limit_value)s.') % {
                    'limit_value': MAXIMUM_CREDITS
                }
            }
        }
        widgets = {
            'credits': DecimalFormatInput(render_value=True),
        }

    def __clean_acronym_external(self):
        acronym = self.data["acronym_0"] if "acronym_0" in self.data else LearningUnitExternalSite.E.value
        if not self.instance.subtype == PARTIM:
            acronym = acronym + self.data["acronym_1"]
        else:
            acronym = acronym + self.data["acronym_1"] + self.data["acronym_2"]
        acronym = acronym.upper()
        if not re.match(REGEX_BY_SUBTYPE[EXTERNAL], acronym) and self.instance.subtype == FULL:
            raise ValidationError(_('Invalid code'))
        if not re.match(REGEX_BY_SUBTYPE[PARTIM], acronym) and self.instance.subtype == PARTIM:
            raise ValidationError(_('Invalid code'))
        return acronym

    def clean_acronym(self):
        if self.external:
            self.cleaned_data["acronym"] = self.__clean_acronym_external()
        elif not self.external and not re.match(REGEX_BY_SUBTYPE[self.instance.subtype], self.cleaned_data["acronym"]):
            raise ValidationError(_('Invalid code'))
        return self.cleaned_data["acronym"]

    def post_clean(self, container_type):
        if "internship_subtype" in self.fields \
                and container_type != INTERNSHIP \
                and self.instance.internship_subtype:
            self.add_error("internship_subtype", _("This field cannot be set"))

        return not self.errors

    # TODO :: Move assignment to self.instance from save into __init__
    # TODO :: Make these kwarg to args (learning_container_year, learning_unit, ... are required args)
    def save(self, **kwargs):
        self.instance.learning_container_year = kwargs.pop('learning_container_year')
        self.instance.academic_year = self.instance.learning_container_year.academic_year
        self.instance.learning_unit = kwargs.pop('learning_unit')
        instance = super().save(**kwargs)
        if self.instance.learning_container_year.container_type not in LCY_TYPES_WITH_FIXED_ACRONYM:
            update_partim_acronym(instance.acronym, instance)
        return instance

    def clean_credits(self):
        credits_ = self.cleaned_data['credits']
        if self.instance.id is None or self.instance.academic_year.year >= CRUCIAL_YEAR_FOR_CREDITS_VALIDATION:
            if not float(credits_).is_integer():
                raise ValidationError(_('The credits value should be an integer'))
        return credits_


class CountryEntityField(forms.ChoiceField):
    def __init__(self, *args, widget_attrs=None, **kwargs):
        kwargs.update(
            choices=lazy(CountryEntityField._get_section_choices, list),
            required=False,
            label=_("Country"),
        )
        super(CountryEntityField, self).__init__(*args, **kwargs)
        if widget_attrs:
            self.widget.attrs.update(**widget_attrs)

    @staticmethod
    def _get_section_choices():
        return add_blank(
            add_all(Country.objects.filter(entity__isnull=False).values_list('id', 'name').distinct().order_by('name')),
            blank_choice_display="UCLouvain"
        )


class LearningContainerYearModelForm(PermissionFieldMixin, forms.ModelForm):
    # TODO :: Refactor code redundant code below for entity fields (requirement - allocation - additionnals)
    requirement_entity = EntitiesVersionChoiceField(
        widget=autocomplete.ModelSelect2(
            url='entity_requirement_autocomplete',
            attrs={
                'id': 'id_requirement_entity',
                'data-html': True,
                'onchange': (
                    'updateAdditionalEntityEditability(this.value, "id_additional_requirement_entity_1", false);'
                    'updateAdditionalEntityEditability(this.value, "id_additional_entity_1_country", false);'
                    'updateAdditionalEntityEditability(this.value, "id_additional_requirement_entity_2", true);'
                    'updateAdditionalEntityEditability(this.value, "id_additional_entity_2_country", true);'
                ),
            },
            forward=['country_requirement_entity']
        ),
        queryset=find_pedagogical_entities_version(),
        label=_('Requirement entity')
    )

    country_requirement_entity = CountryEntityField()

    allocation_entity = EntitiesVersionChoiceField(
        widget=autocomplete.ModelSelect2(
            url='allocation_entity_autocomplete',
            attrs={
                'id': 'allocation_entity',
                'data-html': True,
            },
            forward=['country_allocation_entity']
        ),
        queryset=find_pedagogical_entities_version(),
        label=_('Allocation entity')
    )

    country_allocation_entity = CountryEntityField()

    additional_entity_1 = EntitiesVersionChoiceField(
        required=False,
        widget=autocomplete.ModelSelect2(
            url='additional_entity_1_autocomplete',
            attrs={
                'id': 'id_additional_requirement_entity_1',
                'data-html': True,
                'onchange': (
                    'updateAdditionalEntityEditability(this.value, "id_additional_requirement_entity_2", false);'
                    'updateAdditionalEntityEditability(this.value, "id_additional_entity_2_country", false);'
                    'updateAdditionalEntityEditability(this.value, '
                    '"id_component-0-repartition_volume_additional_entity_1",'
                    ' false);'
                    'updateAdditionalEntityEditability(this.value, '
                    '"id_component-1-repartition_volume_additional_entity_1",'
                    ' false);'
                    'updateAdditionalEntityEditability(this.value,'
                    ' "id_component-0-repartition_volume_additional_entity_2",'
                    ' true);'
                    'updateAdditionalEntityEditability(this.value,'
                    ' "id_component-1-repartition_volume_additional_entity_2",'
                    ' true);'
                ),
            },
            forward=['country_additional_entity_1']
        ),
        queryset=find_additional_requirement_entities_choices(),
        label=_('Additional requirement entity 1')
    )

    country_additional_entity_1 = CountryEntityField(
        widget_attrs={'id': 'id_additional_entity_1_country'}
    )

    additional_entity_2 = EntitiesVersionChoiceField(
        required=False,
        widget=autocomplete.ModelSelect2(
            url='additional_entity_2_autocomplete',
            attrs={
                'id': 'id_additional_requirement_entity_2',
                'data-html': True,
                'onchange': (
                    'updateAdditionalEntityEditability(this.value,'
                    ' "id_component-0-repartition_volume_additional_entity_2", false);'
                    'updateAdditionalEntityEditability(this.value,'
                    ' "id_component-1-repartition_volume_additional_entity_2", false);'
                ),
            },
            forward=['country_additional_entity_2']
        ),
        queryset=find_additional_requirement_entities_choices(),
        label=_('Additional requirement entity 2')
    )

    country_additional_entity_2 = CountryEntityField(
        widget_attrs={'id': 'id_additional_entity_2_country'}
    )

    def __init__(self, *args, **kwargs):
        self.person = kwargs.pop('person')
        self.user = self.person.user
        self.proposal = kwargs.pop('proposal', False)
        self.is_create_form = kwargs['instance'] is None
        super().__init__(*args, **kwargs)
        self.fields['requirement_entity'].queryset = self.person.find_main_entities_version
        self.prepare_fields()
        self.fields['common_title'].label = _('Common part')
        self.fields['common_title_english'].label = _('Common part')

        if self.instance.requirement_entity:
            self.initial['requirement_entity'] = get_last_version(self.instance.requirement_entity).pk

        if self.instance.allocation_entity:
            self.initial['allocation_entity'] = get_last_version(self.instance.allocation_entity).pk

        if self.instance.additional_entity_1:
            self.initial['additional_entity_1'] = get_last_version(self.instance.additional_entity_1).pk

        if self.instance.additional_entity_2:
            self.initial['additional_entity_2'] = get_last_version(self.instance.additional_entity_2).pk

    def prepare_fields(self):
        self.fields['container_type'].widget.attrs = {'onchange': 'showInternshipSubtype()'}

        # Limit types for faculty_manager only if simple creation of learning_unit
        if self.person.is_faculty_manager and not self.proposal and self.is_create_form:
            self.fields["container_type"].choices = _create_faculty_learning_container_type_list()
        else:
            self.fields["container_type"].choices = _create_learning_container_year_type_list()

    def save(self, **kwargs):
        self.instance.learning_container = kwargs.pop('learning_container')
        self.instance.acronym = kwargs.pop('acronym')
        self.instance.academic_year = kwargs.pop('academic_year')
        self._reset_repartition_volumes_if_entity_removed()
        return super().save(**kwargs)

    def _reset_repartition_volumes_if_entity_removed(self):
        """In case an Entity was removed from container, need to reset repartition volume of this entity to None."""
        for entity_link_type in REQUIREMENT_ENTITIES:
            entity_container_attr = self.instance.get_attrs_by_entity_container_type()[entity_link_type]
            entity = getattr(self.instance, entity_container_attr, None)
            if entity_container_attr in self.changed_data and not entity:
                repartition_attr_by_type = LearningComponentYear.repartition_volume_attrs_by_entity_container_type()
                attr_name = repartition_attr_by_type[entity_link_type]
                qs = LearningComponentYear.objects.filter(
                    learning_unit_year__learning_container_year=self.instance)
                qs.update(**{attr_name: None})

    class Meta:
        model = LearningContainerYear
        fields = (
            'container_type',
            'common_title',
            'common_title_english',
            'type_declaration_vacant',
            'team',
            'is_vacant',
            'requirement_entity',
            'allocation_entity',
            'additional_entity_1',
            'additional_entity_2',
        )

    def post_clean(self, specific_title):
        if not self.instance.common_title and not specific_title:
            self.add_error("common_title", _("You must either set the common title or the specific title"))

        return not self.errors

    @cached_property
    def additionnal_entity_version_1(self):
        return self.fields["additional_entity_1"].entity_version

    @cached_property
    def additionnal_entity_version_2(self):
        return self.fields["additional_entity_2"].entity_version
