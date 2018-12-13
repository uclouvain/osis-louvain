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
import collections
import functools
import re

from django.core.exceptions import SuspiciousOperation
from django.db.models import Q
from django.http import Http404
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.generics import get_object_or_404
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from base.models.admission_condition import AdmissionCondition, AdmissionConditionLine
from base.models.education_group_year import EducationGroupYear
from cms.enums.entity_name import OFFER_YEAR
from cms.models.text_label import TextLabel
from cms.models.translated_text import TranslatedText
from cms.models.translated_text_label import TranslatedTextLabel
from webservices import business
from webservices.business import get_evaluation_text, get_common_evaluation_text
from webservices.utils import convert_sections_to_list_of_dict

LANGUAGES = {'fr': 'fr-be', 'en': 'en'}
INTRO_PATTERN = r'intro-(?P<acronym>\w+)'
COMMON_PATTERN = r'(?P<section_name>\w+)-commun'
ACRONYM_PATTERN = re.compile(r'(?P<prefix>[a-z]+)(?P<cycle>[0-9]{1,3})(?P<suffix>[a-z]+)(?P<year>[0-9]?)')

Context = collections.namedtuple(
    'Context',
    ['year', 'language', 'acronym', 'suffix_language',
     'title', 'description',
     'academic_year', 'education_group_year']
)


class AcronymError(Exception):
    pass


def new_description(education_group_year, language, title, acronym):
    return {
        'language': language,
        'acronym': acronym,
        'title': title,
        'year': int(education_group_year.academic_year.year),
        'sections': [],
    }


def get_title_of_education_group_year(education_group_year, iso_language):
    if iso_language == 'fr-be':
        title = education_group_year.title
    else:
        title = education_group_year.title_english
    return title


def validate_json_request(request, year, acronym):
    if request.content_type != 'application/json':
        raise SuspiciousOperation('Invalid JSON')

    request_json = request.data

    if 'anac' not in request_json or 'code_offre' not in request_json or 'sections' not in request_json:
        raise SuspiciousOperation('Invalid JSON')

    if year != int(request_json['anac']):
        raise SuspiciousOperation('Invalid JSON')

    if acronym.lower() != request_json['code_offre'].lower():
        raise SuspiciousOperation('Invalid JSON')

    if not all(isinstance(item, str) for item in request_json['sections']):
        raise SuspiciousOperation('Invalid JSON')


@api_view(['POST'])
@renderer_classes((JSONRenderer,))
def ws_catalog_offer(request, year, language, acronym):
    # Validation
    education_group_year, iso_language, year = parameters_validation(acronym, language, year)

    validate_json_request(request, year, acronym)

    # Processing
    context = new_context(education_group_year, iso_language, language, acronym)
    items = request.data['sections']

    sections = process_message(context, education_group_year, items)

    context.description['sections'] = convert_sections_to_list_of_dict(sections)
    context.description['sections'].append(get_conditions_admissions(context))
    return Response(context.description, content_type='application/json')


def process_message(context, education_group_year, items):
    sections = collections.OrderedDict()
    for item in items:
        section = process_section(context, education_group_year, item)
        if section is not None:
            sections[item] = section
    return sections


def process_section(context, education_group_year, item):
    assert isinstance(context, Context)
    assert isinstance(education_group_year, EducationGroupYear)
    assert isinstance(item, str) and item.strip()

    m_intro = re.match(INTRO_PATTERN, item)
    m_common = re.match(COMMON_PATTERN, item)
    if m_intro or m_common:
        return get_intro_or_common_section(context, education_group_year, m_intro, m_common)
    elif item == business.SKILLS_AND_ACHIEVEMENTS_KEY:
        return get_skills_and_achievements(education_group_year, context.language)
    elif item == business.EVALUATION_KEY:
        return get_evaluation(education_group_year, context.language)
    elif item == business.CONTACTS_KEY:
        return get_contacts(education_group_year, context.language)
    else:
        text_label = TextLabel.objects.filter(entity=OFFER_YEAR, label=item).first()
        if text_label:
            return insert_section(context, education_group_year, text_label)
    return None


def get_intro_or_common_section(context, education_group_year, m_intro, m_common):
    if m_intro:
        egy = EducationGroupYear.objects.filter(partial_acronym__iexact=m_intro.group('acronym'),
                                                academic_year__year=context.year).first()

        text_label = TextLabel.objects.filter(entity=OFFER_YEAR, label='intro').first()

        return insert_section_if_checked(context, egy, text_label)
    elif m_common:
        egy = EducationGroupYear.objects.get_common(
            academic_year=education_group_year.academic_year
        )
        text_label = TextLabel.objects.filter(
            entity=OFFER_YEAR,
            label=m_common.group('section_name')
        ).first()
        return insert_section_if_checked(context, egy, text_label)


def new_context(education_group_year, iso_language, language, original_acronym):
    assert isinstance(education_group_year, EducationGroupYear)
    assert isinstance(iso_language, str) and iso_language in ('fr-be', 'en')
    assert isinstance(language, str) and language in ('fr', 'en')
    assert isinstance(original_acronym, str)

    title = get_title_of_education_group_year(education_group_year, iso_language)
    partial_acronym = education_group_year.partial_acronym.upper()
    acronym = education_group_year.acronym.upper()

    is_partial = original_acronym.upper() == partial_acronym

    final_acronym = partial_acronym if is_partial else acronym
    description = new_description(education_group_year, language, title, final_acronym)
    context = Context(
        acronym=final_acronym,
        year=int(education_group_year.academic_year.year),
        title=title,
        description=description,
        education_group_year=education_group_year,
        academic_year=education_group_year.academic_year,
        language=iso_language,
        suffix_language='' if iso_language == 'fr-be' else '_en'
    )
    return context


def parameters_validation(acronym, language, year):
    assert isinstance(acronym, str)
    assert isinstance(language, str)
    assert isinstance(year, (str, int))

    year = int(year)
    iso_language = LANGUAGES.get(language)
    if not iso_language:
        raise Http404
    education_group_year = get_object_or_404(EducationGroupYear,
                                             Q(acronym__iexact=acronym) | Q(partial_acronym__iexact=acronym),
                                             academic_year__year=year)
    return education_group_year, iso_language, year


def insert_section(context, education_group_year, text_label):
    assert isinstance(context, Context)
    assert isinstance(education_group_year, EducationGroupYear)
    assert isinstance(text_label, TextLabel)

    translated_text_label = TranslatedTextLabel.objects.filter(text_label=text_label,
                                                               language=context.language).first()

    translated_text = TranslatedText.objects.filter(text_label=text_label,
                                                    language=context.language,
                                                    entity=text_label.entity,
                                                    reference=education_group_year.id).first()
    if translated_text_label and translated_text:
        return {'label': translated_text_label.label, 'content': translated_text.text}
    elif translated_text_label:
        return {'label': translated_text_label.label, 'content': None}
    return {'label': None, 'content': None}


def insert_section_if_checked(context, education_group_year, text_label):
    if education_group_year and text_label:
        return insert_section(context, education_group_year, text_label)
    return {'label': None, 'content': None}


def admission_condition_line_to_dict(context, admission_condition_line):
    fields = ('diploma', 'conditions', 'remarks')

    result = {
        field: (getattr(admission_condition_line, field + context.suffix_language) or '').strip() or None
        for field in fields
    }

    result['access'] = admission_condition_line.get_access_display()
    return result


def get_value_from_ac(admission_condition, field, context):
    return getattr(admission_condition, 'text_{}{}'.format(field, context.suffix_language)) or None


def response_for_bachelor(context):
    education_group_year = EducationGroupYear.objects.filter(acronym__iexact='common-1ba',
                                                             academic_year=context.academic_year).first()

    result = {
        'id': 'conditions_admission',
        "label": "conditions_admission",
        "content": None,
    }

    if education_group_year:
        admission_condition, created = AdmissionCondition.objects.get_or_create(
            education_group_year=education_group_year
        )
        get_value = functools.partial(get_value_from_ac, admission_condition=admission_condition, context=context)

        fields = ('alert_message', 'ca_bacs_cond_generales', 'ca_bacs_cond_particulieres',
                  'ca_bacs_examen_langue',
                  'ca_bacs_cond_speciales')

        result['content'] = {field: get_value(field=field) for field in fields}

    return result


def build_content_response(context, admission_condition, admission_condition_common, acronym_suffix):
    get_value = functools.partial(get_value_from_ac, admission_condition=admission_condition_common, context=context)

    response = {
        "free_text": getattr(admission_condition, 'text_free' + context.suffix_language) or None,
    }

    if acronym_suffix in ('2a', '2mc'):
        fields = ('alert_message', 'ca_cond_generales', 'ca_maitrise_fr', 'ca_allegement', 'ca_ouv_adultes')

        response.update({field: get_value(field=field) for field in fields})

    if acronym_suffix in ('2m', '2m1'):
        response.update(build_response_for_master(context, admission_condition, admission_condition_common))

    return response


def build_response_for_master(context, admission_condition, admission_condition_common):
    admission_condition_lines = AdmissionConditionLine.objects.filter(admission_condition=admission_condition)
    group_by_section_name = collections.defaultdict(list)
    for item in admission_condition_lines:
        group_by_section_name[item.section].append(admission_condition_line_to_dict(context, item))

    get_texts = functools.partial(get_texts_for_section,
                                  admission_condition=admission_condition,
                                  admission_condition_common=admission_condition_common,
                                  lang=context.suffix_language)

    alert_message = None
    if admission_condition_common:
        alert_message = getattr(admission_condition_common, 'text_alert_message' + context.suffix_language, '')

    sections = build_response_master_sections(admission_condition,
                                              get_texts,
                                              group_by_section_name,
                                              context.suffix_language)
    return {
        "alert_message": alert_message,
        "sections": sections
    }


def build_response_master_sections(admission_condition, get_texts, group_by_section_name, lang):
    return {
        "university_bachelors": build_response_for_master_university_bachelors(admission_condition,
                                                                               group_by_section_name, lang),
        "non_university_bachelors": get_texts('text_non_university_bachelors'),
        "holders_second_university_degree": build_response_for_master_holders_second_university_degree(
            admission_condition, group_by_section_name, lang),
        "holders_non_university_second_degree": {
            "text": getattr(admission_condition, 'text_holders_non_university_second_degree' + lang) or None,
        },
        "adults_taking_up_university_training": get_texts('text_adults_taking_up_university_training'),
        "personalized_access": get_texts('text_personalized_access'),
        "admission_enrollment_procedures": get_texts('text_admission_enrollment_procedures'),
    }


def build_response_for_master_holders_second_university_degree(admission_condition, group_by_section_name, lang):
    return {
        "text": getattr(admission_condition, 'text_holders_second_university_degree' + lang) or None,
        "records": {
            "graduates": group_by_section_name['graduates'],
            "masters": group_by_section_name['masters']
        }
    }


def build_response_for_master_university_bachelors(admission_condition, group_by_section_name, lang):
    return {
        "text": getattr(admission_condition, 'text_university_bachelors' + lang) or None,
        "records": {
            "ucl_bachelors": group_by_section_name['ucl_bachelors'],
            "others_bachelors_french": group_by_section_name['others_bachelors_french'],
            "bachelors_dutch": group_by_section_name['bachelors_dutch'],
            "foreign_bachelors": group_by_section_name['foreign_bachelors'],
        }
    }


def get_texts_for_section(column_name, admission_condition, admission_condition_common, lang):
    column = column_name + lang
    return {
        "text": getattr(admission_condition, column) or None,
        "text-common": getattr(admission_condition_common, column) if admission_condition_common else None
    }


def get_conditions_admissions(context):
    acronym_match = re.match(ACRONYM_PATTERN, context.acronym.lower())
    if not acronym_match:
        raise AcronymError("The acronym does not match the pattern")

    acronym_suffix = acronym_match.group('suffix').lower()

    full_suffix = '{cycle}{suffix}{year}'.format(**acronym_match.groupdict())

    is_bachelor = acronym_suffix == 'ba'

    if is_bachelor:
        # special case, if it's a bachelor, just return the text for the bachelor
        return response_for_bachelor(context)

    common_acronym = 'common-{}'.format(full_suffix)
    if common_acronym == 'common-2m1':
        common_acronym = 'common-2m'
    admission_condition, created = AdmissionCondition.objects.get_or_create(
        education_group_year=context.education_group_year
    )

    admission_condition_common = AdmissionCondition.objects.filter(
        education_group_year__acronym__iexact=common_acronym).first()

    result = {
        'id': 'conditions_admission',
        "label": "conditions_admission",
        "content": build_content_response(context, admission_condition, admission_condition_common, full_suffix)
    }
    return result


def get_evaluation(education_group_year, language_code):

    label, text = get_evaluation_text(education_group_year, language_code)
    common_text = get_common_evaluation_text(education_group_year, language_code)

    return {
        'id': business.EVALUATION_KEY,
        'label': label,
        'content': common_text,
        'free_text': text
    }


def get_skills_and_achievements(education_group_year, language_code):
    intro_extra_content = business.get_intro_extra_content_achievements(education_group_year, language_code)
    achievements = business.get_achievements(education_group_year, language_code)

    return {
        'id': business.SKILLS_AND_ACHIEVEMENTS_KEY,
        'label': business.SKILLS_AND_ACHIEVEMENTS_KEY,
        'content': {
            'intro': intro_extra_content.get('skills_and_achievements_introduction') or None,
            'blocs': achievements,
            'extra': intro_extra_content.get('skills_and_achievements_additional_text') or None
        }
    }


def get_contacts(education_group_year, language_code):
    contacts = business.get_contacts_group_by_types(education_group_year, language_code)
    intro_content = business.get_contacts_intro_text(education_group_year, language_code)
    entity_version = education_group_year.publication_contact_entity_version

    return {
        'id': business.CONTACTS_KEY,
        'label': business.CONTACTS_KEY,
        'content': {
            'text': intro_content,
            'entity': entity_version.acronym if entity_version else None,
            'contacts': contacts
        }
    }
