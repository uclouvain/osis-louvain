##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.db.models import F, When, CharField, Case
from django.utils.translation import gettext_lazy as _

from base.models.admission_condition import AdmissionCondition, AdmissionConditionLine
from base.models.enums.education_group_types import TrainingType


def get_admission_condition(acronym: str, year: int):
    try:
        admission_condition = AdmissionCondition.objects.filter(
            education_group_year__acronym=acronym,
            education_group_year__academic_year__year=year
        ).annotate(
            admission_requirements_fr=F('text_free'),
            admission_requirements_en=F('text_free_en'),
            non_university_bachelors_fr=F('text_non_university_bachelors'),
            non_university_bachelors_en=F('text_non_university_bachelors_en'),
            holders_non_university_second_degree_fr=F('text_holders_non_university_second_degree'),
            holders_non_university_second_degree_en=F('text_holders_non_university_second_degree_en'),
            adults_taking_up_university_training_fr=F('text_adults_taking_up_university_training'),
            adults_taking_up_university_training_en=F('text_adults_taking_up_university_training_en'),
            personalized_access_fr=F('text_personalized_access'),
            personalized_access_en=F('text_personalized_access_en'),
            admission_enrollment_procedures_fr=F('text_admission_enrollment_procedures'),
            admission_enrollment_procedures_en=F('text_admission_enrollment_procedures_en'),
        ).values(
            'admission_requirements_fr',
            'admission_requirements_en',
            'non_university_bachelors_fr',
            'non_university_bachelors_en',
            'holders_non_university_second_degree_fr',
            'holders_non_university_second_degree_en',
            'adults_taking_up_university_training_fr',
            'adults_taking_up_university_training_en',
            'personalized_access_fr',
            'personalized_access_en',
            'admission_enrollment_procedures_fr',
            'admission_enrollment_procedures_en',
        ).get()
    except AdmissionCondition.DoesNotExist:
        return __default_admission_condition()
    return __format_admission_condition(admission_condition)


def __format_admission_condition(admission_condition):
    admission_condition_formated = __default_admission_condition()
    for key, label in admission_condition_formated.items():
        label['text_fr'] = admission_condition[key + "_fr"]
        label['text_en'] = admission_condition[key + "_en"]
    return admission_condition_formated


def __default_admission_condition():
    return {
        'admission_requirements': {
            'label_translated': _('Specific admission requirements'),
            'text_fr': '',
            'text_en': ''
        },
        'non_university_bachelors': {
            'label_translated': _('Non university Bachelors'),
            'text_fr': '',
            'text_en': ''
        },
        'holders_non_university_second_degree': {
            'label_translated': _('Holders of a non-University 2nd cycle degree'),
            'text_fr': '',
            'text_en': ''
        },
        'adults_taking_up_university_training': {
            'label_translated': _('Adults taking up their university training'),
            'text_fr': '',
            'text_en': ''
        },
        'personalized_access': {
            'label_translated': _('Personalized access'),
            'text_fr': '',
            'text_en': ''
        },
        'admission_enrollment_procedures': {
            'label_translated': _('Admission and Enrolment Procedures for general registration'),
            'text_fr': '',
            'text_en': ''
        }
    }


def get_admission_condition_lines(acronym: str, year: int, language: str):
    admission_condition_sections = (
        'ucl_bachelors',
        'others_bachelors_french',
        'bachelors_dutch',
        'foreign_bachelors',
        'graduates',
        'masters',
    )

    admission_conditions_lines = {}
    for section in admission_condition_sections:
        admission_conditions_lines[section] = AdmissionConditionLine.objects.filter(
            admission_condition__education_group_year__acronym=acronym,
            admission_condition__education_group_year__academic_year__year=year,
            section=section
        ).annotate_text(language)
    return admission_conditions_lines


def get_common_admission_condition(offer_type: str, year: int):
    try:
        common_of_same_type = AdmissionCondition.objects.filter(
            education_group_year__acronym__startswith='common-',
            education_group_year__academic_year__year=year,
            education_group_year__education_group_type__name=offer_type
        ).annotate(
            alert_message_fr=F('text_alert_message'),
            alert_message_en=F('text_alert_message_en'),
            general_conditions_fr=Case(
               When(
                    education_group_year__education_group_type__name=TrainingType.BACHELOR.name,
                    then=F('text_ca_bacs_cond_generales')
               ),
               default=F('text_ca_cond_generales'),
               output_field=CharField(),
            ),
            general_conditions_en=Case(
               When(
                    education_group_year__education_group_type__name=TrainingType.BACHELOR.name,
                    then=F('text_ca_bacs_cond_generales_en')
               ),
               default=F('text_ca_cond_generales_en'),
               output_field=CharField(),
            ),
            specific_conditions_fr=F('text_ca_bacs_cond_particulieres'),
            specific_conditions_en=F('text_ca_bacs_cond_particulieres_en'),
            language_exam_fr=F('text_ca_bacs_examen_langue'),
            language_exam_en=F('text_ca_bacs_examen_langue_en'),
            special_conditions_fr=F('text_ca_bacs_cond_speciales'),
            special_conditions_en=F('text_ca_bacs_cond_speciales_en'),
            french_proficiency_examination_fr=F('text_ca_maitrise_fr'),
            french_proficiency_examination_en=F('text_ca_maitrise_fr_en'),
            subscription_lightening_fr=F('text_ca_allegement'),
            subscription_lightening_en=F('text_ca_allegement_en'),
            opening_to_adults_fr=F('text_ca_ouv_adultes'),
            opening_to_adults_en=F('text_ca_ouv_adultes_en'),
            non_university_bachelors_fr=F('text_non_university_bachelors'),
            non_university_bachelors_en=F('text_non_university_bachelors_en'),
            adults_taking_up_university_training_fr=F('text_adults_taking_up_university_training'),
            adults_taking_up_university_training_en=F('text_adults_taking_up_university_training_en'),
            personalized_access_fr=F('text_personalized_access'),
            personalized_access_en=F('text_personalized_access_en'),
            admission_enrollment_procedures_fr=F('text_admission_enrollment_procedures'),
            admission_enrollment_procedures_en=F('text_admission_enrollment_procedures_en'),
        ).values(
            'alert_message_fr',
            'alert_message_en',
            'general_conditions_fr',
            'general_conditions_en',
            'specific_conditions_fr',
            'specific_conditions_en',
            'language_exam_fr',
            'language_exam_en',
            'special_conditions_fr',
            'special_conditions_en',
            'french_proficiency_examination_fr',
            'french_proficiency_examination_en',
            'subscription_lightening_fr',
            'subscription_lightening_en',
            'opening_to_adults_fr',
            'opening_to_adults_en',
            'non_university_bachelors_fr',
            'non_university_bachelors_en',
            'adults_taking_up_university_training_fr',
            'adults_taking_up_university_training_en',
            'personalized_access_fr',
            'personalized_access_en',
            'admission_enrollment_procedures_fr',
            'admission_enrollment_procedures_en',
        ).get()
    except AdmissionCondition.DoesNotExist:
        return __default_common_admission_condition()
    return __format_common_admission_condition(common_of_same_type)


def __default_common_admission_condition():
    return {
        'alert_message': {
            'label_translated': _('Alert Message'),
            'text_fr': '',
            'text_en': ''
        },
        'general_conditions': {
            'label_translated': _('General Conditions'),
            'text_fr': '',
            'text_en': ''
        },
        'specific_conditions': {
            'label_translated': _('Specific Conditions'),
            'text_fr': '',
            'text_en': ''
        },
        'language_exam': {
            'label_translated': _('Language Exam'),
            'text_fr': '',
            'text_en': ''
        },
        'special_conditions': {
            'label_translated': _('Special Conditions'),
            'text_fr': '',
            'text_en': ''
        },
        'french_proficiency_examination': {
            'label_translated': _('French language proficiency examination'),
            'text_fr': '',
            'text_en': ''
        },
        'subscription_lightening': {
            'label_translated': _('Reduction'),
            'text_fr': '',
            'text_en': ''
        },
        'opening_to_adults': {
            'label_translated': _('Opening to Adults'),
            'text_fr': '',
            'text_en': ''
        },
        'non_university_bachelors': {
            'label_translated': _('Non university Bachelors'),
            'text_fr': '',
            'text_en': ''
        },
        'adults_taking_up_university_training': {
            'label_translated': _('Adults taking up their university training'),
            'text_fr': '',
            'text_en': ''
        },
        'personalized_access': {
            'label_translated': _('Personalized access'),
            'text_fr': '',
            'text_en': ''
        },
        'admission_enrollment_procedures': {
            'label_translated': _('Admission and Enrolment Procedures for general registration'),
            'text_fr': '',
            'text_en': ''
        }
    }


def __format_common_admission_condition(common_admission_condition):
    admission_condition_formated = __default_common_admission_condition()
    for key, label in admission_condition_formated.items():
        label['text_fr'] = common_admission_condition[key + "_fr"]
        label['text_en'] = common_admission_condition[key + "_en"]
    return admission_condition_formated
