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
from collections import OrderedDict

from django import forms
from django.utils.translation import ugettext_lazy as _

from base.forms.utils.acronym_field import AcronymField, PartimAcronymField, split_acronym
from base.forms.utils.choice_field import add_blank
from base.models import entity_version
from base.models.campus import find_main_campuses
from base.models.entity_component_year import EntityComponentYear
from base.models.entity_container_year import EntityContainerYear
from base.models.entity_version import find_main_entities_version, get_last_version
from base.models.enums import learning_unit_year_subtypes
from base.models.enums.component_type import LECTURING, PRACTICAL_EXERCISES
from base.models.enums.entity_container_year_link_type import REQUIREMENT_ENTITY, ALLOCATION_ENTITY, \
    ADDITIONAL_REQUIREMENT_ENTITY_1, ADDITIONAL_REQUIREMENT_ENTITY_2, ENTITY_TYPE_LIST, REQUIREMENT_ENTITIES
from base.models.enums.learning_container_year_types import LEARNING_CONTAINER_YEAR_TYPES, \
    CONTAINER_TYPE_WITH_DEFAULT_COMPONENT, LEARNING_CONTAINER_YEAR_TYPES_MUST_HAVE_SAME_ENTITIES
from base.models.enums.learning_container_year_types import LEARNING_CONTAINER_YEAR_TYPES_FOR_FACULTY
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_container import LearningContainer
from base.models.learning_container_year import LearningContainerYear
from base.models.learning_unit import LearningUnit
from base.models.learning_unit_component import LearningUnitComponent
from base.models.learning_unit_year import LearningUnitYear

DEFAULT_ACRONYM_COMPONENT = {
    LECTURING: "CM1",
    PRACTICAL_EXERCISES: "TP1",
    None: "NT1"
}


def _get_default_components_type(container_type):
    """This function will return the default components type to create/update according to container type"""
    if container_type in CONTAINER_TYPE_WITH_DEFAULT_COMPONENT:
        return [LECTURING, PRACTICAL_EXERCISES]
    return [None]


def _create_learning_container_year_type_list():
    return add_blank(LEARNING_CONTAINER_YEAR_TYPES)


def _create_faculty_learning_container_type_list():
    return add_blank(LEARNING_CONTAINER_YEAR_TYPES_FOR_FACULTY)


class EntitiesVersionChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.acronym


class LearningUnitModelForm(forms.ModelForm):

    def save(self, **kwargs):
        self.instance.learning_container = kwargs.pop('learning_container')
        self.instance.start_year = kwargs.pop('start_year')
        return super(LearningUnitModelForm, self).save(**kwargs)

    class Meta:
        model = LearningUnit
        fields = ('periodicity', 'faculty_remark', 'other_remark', )
        widgets = {
            'faculty_remark': forms.Textarea(attrs={'rows': '5'}),
            'other_remark': forms.Textarea(attrs={'rows': '5'})
        }


# TODO Is it really useful ?
class LearningContainerModelForm(forms.ModelForm):
    class Meta:
        model = LearningContainer
        fields = ()


class LearningUnitYearModelForm(forms.ModelForm):
    _warnings = None

    def __init__(self, data, person, subtype, *args, **kwargs):
        super().__init__(data, *args, **kwargs)

        if person.is_faculty_manager():
            self.fields.pop('internship_subtype')

        self.instance.subtype = subtype

        acronym = self.initial.get('acronym')
        if acronym:
            self.initial['acronym'] = split_acronym(acronym, subtype)

        if subtype == learning_unit_year_subtypes.PARTIM:
            self.fields['acronym'] = PartimAcronymField()
            self.fields['specific_title'].label = _('official_title_proper_to_partim')
            self.fields['specific_title_english'].label = _('official_english_title_proper_to_partim')

        if kwargs.get('instance'):
            self.fields['academic_year'].disabled = True

    class Meta:
        model = LearningUnitYear
        fields = ('academic_year', 'acronym', 'specific_title', 'specific_title_english', 'credits',
                  'session', 'quadrimester', 'status', 'internship_subtype', 'attribution_procedure', )

        field_classes = {'acronym': AcronymField}

    # TODO :: Move assignment to self.instance from save into __init__
    # TODO :: Make these kwarg to args (learning_container_year, learning_unit, ... are required args)
    def save(self, **kwargs):
        self.instance.learning_container_year = kwargs.pop('learning_container_year')
        self.instance.academic_year = self.instance.learning_container_year.academic_year
        self.instance.learning_unit = kwargs.pop('learning_unit')
        entity_container_years = kwargs.pop('entity_container_years')
        instance = super().save(**kwargs)
        self._save_learning_components(entity_container_years, instance)
        return instance

    def _save_learning_components(self, entity_container_years, learning_unit_year):
        components_type = _get_default_components_type(self.instance.learning_container_year.container_type)
        for component_type in components_type:
            component, created = LearningComponentYear.objects.get_or_create(
                learningunitcomponent__learning_unit_year=learning_unit_year,
                type=component_type,
                defaults={
                    'acronym': DEFAULT_ACRONYM_COMPONENT[component_type],
                    'learning_container_year': learning_unit_year.learning_container_year
                }
            )
            self._save_learning_unit_component(component, learning_unit_year)
            self._save_entity_components_year(component, entity_container_years)

    @staticmethod
    def _save_learning_unit_component(component, learning_unit_year):
        return LearningUnitComponent.objects.get_or_create(learning_unit_year=learning_unit_year,
                                                           learning_component_year=component)

    @staticmethod
    def _save_entity_components_year(component, entity_container_years):
        requirement_entity_containers = filter(lambda ec: getattr(ec, 'type', None) in REQUIREMENT_ENTITIES,
                                               entity_container_years)
        for requirement_entity_container in requirement_entity_containers:
            EntityComponentYear.objects.get_or_create(entity_container_year=requirement_entity_container,
                                                      learning_component_year=component)

    @property
    def warnings(self):
        if self._warnings is None and self.instance:
            if hasattr(self.instance, 'warnings'):
                self._warnings = self.instance.warnings
        return self._warnings


class LearningUnitYearPartimModelForm(LearningUnitYearModelForm):
    class Meta(LearningUnitYearModelForm.Meta):
        labels = {
            'specific_title': _('official_title_proper_to_partim'),
            'specific_title_english': _('official_english_title_proper_to_partim')
        }
        field_classes = {
            'acronym': PartimAcronymField
        }


class EntityContainerYearModelForm(forms.ModelForm):
    entity = EntitiesVersionChoiceField(find_main_entities_version())
    entity_version = None
    entity_type = ''

    def __init__(self, *args, **kwargs):
        self.person = kwargs.pop('person')

        super().__init__(*args, prefix=self.entity_type.lower(), **kwargs)

        self.fields['entity'].label = _(self.entity_type.lower())
        self.instance.type = self.entity_type

        if hasattr(self.instance, 'entity'):
            self.initial['entity'] = get_last_version(self.instance.entity).pk

    class Meta:
        model = EntityContainerYear
        fields = ['entity']

    def clean_entity(self):
        ev_data = self.cleaned_data['entity']
        self.entity_version = ev_data
        return ev_data.entity if ev_data else None

    def pre_save(self, learning_container_year):
        self.instance.learning_container_year = learning_container_year

    def save(self, commit=True):
        if hasattr(self.instance, 'entity'):
            return super().save(commit)
        elif self.instance.pk:
            # if the instance has no entity, it must be deleted
            self.instance.delete()

    def post_clean(self, start_date):
        entity = self.cleaned_data.get('entity')
        if not entity:
            return

        if not entity_version.get_by_entity_and_date(entity, start_date):
            self.add_error('entity', _("The linked entity does not exist at the start date of the "
                                       "academic year linked to this learning unit"))


class RequirementEntityContainerYearModelForm(EntityContainerYearModelForm):
    entity_type = REQUIREMENT_ENTITY

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields['entity']
        field.queryset = self.person.find_main_entities_version
        field.widget.attrs = {
            'onchange': (
                'updateAdditionalEntityEditability(this.value, "id_additional_requirement_entity_1", false);'
                'updateAdditionalEntityEditability(this.value, "id_additional_requirement_entity_2", true);'
            ), 'id': 'id_requirement_entity'}


class AllocationEntityContainerYearModelForm(EntityContainerYearModelForm):
    entity_type = ALLOCATION_ENTITY

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields['entity']
        field.widget.attrs = {'id': 'allocation_entity'}


class Additional1EntityContainerYearModelForm(EntityContainerYearModelForm):
    entity_type = ADDITIONAL_REQUIREMENT_ENTITY_1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields['entity']
        field.required = False
        field.widget.attrs = {
            'onchange':
                'updateAdditionalEntityEditability(this.value, "id_additional_requirement_entity_2", false)',
                'disable': 'disable',
                'id': 'id_additional_requirement_entity_1'
            }


class Additional2EntityContainerYearModelForm(EntityContainerYearModelForm):
    entity_type = ADDITIONAL_REQUIREMENT_ENTITY_2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields['entity']
        field.required = False
        field.widget.attrs = {'disable': 'disable', 'id': 'id_additional_requirement_entity_2'}


class EntityContainerBaseForm:
    form_classes = [
        RequirementEntityContainerYearModelForm,
        AllocationEntityContainerYearModelForm,
        Additional1EntityContainerYearModelForm,
        Additional2EntityContainerYearModelForm
    ]

    def __init__(self, data=None, person=None, learning_container_year=None):
        self.forms = []
        self.instance = learning_container_year
        for form in self.form_classes:
            qs = EntityContainerYear.objects.filter(learning_container_year=self.instance,
                                                    type=form.entity_type)

            instance = qs.get() if qs.exists() else None
            self.forms.append(form(data, person=person, instance=instance))

    @property
    def changed_data(self):
        return [form.changed_data for form in self.forms]

    @property
    def errors(self):
        return {form.prefix: form.errors for form in self.forms if form.errors}

    def get_clean_data_entity(self, key):
        try:
            form = self.forms[ENTITY_TYPE_LIST.index(key.upper())]
            return form.instance.entity
        except(AttributeError, IndexError):
            return None

    @property
    def fields(self):
        return OrderedDict(
            (ENTITY_TYPE_LIST[index].lower(), form.fields['entity']) for index, form in enumerate(self.forms)
        )

    def post_clean(self, container_type, academic_year):
        for form in self.forms:
            form.post_clean(academic_year.start_date)

        requirement_entity_version = self.forms[0].entity_version
        allocation_entity_version = self.forms[1].entity_version
        requirement_faculty = requirement_entity_version.find_faculty_version(academic_year)
        allocation_faculty = allocation_entity_version.find_faculty_version(academic_year)

        if container_type in LEARNING_CONTAINER_YEAR_TYPES_MUST_HAVE_SAME_ENTITIES:
            if requirement_faculty != allocation_faculty:
                self.forms[1].add_error(
                    "entity", _("Requirement and allocation entities must be linked to the same "
                                "faculty for this learning unit type.")
                )

        return not any(form.errors for form in self.forms)

    def is_valid(self):
        """ Trigger the forms validation"""
        return not self.errors

    def __iter__(self):
        """Yields the forms in the order they should be rendered"""
        return iter(self.forms)

    def __getitem__(self, index):
        """Returns the form at the given index, based on the rendering order"""
        return self.forms[index]

    def save(self, commit=True, learning_container_year=None):
        if learning_container_year:
            for form in self.forms:
                form.pre_save(learning_container_year)
        return [form.save(commit) for form in self.forms]

    def get_linked_entities_forms(self):
        return {key: self.get_clean_data_entity(key) for key in ENTITY_TYPE_LIST}


class LearningContainerYearModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        person = kwargs.pop('person')
        proposal = kwargs.pop('proposal', False)
        super().__init__(*args, **kwargs)

        self.fields['campus'].queryset = find_main_campuses()
        self.fields['container_type'].widget.attrs = {'onchange': 'showInternshipSubtype()'}

        # Limit types for faculty_manager only if simple creation of learning_unit
        if person.is_faculty_manager() and not proposal and not self.instance:
            self.fields["container_type"].choices = _create_faculty_learning_container_type_list()

        if self.initial.get('subtype') == learning_unit_year_subtypes.PARTIM:
            self.fields["container_type"].choices = _create_learning_container_year_type_list()

    def save(self, **kwargs):
        self.instance.learning_container = kwargs.pop('learning_container')
        self.instance.acronym = kwargs.pop('acronym')
        self.instance.academic_year = kwargs.pop('academic_year')
        return super().save(**kwargs)

    class Meta:
        model = LearningContainerYear
        fields = ('container_type', 'common_title', 'common_title_english', 'language', 'campus',
                  'type_declaration_vacant', 'team', 'is_vacant')

    def post_clean(self, specific_title):
        if not self.instance.common_title and not specific_title:
            self.add_error("common_title", _("must_set_common_title_or_specific_title"))

        return not self.errors
