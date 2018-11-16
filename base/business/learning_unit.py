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
from operator import itemgetter

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from attribution.models import attribution
from attribution.models.attribution import find_all_tutors_by_learning_unit_year
from base import models as mdl_base
from base.business.entity import get_entity_calendar

from base.business.learning_unit_year_with_context import volume_learning_component_year
from base.business.learning_units.comparison import get_entity_by_type
from base.business.xls import get_name_or_username
from base.models import entity_container_year, academic_calendar
from base.models import learning_achievement
from base.models.entity_component_year import EntityComponentYear
from base.models.enums import academic_calendar_type
from base.models.enums.entity_container_year_link_type import REQUIREMENT_ENTITIES
from cms import models as mdl_cms
from cms.enums import entity_name
from cms.enums.entity_name import LEARNING_UNIT_YEAR
from cms.models import translated_text
from osis_common.document import xls_build
from osis_common.utils.datetime import convert_date_to_datetime
from base.models.enums import entity_container_year_link_type
# List of key that a user can modify

WORKSHEET_TITLE = 'learning_units'
XLS_FILENAME = 'learning_units_filename'
XLS_DESCRIPTION = "List_activities"
LEARNING_UNIT_TITLES_PART1 = [
    str(_('code')),
    str(_('Ac yr.')),
    str(_('Title')),
    str(_('type')),
    str(_('Subtype')),
    str(_('Req. Entity')),
    str(_('Proposal type')),
    str(_('Proposal status')),
    str(_('credits')),
    str(_('Alloc. Ent.')),
    str(_('Title in English')),
]

LEARNING_UNIT_TITLES_PART2 = [
    str(_('Periodicity')),
    str(_('Active')),
    "{} 1 - {}".format(_('Hourly vol.'), _('Annual')),
    "{} 1 - {}".format(_('Hourly vol.'), _('1st quadri')),
    "{} 1 - {}".format(_('Hourly vol.'), _('2nd quadri')),
    "{} 1".format(_('Planned classes')),
    "{} 2 - {}".format(_('Hourly vol.'), _('Annual')),
    "{} 2 - {}".format(_('Hourly vol.'), _('1st quadri')),
    "{} 2 - {}".format(_('Hourly vol.'), _('2nd quadri')),
    "{} 2".format(_('Planned classes')),
    str(_('Quadrimester')),
    str(_('Session derogation')),
    str(_('Language')),
    str(_('Absolute credits')),
]
CMS_LABEL_SPECIFICATIONS = ['themes_discussed', 'prerequisite']

CMS_LABEL_PEDAGOGY_FR_AND_EN = ['resume', 'teaching_methods', 'evaluation_methods', 'other_informations',
                                'online_resources']
CMS_LABEL_PEDAGOGY_FR_ONLY = ['bibliography', 'mobility']
CMS_LABEL_PEDAGOGY = CMS_LABEL_PEDAGOGY_FR_AND_EN + CMS_LABEL_PEDAGOGY_FR_ONLY

CMS_LABEL_SUMMARY = ['resume']

COLORED = 'COLORED_ROW'


def get_same_container_year_components(learning_unit_year, with_classes=False):
    learning_container_year = learning_unit_year.learning_container_year
    components = []
    learning_components_year = mdl_base.learning_component_year.find_by_learning_container_year(learning_container_year,
                                                                                                with_classes)
    additionnal_entities = {}

    for indx, learning_component_year in enumerate(learning_components_year):
        if learning_component_year.classes:
            for learning_class_year in learning_component_year.classes:
                learning_class_year.used_by_learning_units_year = _learning_unit_usage_by_class(learning_class_year)
                learning_class_year.is_used_by_full_learning_unit_year = _is_used_by_full_learning_unit_year(
                    learning_class_year)

        used_by_learning_unit = mdl_base.learning_unit_component.search(learning_component_year, learning_unit_year)

        entity_components_yr = EntityComponentYear.objects.filter(learning_component_year=learning_component_year)
        if indx == 0:
            additionnal_entities = _get_entities(entity_components_yr)

        components.append({'learning_component_year': learning_component_year,
                           'volumes': volume_learning_component_year(learning_component_year, entity_components_yr),
                           'learning_unit_usage': _learning_unit_usage(learning_component_year),
                           'used_by_learning_unit': used_by_learning_unit
                           })

    components = sorted(components, key=itemgetter('learning_unit_usage'))
    return _compose_components_dict(components, additionnal_entities)


def get_organization_from_learning_unit_year(learning_unit_year):
    if learning_unit_year.campus:
        return learning_unit_year.campus.organization


def get_all_attributions(learning_unit_year):
    attributions = {}
    if learning_unit_year.learning_container_year:
        all_attributions = entity_container_year.find_last_entity_version_grouped_by_linktypes(
            learning_unit_year.learning_container_year)

        attributions['requirement_entity'] = all_attributions.get(entity_container_year_link_type.REQUIREMENT_ENTITY)
        attributions['allocation_entity'] = all_attributions.get(entity_container_year_link_type.ALLOCATION_ENTITY)
        attributions['additional_requirement_entity_1'] = \
            all_attributions.get(entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1)
        attributions['additional_requirement_entity_2'] = \
            all_attributions.get(entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_2)
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
    components = mdl_base.learning_unit_component.find_by_learning_component_year(a_learning_component_year)
    return ", ".join(["{} ({})".format(
        c.learning_unit_year.acronym,
        _(c.learning_unit_year.quadrimester) if c.learning_unit_year.quadrimester else '?'
    ) for c in components])


def _learning_unit_usage_by_class(a_learning_class_year):
    queryset = mdl_base.learning_unit_component_class.find_by_learning_class_year(a_learning_class_year) \
        .order_by('learning_unit_component__learning_unit_year__acronym') \
        .values_list('learning_unit_component__learning_unit_year__acronym', flat=True)
    return ", ".join(list(queryset))


def get_components_identification(learning_unit_yr):
    a_learning_container_yr = learning_unit_yr.learning_container_year
    components = []
    additionnal_entities = {}

    if a_learning_container_yr:
        learning_component_year_list = mdl_base.learning_component_year.find_by_learning_container_year(
            a_learning_container_yr)

        for learning_component_year in learning_component_year_list:
            if mdl_base.learning_unit_component.search(learning_component_year, learning_unit_yr).exists():
                entity_components_yr = EntityComponentYear.objects.filter(
                    learning_component_year=learning_component_year)
                if not additionnal_entities:
                    additionnal_entities = _get_entities(entity_components_yr)

                components.append({'learning_component_year': learning_component_year,
                                   'entity_component_yr': entity_components_yr.first(),
                                   'volumes': volume_learning_component_year(learning_component_year,
                                                                             entity_components_yr)})

    return _compose_components_dict(components, additionnal_entities)


def _is_used_by_full_learning_unit_year(a_learning_class_year):
    for l in mdl_base.learning_unit_component_class.find_by_learning_class_year(a_learning_class_year):
        if l.learning_unit_component.learning_unit_year.subdivision is None:
            return True

    return False


def prepare_xls_content(found_learning_units):
    return [extract_xls_data_from_learning_unit(lu) for lu in found_learning_units]


def extract_xls_data_from_learning_unit(learning_unit_yr):
    return [
        learning_unit_yr.academic_year.name, learning_unit_yr.acronym, learning_unit_yr.complete_title,
        xls_build.translate(learning_unit_yr.learning_container_year.container_type)
        # FIXME Condition to remove when the LearningUnitYear.learning_continer_year_id will be null=false
        if learning_unit_yr.learning_container_year else "",
        xls_build.translate(learning_unit_yr.subtype),
        get_entity_acronym(learning_unit_yr.entities.get('REQUIREMENT_ENTITY')),
        get_entity_acronym(learning_unit_yr.entities.get('ALLOCATION_ENTITY')),
        learning_unit_yr.credits, xls_build.translate(learning_unit_yr.status)
    ]


def get_entity_acronym(an_entity):
    return an_entity.acronym if an_entity else None


def create_xls(user, found_learning_units, filters):
    titles = LEARNING_UNIT_TITLES_PART1 + LEARNING_UNIT_TITLES_PART2
    working_sheets_data = prepare_xls_content(found_learning_units)
    parameters = {xls_build.DESCRIPTION: XLS_DESCRIPTION,
                  xls_build.USER: get_name_or_username(user),
                  xls_build.FILENAME: XLS_FILENAME,
                  xls_build.HEADER_TITLES: titles,
                  xls_build.WS_TITLE: WORKSHEET_TITLE}

    return xls_build.generate_xls(xls_build.prepare_xls_parameters_list(working_sheets_data, parameters), filters)


def is_summary_submission_opened():
    current_academic_year = mdl_base.academic_year.current_academic_year()
    return mdl_base.academic_calendar.\
        is_academic_calendar_opened_for_specific_academic_year(current_academic_year,
                                                               academic_calendar_type.SUMMARY_COURSE_SUBMISSION)


def find_language_in_settings(language_code):
    return next((lang for lang in settings.LANGUAGES if lang[0] == language_code), None)


def _compose_components_dict(components, additional_entities):
    data_components = {'components': components}
    data_components.update(additional_entities)
    return data_components


def _get_entities(entity_components_yr):
    return {e.entity_container_year.type: e.entity_container_year.entity.most_recent_acronym
            for e in entity_components_yr
            if e.entity_container_year.type in REQUIREMENT_ENTITIES}


def _get_summary_status(a_calendar, cms_list, lu):
    for educational_information in cms_list:
        if educational_information.reference == lu.id \
                and _changed_in_period(a_calendar.start_date, educational_information.changed):
            return True
    return False


def _get_calendar(academic_yr, an_entity_version):
    a_calendar = get_entity_calendar(an_entity_version, academic_yr)
    if a_calendar is None:
        a_calendar = academic_calendar.get_by_reference_and_academic_year(
            academic_calendar_type.SUMMARY_COURSE_SUBMISSION,
            academic_yr
        )
    return a_calendar


def _get_summary_detail(a_calendar, cms_list, entity_learning_unit_yr_list_param):
    entity_learning_unit_yr_list = entity_learning_unit_yr_list_param
    for lu in entity_learning_unit_yr_list:
        lu.summary_responsibles = attribution.search(summary_responsible=True,
                                                     learning_unit_year=lu)
        lu.summary_status = _get_summary_status(a_calendar, cms_list, lu)
    return entity_learning_unit_yr_list


def _changed_in_period(start_date, changed_date):
    return convert_date_to_datetime(start_date) <= changed_date


def get_learning_units_and_summary_status(learning_unit_years):
    learning_units_found = []
    cms_list = translated_text.find_with_changed(LEARNING_UNIT_YEAR, CMS_LABEL_PEDAGOGY)
    for learning_unit_yr in learning_unit_years:
        learning_units_found.extend(_get_learning_unit_by_luy_entity(cms_list, learning_unit_yr))
    return learning_units_found


def _get_learning_unit_by_luy_entity(cms_list, learning_unit_yr):
    requirement_entity = learning_unit_yr.entities.get('REQUIREMENT_ENTITY', None)
    if requirement_entity:
        a_calendar = _get_calendar(learning_unit_yr.academic_year.past(), requirement_entity)
        if a_calendar:
            return _get_summary_detail(a_calendar, cms_list, [learning_unit_yr])
    return []


def get_achievements_group_by_language(learning_unit_year):
    achievement_grouped = {}
    all_achievements = learning_achievement.find_by_learning_unit_year(learning_unit_year)
    for achievement in all_achievements:
        key = 'achievements_{}'.format(achievement.language.code)
        achievement_grouped.setdefault(key, []).append(achievement)
    return achievement_grouped


def get_no_summary_responsible_teachers(learning_unit_yr, summary_responsibles):
    tutors = find_all_tutors_by_learning_unit_year(learning_unit_yr, "-summary_responsible")
    return [tutor[0] for tutor in tutors if tutor[0] not in summary_responsibles]


def get_learning_unit_comparison_context(learning_unit_year):
    context = dict({'learning_unit_year': learning_unit_year})
    context['campus'] = learning_unit_year.campus
    context['organization'] = get_organization_from_learning_unit_year(learning_unit_year)
    context['experimental_phase'] = True
    components = get_components_identification(learning_unit_year)
    context['components'] = components.get('components')
    context['REQUIREMENT_ENTITY'] = get_entity_by_type(learning_unit_year,
                                                       entity_container_year_link_type.REQUIREMENT_ENTITY)
    context['ALLOCATION_ENTITY'] = get_entity_by_type(learning_unit_year,
                                                      entity_container_year_link_type.ALLOCATION_ENTITY)
    context['ADDITIONAL_REQUIREMENT_ENTITY_1'] = \
        get_entity_by_type(learning_unit_year, entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1)
    context['ADDITIONAL_REQUIREMENT_ENTITY_2'] = \
        get_entity_by_type(learning_unit_year, entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_2)
    context['learning_container_year_partims'] = learning_unit_year.get_partims_related()
    return context
