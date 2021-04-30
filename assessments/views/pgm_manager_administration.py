##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
import json
from collections import OrderedDict
from typing import Dict, Union, List

from dal import autocomplete
from django import forms
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q, Subquery, OuterRef
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils.functional import cached_property
from django.views.generic import ListView, DeleteView, FormView
from django.views.generic.edit import BaseUpdateView

from base.auth.roles import program_manager
from base.auth.roles.entity_manager import EntityManager
from base.auth.roles.program_manager import ProgramManager
from base.models import academic_year
from base.models.education_group import EducationGroup
from base.models.education_group_type import EducationGroupType
from base.models.education_group_year import EducationGroupYear
from base.models.entity_version import EntityVersion, build_current_entity_version_structure_in_memory, \
    find_all_current_entities_version
from base.models.enums import education_group_categories
from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import TrainingType
from base.models.person import Person
from base.views.mixins import AjaxTemplateMixin

ALL_OPTION_VALUE = "-"
ALL_OPTION_VALUE_ENTITY = "all_"

EXCLUDE_OFFER_TYPE_SEARCH = TrainingType.finality_types()


class ProgramManagerListView(ListView):
    model = ProgramManager
    template_name = "admin/programmanager_list.html"

    @cached_property
    def education_group_ids(self) -> List[int]:
        return self.request.GET.getlist('education_groups')

    def get_queryset(self):
        qs = super().get_queryset()
        education_group_ids = self.education_group_ids
        if not education_group_ids:
            return qs.none()

        result = qs.filter(education_group_id__in=education_group_ids).annotate(
            offer_acronym=Subquery(
                EducationGroupYear.objects.filter(
                    education_group_id=OuterRef('education_group_id'),
                    academic_year=academic_year.current_academic_year(),
                ).values('acronym')[:1]
            ),
        ).select_related(
            'person'
        ).order_by(
            'person__last_name',
            'person__first_name',
            'pk'
        )
        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['education_groups'] = self.education_group_ids

        result = OrderedDict()
        for i in self.object_list:
            result.setdefault(i.person, []).append(i)

        context["by_person"] = result
        return context


class ProgramManagerMixin(PermissionRequiredMixin, AjaxTemplateMixin):
    model = ProgramManager
    success_url = reverse_lazy('manager_list')
    partial_reload = '#pnl_managers'
    permission_required = 'base.change_programmanager'

    @property
    def education_group_ids(self) -> list:
        return self.request.GET['education_groups'].split(',')

    def get_success_url(self):
        url = reverse_lazy('manager_list') + "?"
        for education_group_id in self.education_group_ids:
            url += "education_groups={}&".format(education_group_id)
        return url


class ProgramManagerDeleteView(ProgramManagerMixin, DeleteView):
    template_name = 'admin/programmanager_confirm_delete_inner.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['manager'] = self.object.person
        context['other_programs'] = self.object.person.programmanager_set.exclude(pk=self.object.pk)
        return context


class ProgramManagerPersonDeleteView(ProgramManagerMixin, DeleteView):
    template_name = 'admin/programmanager_confirm_delete_inner.html'

    def get_object(self, queryset=None):
        return self.model.objects.filter(
            person__pk=self.kwargs['pk'],
            education_group_id__in=self.education_group_ids
        )

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        for obj in self.object.all():
            obj.delete()
        return self._ajax_response() or HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        manager = Person.objects.get(pk=self.kwargs['pk'])
        context['manager'] = manager
        context['other_programs'] = manager.programmanager_set.exclude(education_group_id__in=self.education_group_ids)
        return context


class MainProgramManagerUpdateView(ProgramManagerMixin, BaseUpdateView):
    fields = 'is_main',


class MainProgramManagerPersonUpdateView(ProgramManagerMixin, ListView):
    def get_queryset(self):
        return self.model.objects.filter(
            person=self.kwargs["pk"],
            education_group_id__in=self.education_group_ids
        )

    def post(self, *args, **kwargs):
        """ Update column is_main for selected education_groups"""
        val = json.loads(self.request.POST.get('is_main'))
        self.get_queryset().update(is_main=val)
        return super()._ajax_response() or HttpResponseRedirect(self.get_success_url())


class PersonAutocomplete(autocomplete.Select2QuerySetView):
    def get_result_label(self, item):
        return "{} {}, {}".format(item.last_name, item.first_name, item.email)

    def get_queryset(self):
        qs = Person.objects.all()
        if self.q:
            qs = qs.filter(Q(last_name__icontains=self.q) | Q(first_name__icontains=self.q))
        return qs.order_by('last_name', 'first_name')


class ProgramManagerForm(forms.ModelForm):
    class Meta:
        model = ProgramManager
        fields = ('person',)
        widgets = {'person': autocomplete.ModelSelect2(url='person-autocomplete', attrs={'style': 'width:100%'})}


class ProgramManagerCreateView(ProgramManagerMixin, FormView):
    form_class = ProgramManagerForm
    template_name = 'admin/manager_add_inner.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['education_groups'] = self.request.GET['education_groups']
        return context

    def form_valid(self, form):
        education_groups = EducationGroup.objects.filter(pk__in=self.education_group_ids).distinct()

        person = form.cleaned_data['person']
        for education_group in education_groups:
            ProgramManager.objects.get_or_create(person=person, education_group=education_group)

        return super().form_valid(form)


@login_required
@permission_required('base.view_programmanager', raise_exception=True)
def pgm_manager_administration(request):
    administrator_entities = get_administrator_entities(request.user)
    return render(request, "admin/pgm_manager.html", {
        'administrator_entities_string': _get_administrator_entities_acronym_list(administrator_entities),
        'entities_managed_root': administrator_entities,
        'offer_types': __search_offer_types(),
        'managers': _get_entity_program_managers(administrator_entities),
        'init': '1'
    })


def __search_offer_types():
    return EducationGroupType.objects.filter(
        category=Categories.TRAINING.name
    )


@login_required
def pgm_manager_search(request):
    person_id = get_filter_value(request, 'person')
    manager_person = None
    if person_id:
        manager_person = get_object_or_404(Person, pk=person_id)

    entity_selected = get_filter_value(request, 'entity')  # if an acronym is selected this value is not none
    entity_root_selected = None  # if an 'all hierarchy of' is selected this value is not none

    if entity_selected is None:
        entity_root_selected = get_entity_root_selected(request)

    pgm_offer_type = get_filter_value(request, 'offer_type')

    administrator_entities = get_administrator_entities(request.user)

    current_academic_yr = academic_year.current_academic_year()

    data = {
        'person': manager_person,
        'administrator_entities_string': _get_administrator_entities_acronym_list(administrator_entities),
        'entities_managed_root': administrator_entities,
        'entity_selected': entity_selected,
        'entity_root_selected': entity_root_selected,
        'offer_types': __search_offer_types(),
        'pgms': _get_trainings(current_academic_yr,
                               get_entity_list(entity_selected, get_entity_root(entity_root_selected)),
                               manager_person,
                               pgm_offer_type),
        'managers': _get_entity_program_managers(administrator_entities),
        'offer_type': pgm_offer_type
    }
    return render(request, "admin/pgm_manager.html", data)


def get_entity_root(entity_id: int):
    return find_all_current_entities_version().filter(entity_id=entity_id).first()


def get_entity_root_selected(request):
    entity_root_selected = get_filter_value_entity(request, 'entity')
    if entity_root_selected is None:
        entity_root_selected = request.POST.get('entity_root', None)
    return entity_root_selected


def get_managed_entities(
        entity_managed_list: List[Dict[str, Union['EntityVersion', List['EntityVersion']]]]
) -> List['EntityVersion']:
    if entity_managed_list:
        structures = []
        for entity_managed in entity_managed_list:
            structures += entity_managed['structures']
        return list(sorted(set(structures), key=lambda entity_version: entity_version.acronym))

    return None


def get_entity_list(entity_id: int, entity_managed_structure: 'EntityVersion'):
    if entity_id:
        entity_found = get_entity_root(entity_id)
        if entity_found:
            return [entity_found]
    elif entity_managed_structure:
        structure = build_current_entity_version_structure_in_memory()  # TODO :: reuse CTE
        return [entity_managed_structure] + structure[entity_managed_structure.entity_id]['all_children']
    return None


@login_required
def get_filter_value(request, value_name):
    value = _get_request_value(request, value_name)

    if value == ALL_OPTION_VALUE or value == '' or value.startswith(ALL_OPTION_VALUE_ENTITY):
        return None
    return value


def get_administrator_entities(a_user) -> List[Dict[str, Union['EntityVersion', List['EntityVersion']]]]:
    root_entity_ids = EntityManager.objects.filter(
        person__user=a_user
    ).values_list(
        'entity_id',
        flat=True
    ).distinct().order_by('entity__entityversion__acronym')

    structure = build_current_entity_version_structure_in_memory()

    structures = []

    for root_entity_id in root_entity_ids:
        root_entity = structure[root_entity_id]['entity_version']
        structures.append({
            'root': root_entity,
            'structures': sorted(
                [root_entity] + structure[root_entity_id]['all_children'],
                key=lambda entity_version: entity_version.acronym
            )
        })
    return structures


def _get_trainings(academic_yr, entity_list, manager_person, education_group_type) -> List['EducationGroupYear']:
    qs = EducationGroupYear.objects.filter(
        academic_year=academic_yr,
        management_entity__in={ev.entity_id for ev in entity_list},
        education_group_type__category=education_group_categories.TRAINING,
    )

    if education_group_type:
        qs = qs.filter(education_group_type=education_group_type)

    if manager_person:
        qs = qs.filter(education_group__programmanager__person=manager_person)
    return qs.distinct().select_related('management_entity', 'education_group_type').order_by('acronym')


def _get_entity_program_managers(entity):
    entities = get_managed_entities(entity)
    return program_manager.find_by_management_entity(entities)


def find_values(key_value, json_repr):
    results = []

    def _decode_dict(a_dict):
        try:
            results.append(a_dict[key_value])
        except KeyError:
            pass
        return a_dict

    json.loads(json_repr, object_hook=_decode_dict)  # return value ignored
    return results


@login_required
def get_filter_value_entity(request, value_name):
    value = _get_request_value(request, value_name)
    if value != '' and value.startswith(ALL_OPTION_VALUE_ENTITY):
        return value.replace(ALL_OPTION_VALUE_ENTITY, "")

    return None


def _get_request_value(request, value_name):
    if request.method == 'POST':
        value = request.POST.get(value_name, None)
    else:
        value = request.GET.get(value_name, None)
    return value


def _get_administrator_entities_acronym_list(administrator_entities):
    """
    Return a list of acronyms separated by comma.  List of the acronyms administrate by the user
    :param administrator_entities:
    :return:
    """
    return ', '.join(str(entity_manager['root'].acronym) for entity_manager in administrator_entities)
