from django.db.models import F
from django.utils.translation import gettext_lazy as _

from base.models.admission_condition import AdmissionCondition
from base.models.education_group_year import EducationGroupYear


def get_admission_condition(offer: EducationGroupYear):
    try:
        admission_condition = AdmissionCondition.objects.filter(
            education_group_year=offer
        ).select_related(
            'education_group_year'
        ).annotate(
            admission_requirements_fr=F('text_free'),
            admission_requirements_en=F('text_free_en')
        ).get()
    except AdmissionCondition.DoesNotExist:
        return __default_admission_condition(offer)
    return __format_admission_condition(admission_condition)


def __format_admission_condition(admission_condition):
    bachelor_sections = [
        'ca_bacs_cond_generales', 'ca_bacs_cond_particulieres', 'ca_bacs_examen_langue', 'ca_bacs_cond_speciales',
    ]
    master_sections = ['ca_cond_generales', 'ca_maitrise_fr', 'ca_allegement', 'ca_ouv_adultes']
    sections = [
        'university_bachelors', 'non_university_bachelors', 'holders_second_university_degree', 'personalized_access',
        'holders_non_university_second_degree', 'adults_taking_up_university_training', 'alert_message',
        'admission_enrollment_procedures'
    ]
    admission_condition_formated = __default_admission_condition(admission_condition.education_group_year)
    admission_condition_formated['admission_requirements'].update({
        'text_fr': admission_condition.admission_requirements_fr,
        'text_en': admission_condition.admission_requirements_en
    })
    for section in sections + bachelor_sections + master_sections:
        admission_condition_formated[section].update({
            'text_fr': getattr(admission_condition, 'text_' + section),
            'text_en': getattr(admission_condition, 'text_' + section + '_en')
        })
    return admission_condition_formated


def __default_admission_condition(offer: EducationGroupYear):
    default_texts = {
        'text_fr': '',
        'text_en': ''
    }
    return {
        'alert_message': {
            'label_translated': _('Alert Message'),
            'display': True,  # To edit
            **default_texts
        },
        'ca_bacs_cond_generales': {
            'label_translated': _('General Conditions'),
            'display': offer.is_bachelor,
            **default_texts
        },
        'ca_bacs_cond_particulieres': {
            'label_translated': _('Specific Conditions'),
            'display': offer.is_bachelor,
            **default_texts
        },
        'ca_bacs_examen_langue': {
            'label_translated': _('Language Exam'),
            'display': offer.is_bachelor,
            **default_texts
        },
        'ca_bacs_cond_speciales': {
            'label_translated': _('Special Conditions'),
            'display': offer.is_bachelor,
            **default_texts
        },
        'admission_requirements': {
            'label_translated': _('Specific admission requirements'),
            'display': not offer.is_common,
            **default_texts
        },
        'ca_cond_generales': {
            'label_translated': _('General Conditions'),
            'display': offer.is_specialized_master or offer.is_aggregation,
            **default_texts
        },
        'ca_maitrise_fr': {
            'label_translated': _('French language proficiency examination'),
            'display': offer.is_aggregation,
            **default_texts
        },
        'ca_allegement': {
            'label_translated': _('Reduction'),
            'display': offer.is_aggregation,
            **default_texts
        },
        'ca_ouv_adultes': {
            'label_translated': _('Opening to Adults'),
            'display': offer.is_aggregation,
            **default_texts
        },
        'university_bachelors': {
            'label_translated': _('University Bachelors'),
            'display': not offer.is_common and offer.is_a_master,
            **default_texts
        },
        'non_university_bachelors': {
            'label_translated': _('Non university Bachelors'),
            'display': offer.is_a_master,
            **default_texts
        },
        'holders_second_university_degree': {
            'label_translated': _('Holders of a 2nd cycle University degree'),
            'display': not offer.is_common and offer.is_a_master,
            **default_texts
        },
        'holders_non_university_second_degree': {
            'label_translated': _('Holders of a non-University 2nd cycle degree'),
            'display': not offer.is_common and offer.is_a_master,
            **default_texts
        },
        'adults_taking_up_university_training': {
            'label_translated': _('Adults taking up their university training'),
            'display': offer.is_a_master,
            **default_texts
        },
        'personalized_access': {
            'label_translated': _('Personalized access'),
            'display': offer.is_a_master,
            **default_texts
        },
        'admission_enrollment_procedures': {
            'label_translated': _('Admission and Enrolment Procedures for general registration'),
            'display': offer.is_a_master,
            **default_texts
        },
    }
