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
import datetime
from collections import OrderedDict
from base import models as mdl
from base.business.learning_unit_year_with_context import volume_learning_component_year
from base.models import entity_container_year
from base.models.entity_component_year import EntityComponentYear
from base.models.entity_container_year import EntityContainerYear
from base.models.enums import entity_container_year_link_type
from base.models.enums import learning_component_year_type
from base.models.enums import learning_container_year_types
from base.models.enums import learning_unit_year_subtypes
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_container_year import LearningContainerYear
from base.models.learning_unit import LearningUnit
from base.models.learning_unit_component import LearningUnitComponent
from base.models.learning_unit_year import LearningUnitYear
from cms import models as mdl_cms
from cms.enums import entity_name
from reference.models import language


# List of key that a user can modify
VALID_VOLUMES_KEYS = [
    'VOLUME_TOTAL',
    'VOLUME_Q1',
    'VOLUME_Q2',
    'PLANNED_CLASSES',
    'VOLUME_' + entity_container_year_link_type.REQUIREMENT_ENTITY,
    'VOLUME_' + entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1,
    'VOLUME_' + entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_2,
    'VOLUME_TOTAL_REQUIREMENT_ENTITIES'
]


def extract_volumes_from_data(post_data):
    volumes = {}

    for param, value in post_data.items():
        param_splitted = param.rsplit("_", 2)
        key = param_splitted[0]
        if _is_a_valid_volume_key(key) and len(param_splitted) == 3:  # KEY_[LEARNINGUNITYEARID]_[LEARNINGCOMPONENTID]
            learning_unit_year_id = int(param_splitted[1])
            component_id = int(param_splitted[2])
            volumes.setdefault(learning_unit_year_id, {}).setdefault(component_id, {}).update({key: value})
    return volumes


def _is_a_valid_volume_key(post_key):
    return post_key in VALID_VOLUMES_KEYS


def get_last_academic_years(last_years=10):
    today = datetime.date.today()
    date_ten_years_before = today.replace(year=today.year - last_years)
    return mdl.academic_year.find_academic_years().filter(start_date__gte=date_ten_years_before)


def get_common_context_learning_unit_year(learning_unit_year_id):
    learning_unit_year = mdl.learning_unit_year.find_by_id(learning_unit_year_id)
    return {
        'learning_unit_year': learning_unit_year,
        'current_academic_year': mdl.academic_year.current_academic_year()
    }


def get_same_container_year_components(learning_unit_year, with_classes=False):
    learning_container_year = learning_unit_year.learning_container_year
    components = []
    learning_components_year = mdl.learning_component_year.find_by_learning_container_year(learning_container_year,
                                                                                           with_classes)

    for learning_component_year in learning_components_year:
        if learning_component_year.classes:
            for learning_class_year in learning_component_year.classes:
                learning_class_year.used_by_learning_units_year = _learning_unit_usage_by_class(learning_class_year)
                learning_class_year.is_used_by_full_learning_unit_year = _is_used_by_full_learning_unit_year(
                    learning_class_year)

        used_by_learning_unit = mdl.learning_unit_component.search(learning_component_year, learning_unit_year)

        entity_components_yr = EntityComponentYear.objects.filter(learning_component_year=learning_component_year)

        components.append({'learning_component_year': learning_component_year,
                           'entity_component_yr': entity_components_yr.first(),
                           'volumes': volume_learning_component_year(learning_component_year, entity_components_yr),
                           'learning_unit_usage': _learning_unit_usage(learning_component_year),
                           'used_by_learning_unit': used_by_learning_unit
                           })
    return components


def get_partims_related(learning_unit_year):
    learning_container_year = learning_unit_year.learning_container_year
    if learning_container_year:
        return mdl.learning_unit_year.search(learning_container_year_id=learning_container_year,
                                             subtype=learning_unit_year_subtypes.PARTIM) \
            .exclude(learning_container_year__isnull=True).order_by('acronym')


def show_subtype(learning_unit_year):
    learning_container_year = learning_unit_year.learning_container_year

    if learning_container_year:
        return learning_container_year.container_type == learning_container_year_types.COURSE or \
               learning_container_year.container_type == learning_container_year_types.INTERNSHIP
    return False


def get_campus_from_learning_unit_year(learning_unit_year):
    if learning_unit_year.learning_container_year:
        return learning_unit_year.learning_container_year.campus


def get_organization_from_learning_unit_year(learning_unit_year):
    campus = get_campus_from_learning_unit_year(learning_unit_year)
    if campus:
        return campus.organization


def get_all_attributions(learning_unit_year):
    attributions = {}
    if learning_unit_year.learning_container_year:
        all_attributions = entity_container_year.find_last_entity_version_grouped_by_linktypes(
            learning_unit_year.learning_container_year)

        attributions['requirement_entity'] = all_attributions.get(entity_container_year_link_type.REQUIREMENT_ENTITY)
        attributions['allocation_entity'] = all_attributions.get(entity_container_year_link_type.ALLOCATION_ENTITY)
        attributions['additional_requirement_entities'] = [
            all_attributions[link_type] for link_type in all_attributions
            if link_type not in [entity_container_year_link_type.REQUIREMENT_ENTITY,
                                 entity_container_year_link_type.ALLOCATION_ENTITY]
        ]
    return attributions


def get_cms_label_data(cms_label, user_language):
    cms_label_data = OrderedDict()
    translated_labels = mdl_cms.translated_text_label.search(text_entity=entity_name.LEARNING_UNIT_YEAR,
                                                             labels=cms_label,
                                                             language=user_language)

    for label in cms_label:
        translated_text = next((trans.label for trans in translated_labels if trans.text_label.label == label), None)
        cms_label_data[label] = translated_text

    return cms_label_data


def _learning_unit_usage(a_learning_component_year):
    learning_unit_component = mdl.learning_unit_component.find_by_learning_component_year(a_learning_component_year)
    return ", ".join(l.learning_unit_year.acronym for l in learning_unit_component)


def _learning_unit_usage_by_class(a_learning_class_year):
    queryset = mdl.learning_unit_component_class.find_by_learning_class_year(a_learning_class_year) \
        .order_by('learning_unit_component__learning_unit_year__acronym') \
        .values_list('learning_unit_component__learning_unit_year__acronym', flat=True)
    return ", ".join(list(queryset))


def get_components_identification(learning_unit_yr):
    a_learning_container_yr = learning_unit_yr.learning_container_year
    components = []
    if a_learning_container_yr:
        learning_component_year_list = mdl.learning_component_year.find_by_learning_container_year(
            a_learning_container_yr)

        for learning_component_year in learning_component_year_list:
            if mdl.learning_unit_component.search(learning_component_year, learning_unit_yr).exists():
                entity_components_yr = EntityComponentYear.objects.filter(
                    learning_component_year=learning_component_year)

                components.append({'learning_component_year': learning_component_year,
                                   'entity_component_yr': entity_components_yr.first(),
                                   'volumes': volume_learning_component_year(learning_component_year,
                                                                             entity_components_yr),
                                   'learning_unit_usage': _learning_unit_usage(learning_component_year)})
    return components


def _is_used_by_full_learning_unit_year(a_learning_class_year):
    for l in mdl.learning_unit_component_class.find_by_learning_class_year(a_learning_class_year):
        if l.learning_unit_component.learning_unit_year.subdivision is None:
            return True

    return False


def create_learning_unit_structure(additional_entity_version_1, additional_entity_version_2, allocation_entity_version,
                                   data, form, new_learning_container, new_learning_unit, requirement_entity_version,
                                   status, academic_year):
    new_learning_container_year = LearningContainerYear.objects. \
        create(academic_year=academic_year,
               learning_container=new_learning_container,
               title=data['title'],
               acronym=data['acronym'].upper(),
               container_type=data['learning_container_year_type'],
               language=data['language'])
    new_requirement_entity = create_entity_container_year(requirement_entity_version,
                                                          new_learning_container_year,
                                                          entity_container_year_link_type.REQUIREMENT_ENTITY)
    if allocation_entity_version:
        create_entity_container_year(allocation_entity_version, new_learning_container_year,
                                     entity_container_year_link_type.ALLOCATION_ENTITY)
    if additional_entity_version_1:
        create_entity_container_year(additional_entity_version_1, new_learning_container_year,
                                     entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1)
    if additional_entity_version_2:
        create_entity_container_year(additional_entity_version_2, new_learning_container_year,
                                     entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_2)
    if data['learning_container_year_type'] == learning_container_year_types.COURSE:
        create_course(academic_year, form, new_learning_container_year, new_learning_unit,
                      new_requirement_entity, status)
    else:
        create_another_type(academic_year, form, new_learning_container_year, new_learning_unit,
                            new_requirement_entity, status)


def create_another_type(an_academic_year, form, new_learning_container_year, new_learning_unit, new_requirement_entity,
                        status):
    new_learning_component_year = create_learning_component_year(new_learning_container_year,
                                                                 "NT1", None)
    EntityComponentYear.objects.create(entity_container_year=new_requirement_entity,
                                       learning_component_year=new_learning_component_year)
    new_learning_unit_year = create_learning_unit_year(an_academic_year, form,
                                                       new_learning_container_year,
                                                       new_learning_unit,
                                                       status)
    create_learning_unit_component(new_learning_unit_year, new_learning_component_year, None)


def create_course(an_academic_year, form, new_learning_container_year, new_learning_unit,
                  new_requirement_entity, status):
    new_lecturing = create_learning_component_year(new_learning_container_year, "CM1",
                                                   learning_component_year_type.LECTURING)
    new_practical_exercise = create_learning_component_year(new_learning_container_year, "TP1",
                                                            learning_component_year_type.PRACTICAL_EXERCISES)
    EntityComponentYear.objects.create(entity_container_year=new_requirement_entity,
                                       learning_component_year=new_lecturing)
    EntityComponentYear.objects.create(entity_container_year=new_requirement_entity,
                                       learning_component_year=new_practical_exercise)
    new_learning_unit_year = create_learning_unit_year(an_academic_year, form,
                                                       new_learning_container_year,
                                                       new_learning_unit,
                                                       status)
    create_learning_unit_component(new_learning_unit_year, new_lecturing,
                                   learning_component_year_type.LECTURING)
    create_learning_unit_component(new_learning_unit_year, new_practical_exercise,
                                   learning_component_year_type.PRACTICAL_EXERCISES)


def create_learning_component_year(learning_container_year, acronym, type_learning_component_year):
    return LearningComponentYear.objects.create(learning_container_year=learning_container_year,
                                                acronym=acronym,
                                                type=type_learning_component_year)


def create_learning_unit_component(learning_unit_year, learning_component_year, type_learning_unit_component):
    return LearningUnitComponent.objects.create(learning_unit_year=learning_unit_year,
                                                learning_component_year=learning_component_year,
                                                type=type_learning_unit_component)


def create_entity_container_year(entity_version, learning_container_year, type_entity_container_year):
    return EntityContainerYear.objects.create(entity=entity_version.entity,
                                              learning_container_year=learning_container_year,
                                              type=type_entity_container_year)


def create_learning_unit(data, learning_container, year):
    return LearningUnit.objects.create(acronym=data['acronym'].upper(), title=data['title'], start_year=year,
                                       periodicity=data['periodicity'], learning_container=learning_container,
                                       faculty_remark=data['faculty_remark'], other_remark=data['other_remark'])


def create_learning_unit_year(academic_year, form, learning_container_year, learning_unit, status):
    return LearningUnitYear.objects.create(academic_year=academic_year, learning_unit=learning_unit,
                                           learning_container_year=learning_container_year,
                                           acronym=form.data['acronym'].upper(),
                                           title=form.data['title'],
                                           title_english=form.data['title_english'],
                                           subtype=form.data['subtype'],
                                           credits=form.data['credits'],
                                           internship_subtype=form.data.get('internship_subtype'),
                                           status=status,
                                           session=form.data['session'])



