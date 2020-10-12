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
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from base.models.enums.education_group_types import TrainingType
from base.tests.factories.admission_condition import AdmissionConditionFactory
from base.tests.factories.education_group_year import EducationGroupYearCommonMasterFactory
from education_group.views.serializers import admission_condition


class TestGetCommonAdmissionConditionSerializer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.common_training_120 = EducationGroupYearCommonMasterFactory(academic_year__year=2018)
        cls.common_admission_training_120 = AdmissionConditionFactory(education_group_year=cls.common_training_120)
        cls.common_training_120_condition_serialized = {
            'alert_message': {
                'label_translated': _('Alert Message'),
                'text_fr': cls.common_admission_training_120.text_alert_message,
                'text_en': cls.common_admission_training_120.text_alert_message_en
            },
            'general_conditions': {
                'label_translated': _('General Conditions'),
                'text_fr': cls.common_admission_training_120.text_ca_cond_generales,
                'text_en': cls.common_admission_training_120.text_ca_cond_generales_en
            },
            'specific_conditions': {
                'label_translated': _('Specific Conditions'),
                'text_fr': cls.common_admission_training_120.text_ca_bacs_cond_particulieres,
                'text_en':  cls.common_admission_training_120.text_ca_bacs_cond_particulieres_en,
            },
            'language_exam': {
                'label_translated': _('Language Exam'),
                'text_fr': cls.common_admission_training_120.text_ca_bacs_examen_langue,
                'text_en': cls.common_admission_training_120.text_ca_bacs_examen_langue_en
            },
            'special_conditions': {
                'label_translated': _('Special Conditions'),
                'text_fr': cls.common_admission_training_120.text_ca_bacs_cond_speciales,
                'text_en': cls.common_admission_training_120.text_ca_bacs_cond_speciales_en
            },
            'french_proficiency_examination': {
                'label_translated': _('French language proficiency examination'),
                'text_fr': cls.common_admission_training_120.text_ca_maitrise_fr,
                'text_en': cls.common_admission_training_120.text_ca_maitrise_fr_en
            },
            'subscription_lightening': {
                'label_translated': _('Reduction'),
                'text_fr': cls.common_admission_training_120.text_ca_allegement,
                'text_en': cls.common_admission_training_120.text_ca_allegement_en
            },
            'opening_to_adults': {
                'label_translated': _('Opening to Adults'),
                'text_fr': cls.common_admission_training_120.text_ca_ouv_adultes,
                'text_en': cls.common_admission_training_120.text_ca_ouv_adultes_en
            },
            'non_university_bachelors': {
                'label_translated': _('Non university Bachelors'),
                'text_fr': cls.common_admission_training_120.text_non_university_bachelors,
                'text_en': cls.common_admission_training_120.text_non_university_bachelors_en
            },
            'adults_taking_up_university_training': {
                'label_translated': _('Adults taking up their university training'),
                'text_fr': cls.common_admission_training_120.text_adults_taking_up_university_training,
                'text_en': cls.common_admission_training_120.text_adults_taking_up_university_training_en
            },
            'personalized_access': {
                'label_translated': _('Personalized access'),
                'text_fr': cls.common_admission_training_120.text_personalized_access,
                'text_en': cls.common_admission_training_120.text_personalized_access_en
            },
            'admission_enrollment_procedures': {
                'label_translated': _('Admission and Enrolment Procedures for general registration'),
                'text_fr': cls.common_admission_training_120.text_admission_enrollment_procedures,
                'text_en': cls.common_admission_training_120.text_admission_enrollment_procedures_en
            }
        }

    def test_assert_return_admission_of_pgrm_120_when_offer_type_is_master_60(self):
        self.assertDictEqual(
            admission_condition.get_common_admission_condition(TrainingType.MASTER_M1.name, 2018),
            self.common_training_120_condition_serialized
        )

    def test_assert_return_admission_of_pgrm_120_when_offer_type_is_master_180_240(self):
        self.assertDictEqual(
            admission_condition.get_common_admission_condition(TrainingType.PGRM_MASTER_180_240.name, 2018),
            self.common_training_120_condition_serialized
        )
