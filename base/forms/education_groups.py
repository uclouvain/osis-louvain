##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.db import models
from django.forms import ModelChoiceField
from django.utils.translation import ugettext_lazy as _

from base.forms.bootstrap import BootstrapForm
from base.models import academic_year, education_group_year, entity_version, offer_type, offer_year_entity
from base.models import entity
from base.models.entity_version import find_last_faculty_entities_version, EntityVersion
from base.models.enums import education_group_categories, offer_year_entity_type
from base.models.enums import entity_type

MAX_RECORDS = 1000

EDUCATION_GROUP_CATEGORIES = (
    (education_group_categories.TRAINING, _('TRAINING')),
    (education_group_categories.MINI_TRAINING, _('MINI_TRAINING')),
    (education_group_categories.GROUP, _('GROUP')),
)


class EntityManagementModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.acronym


class EducationGroupFilter(BootstrapForm):
    academic_year = forms.ModelChoiceField(queryset=academic_year.find_academic_years(), required=False,
                                           empty_label=_('all_label'))
    education_group_type = forms.ModelChoiceField(queryset=offer_type.find_all(), required=False,
                                                  empty_label=_('all_label'))
    category = forms.ChoiceField(EDUCATION_GROUP_CATEGORIES, required=False)
    acronym = title = forms.CharField(
        widget=forms.TextInput(attrs={'size': '10'}),
        max_length=20, required=False)
    entity_management = EntityManagementModelChoiceField(queryset=find_last_faculty_entities_version(), required=False)

    def clean_category(self):
        data_cleaned = self.cleaned_data.get('category')
        if data_cleaned:
            return data_cleaned
        return None

    def get_object_list(self):
        clean_data = {key: value for key, value in self.cleaned_data.items() if value is not None}

        offer_year_entity_prefetch = models.Prefetch(
            'offeryearentity_set',
            queryset=offer_year_entity.search(type=offer_year_entity_type.ENTITY_MANAGEMENT)\
                                      .prefetch_related(
                                         models.Prefetch('entity__entityversion_set', to_attr='entity_versions')
                                      ),
            to_attr='offer_year_entities'
        )
        if clean_data.get('entity_management'):
            clean_data['id'] = _get_filter_entity_management(clean_data['entity_management'])

        education_groups = education_group_year.search(**clean_data)[:MAX_RECORDS + 1]\
                                               .prefetch_related(offer_year_entity_prefetch)
        return [_append_entity_management(education_group) for education_group in education_groups]


def _get_filter_entity_management(entity_management):
    entity_ids = _get_entities_ids(entity_management)
    return list(offer_year_entity.search(link_type=offer_year_entity_type.ENTITY_MANAGEMENT, entity=entity_ids)
                .values_list('education_group_year', flat=True).distinct())


def _get_entities_ids(entity_management):
    entity_versions = entity_version.search(acronym=entity_management.acronym, entity_type=entity_type.FACULTY)\
                                    .select_related('entity').distinct('entity')
    entities = entity.find_descendants([ent_v.entity for ent_v in entity_versions])
    return [ent.id for ent in entities] if entities else []


def _append_entity_management(education_group):
    education_group.entity_management = None
    if education_group.offer_year_entities:
        education_group.entity_management = _find_entity_version_according_academic_year(education_group.
                                                                                         offer_year_entities[0].entity,
                                                                                         education_group.academic_year)
    return education_group


def _find_entity_version_according_academic_year(an_entity, an_academic_year):
    if an_entity.entity_versions:
        return next((entity_vers for entity_vers in an_entity.entity_versions
                     if entity_vers.start_date <= an_academic_year.start_date and
                     (entity_vers.end_date is None or entity_vers.end_date > an_academic_year.end_date)), None)
    return None
