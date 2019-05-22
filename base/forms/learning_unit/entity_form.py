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
from collections import OrderedDict

from dal import autocomplete
from django import forms
from django.db.models import Q
from django.utils import timezone
from django.utils.functional import lazy
from django.utils.translation import ugettext_lazy as _

from base.forms.utils.choice_field import add_blank, add_all
from base.models.entity_container_year import EntityContainerYear
from base.models.entity_version import get_last_version, find_pedagogical_entities_version, EntityVersion
from base.models.enums.entity_container_year_link_type import REQUIREMENT_ENTITY, ALLOCATION_ENTITY, \
    ADDITIONAL_REQUIREMENT_ENTITY_1, ADDITIONAL_REQUIREMENT_ENTITY_2, ENTITY_TYPE_LIST, EntityContainerYearLinkTypes
from base.models.enums.organization_type import MAIN, ACADEMIC_PARTNER
from base.models.learning_component_year import LearningComponentYear
from reference.models.country import Country


def _get_section_choices():
    return add_blank(
        add_all(Country.objects.filter(entity__isnull=False).values_list('id', 'name').distinct().order_by('name')),
        blank_choice_display="UCLouvain"
    )


class EntitiesVersionChoiceField(forms.ModelChoiceField):
    entity_version = None

    def label_from_instance(self, obj):
        return obj.verbose_title

    def clean(self, value):
        ev_data = super().clean(value)
        self.entity_version = ev_data
        return ev_data.entity if ev_data else None


def find_additional_requirement_entities_choices():
    date = timezone.now()
    return EntityVersion.objects.current(date).filter(
        Q(entity__organization__type=MAIN) |
        (Q(entity__organization__type=ACADEMIC_PARTNER) & Q(entity__organization__is_current_partner=True))
    ).select_related('entity', 'entity__organization').order_by('acronym')


class EntityContainerYearModelForm(forms.ModelForm):
    entity = EntitiesVersionChoiceField(
        widget=autocomplete.ModelSelect2(
            url='entity_autocomplete',
            attrs={'data-html': True},
            forward=['country']
        ),
        queryset=find_additional_requirement_entities_choices()
    )
    entity_type = ''
    country = forms.ChoiceField(choices=lazy(_get_section_choices, list), required=False, label=_("Country"))

    def __init__(self, *args, **kwargs):
        self.person = kwargs.pop('person')

        super().__init__(*args, prefix=self.entity_type.lower(), **kwargs)

        self.fields['entity'].label = EntityContainerYearLinkTypes[self.entity_type].value
        self.instance.type = self.entity_type

        if hasattr(self.instance, 'entity'):
            self.initial['entity'] = get_last_version(self.instance.entity).pk

    class Meta:
        model = EntityContainerYear
        fields = ['entity', 'country']

    def pre_save(self, learning_container_year):
        self.instance.learning_container_year = learning_container_year

    def save(self, commit=True):
        if hasattr(self.instance, 'entity'):
            return super().save(commit)
        elif self.instance.pk:
            # if the instance has no entity, it must be deleted
            self.instance.delete()
            self._assert_repartition_volumes_consistency()

    def _assert_repartition_volumes_consistency(self):
        """In case EntityContainerYear was removed, need to reset repartition volumes to None."""
        repartition_attr_by_type = LearningComponentYear.repartition_volume_attrs_by_entity_container_type()
        attr_name = repartition_attr_by_type[self.entity_type]
        qs = LearningComponentYear.objects.filter(
            learning_unit_year__learning_container_year=self.instance.learning_container_year)
        qs.update(**{attr_name: None})

    @property
    def entity_version(self):
        return self.fields["entity"].entity_version

    def post_clean(self, start_date):
        entity = self.cleaned_data.get('entity')
        if not entity:
            return


class RequirementEntityContainerYearModelForm(EntityContainerYearModelForm):
    entity_type = REQUIREMENT_ENTITY
    entity = EntitiesVersionChoiceField(
        widget=autocomplete.ModelSelect2(
            url='entity_requirement_autocomplete',
            attrs={'data-html': True},
            forward=['country']
        ),
        queryset=find_additional_requirement_entities_choices()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        entity_field = self.fields['entity']
        entity_field.queryset = self.person.find_main_entities_version
        entity_field.widget.attrs = {
            'onchange': (
                'updateAdditionalEntityEditability(this.value, "id_additional_requirement_entity_1", false);'
                'updateAdditionalEntityEditability(this.value, "id_additional_requirement_entity_1_country", false);'
                'updateAdditionalEntityEditability(this.value, "id_additional_requirement_entity_2", true);'
                'updateAdditionalEntityEditability(this.value, "id_additional_requirement_entity_2_country", true);'
            ), 'id': 'id_requirement_entity'}


class AllocationEntityContainerYearModelForm(EntityContainerYearModelForm):
    entity_type = ALLOCATION_ENTITY

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        entity_field = self.fields['entity']
        entity_field.queryset = find_pedagogical_entities_version()
        entity_field.widget.attrs = {'id': 'allocation_entity'}


class Additional1EntityContainerYearModelForm(EntityContainerYearModelForm):
    entity_type = ADDITIONAL_REQUIREMENT_ENTITY_1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields['entity']
        field.required = False
        field.widget.attrs = {
            'onchange': (
                'updateAdditionalEntityEditability(this.value, "id_additional_requirement_entity_2", false);'
                'updateAdditionalEntityEditability(this.value, "id_additional_requirement_entity_2_country", false);'
            ),
            'id': 'id_additional_requirement_entity_1'
        }
        country = self.fields['country']
        country.widget.attrs = {'id': 'id_additional_requirement_entity_1_country'}


class Additional2EntityContainerYearModelForm(EntityContainerYearModelForm):
    entity_type = ADDITIONAL_REQUIREMENT_ENTITY_2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields['entity']
        field.required = False
        field.widget.attrs = {'id': 'id_additional_requirement_entity_2'}
        country = self.fields['country']
        country.widget.attrs = {'id': 'id_additional_requirement_entity_2_country'}


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

    @property
    def instances_data(self):
        return OrderedDict(
            (ENTITY_TYPE_LIST[index].lower(), getattr(form.instance, 'entity', None))
            for index, form in enumerate(self.forms)
        )

    def post_clean(self, container_type, academic_year):
        for form in self.forms:
            form.post_clean(academic_year.start_date)
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
