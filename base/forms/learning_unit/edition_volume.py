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
from django.db import transaction
from django.db.models import Prefetch
from django.forms import formset_factory
from django.utils.translation import ugettext_lazy as _

from base.business.learning_unit_year_with_context import ENTITY_TYPES_VOLUME
from base.business.learning_units import edition
from base.business.learning_units.edition import check_postponement_conflict_report_errors
from base.forms.utils.emptyfield import EmptyField
from base.models.entity_component_year import EntityComponentYear
from base.models.enums import entity_container_year_link_type as entity_types
from base.models.learning_unit_component import LearningUnitComponent


class VolumeField(forms.DecimalField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, max_digits=6, decimal_places=2, min_value=0, **kwargs)


class VolumeEditionForm(forms.Form):

    requirement_entity_key = 'volume_' + entity_types.REQUIREMENT_ENTITY.lower()
    additional_requirement_entity_1_key = 'volume_' + entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1.lower()
    additional_requirement_entity_2_key = 'volume_' + entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2.lower()

    opening_parenthesis_field = EmptyField(label='(')
    volume_q1 = VolumeField(label=_('partial_volume_1Q'), help_text=_('partial_volume_1'))
    add_field = EmptyField(label='+')
    volume_q2 = VolumeField(label=_('partial_volume_2Q'), help_text=_('partial_volume_2'))
    equal_field_1 = EmptyField(label='=')
    help_volume_total = "{} = {} + {}".format(_('Volume total annual'), _('partial_volume_1'), _('partial_volume_2'))
    volume_total = VolumeField(label=_('Vol. tot. annual'), help_text=help_volume_total)
    closing_parenthesis_field = EmptyField(label=')')
    mult_field = EmptyField(label='*')
    planned_classes = forms.IntegerField(label=_('planned_classes_pc'), help_text=_('planned_classes'), min_value=0)
    equal_field_2 = EmptyField(label='=')

    _post_errors = []
    _parent_data = {}
    _faculty_manager_fields = ['volume_q1', 'volume_q2']

    def __init__(self, *args, **kwargs):
        self.component = kwargs.pop('component')
        self.learning_unit_year = kwargs.pop('learning_unit_year')
        self.entities = kwargs.pop('entities')
        self.is_faculty_manager = kwargs.pop('is_faculty_manager', False)

        self.title = self.component.acronym
        self.title_help = _(self.component.type) + ' ' if self.component.type else ''
        self.title_help += self.component.acronym

        super().__init__(*args, **kwargs)
        help_volume_global = "{} = {} * {}".format(_('volume_global'), _('Volume total annual'), _('planned_classes'))
        self.fields['volume_total_requirement_entities'] = VolumeField(
            label=_('vol_global'), help_text=help_volume_global)
        self.fields['equal_field_3'] = EmptyField(label='=')

        # Append dynamic fields
        entities_to_add = [entity for entity in ENTITY_TYPES_VOLUME if entity in self.entities]
        for i, key in enumerate(entities_to_add):
            entity = self.entities[key]
            self.fields["volume_" + key.lower()] = VolumeField(label=entity.acronym, help_text=entity.title)
            if i != len(entities_to_add) - 1:
                self.fields["add" + key.lower()] = EmptyField(label='+')

        if self.is_faculty_manager and self.learning_unit_year.is_full():
            self._disable_central_manager_fields()

    def _disable_central_manager_fields(self):
        for key, field in self.fields.items():
            if key not in self._faculty_manager_fields:
                field.disabled = True

    def get_entity_fields(self):
        entity_keys = [self.requirement_entity_key, self.additional_requirement_entity_1_key,
                       self.additional_requirement_entity_2_key]
        return [self.fields[key] for key in entity_keys if key in self.fields]

    def save(self, postponement):
        if not self.changed_data:
            return None

        conflict_report = {}
        if postponement:
            conflict_report = edition.get_postponement_conflict_report(self.learning_unit_year)
            luy_to_update_list = conflict_report['luy_without_conflict']
        else:
            luy_to_update_list = [self.learning_unit_year]

        with transaction.atomic():
            for component in self._find_learning_components_year(luy_to_update_list):
                self._save(component)

        # Show conflict error if exists
        check_postponement_conflict_report_errors(conflict_report)

    def _save(self, component):
        component.hourly_volume_total_annual = self.cleaned_data['volume_total']
        component.hourly_volume_partial_q1 = self.cleaned_data['volume_q1']
        component.hourly_volume_partial_q2 = self.cleaned_data['volume_q2']
        component.planned_classes = self.cleaned_data['planned_classes']
        component.save()
        self._save_requirement_entities(component.entity_components_year)

    def _save_requirement_entities(self, entity_components_year):
        for ecy in entity_components_year:
            link_type = ecy.entity_container_year.type
            repartition_volume = self.cleaned_data.get('volume_' + link_type.lower())

            if repartition_volume is None:
                continue

            ecy.repartition_volume = repartition_volume
            ecy.save()

    def _find_learning_components_year(self, luy_to_update_list):
        prefetch = Prefetch(
            'learning_component_year__entitycomponentyear_set',
            queryset=EntityComponentYear.objects.all(),
            to_attr='entity_components_year'
        )
        return [
            luc.learning_component_year
            for luc in LearningUnitComponent.objects.filter(
                learning_unit_year__in=luy_to_update_list).prefetch_related(prefetch)
            if luc.learning_component_year.type == self.component.type
        ]


class VolumeEditionBaseFormset(forms.BaseFormSet):

    def __init__(self, *args, **kwargs):
        self.learning_unit_year = kwargs.pop('learning_unit_year')
        self.components = list(self.learning_unit_year.components.keys())
        self.components_values = list(self.learning_unit_year.components.values())
        self.is_faculty_manager = kwargs.pop('is_faculty_manager')

        super().__init__(*args, **kwargs)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs['learning_unit_year'] = self.learning_unit_year
        kwargs['component'] = self.components[index]
        kwargs['initial'] = self._clean_component_keys(self.components_values[index])
        kwargs['entities'] = self.learning_unit_year.entities
        kwargs['is_faculty_manager'] = self.is_faculty_manager
        return kwargs

    @staticmethod
    def _clean_component_keys(component_dict):
        # Field's name must be in lowercase
        return {k.lower(): v for k, v in component_dict.items()}

    def get_form_by_type(self, component_type):
        return next(form for form in self.forms if form.component.type == component_type)

    def save(self, postponement):
        for form in self.forms:
            form.save(postponement)


class VolumeEditionFormsetContainer:
    """
    Create and Manage a set of VolumeEditionFormsets
    """
    def __init__(self, request, learning_units, person):
        self.formsets = OrderedDict()
        self.learning_units = learning_units
        self.parent = self.learning_units[0]
        self.postponement = int(request.POST.get('postponement', 1))
        self.request = request

        self.is_faculty_manager = person.is_faculty_manager() and not person.is_central_manager()

        for learning_unit in learning_units:
            volume_edition_formset = formset_factory(
                form=VolumeEditionForm, formset=VolumeEditionBaseFormset, extra=len(learning_unit.components)
            )
            self.formsets[learning_unit] = volume_edition_formset(
                request.POST or None,
                learning_unit_year=learning_unit,
                prefix=learning_unit.acronym,
                is_faculty_manager=self.is_faculty_manager
            )

    def is_valid(self):
        if not self.request.POST:
            return False

        if not all([formset.is_valid() for formset in self.formsets.values()]):
            return False

        return True

    def save(self):
        for formset in self.formsets.values():
            formset.save(self.postponement)

    @property
    def errors(self):
        errors = {}
        for formset in self.formsets.values():
            errors.update(self._get_formset_errors(formset))
        return errors

    @staticmethod
    def _get_formset_errors(formset):
        errors = {}
        for i, form_errors in enumerate(formset.errors):
            for name, error in form_errors.items():
                errors["{}-{}-{}".format(formset.prefix, i, name)] = error
        return errors
