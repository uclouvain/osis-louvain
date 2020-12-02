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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################

import factory.fuzzy

from base.tests.factories.education_group_year import EducationGroupYearFactory


class AdmissionConditionFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'base.AdmissionCondition'

    text_alert_message = factory.Faker(
        'paragraph',
        nb_sentences=1,
        variable_nb_sentences=True
    )

    education_group_year = factory.SubFactory(EducationGroupYearFactory)

    text_free = factory.Faker('sentence', nb_words=2)

    text_university_bachelors = factory.Faker('sentence', nb_words=2)

    text_non_university_bachelors = factory.Faker('sentence', nb_words=2)

    text_holders_second_university_degree = factory.Faker('sentence', nb_words=2)
    text_holders_non_university_second_degree = factory.Faker('sentence', nb_words=2)

    text_adults_taking_up_university_training = factory.Faker('sentence', nb_words=2)
    text_personalized_access = factory.Faker('sentence', nb_words=2)
    text_admission_enrollment_procedures = factory.Faker('sentence', nb_words=2)

    text_ca_bacs_cond_generales = factory.Faker('sentence', nb_words=2)
    text_ca_bacs_cond_particulieres = factory.Faker('sentence', nb_words=2)
    text_ca_bacs_examen_langue = factory.Faker('sentence', nb_words=2)
    text_ca_bacs_cond_speciales = factory.Faker('sentence', nb_words=2)

    text_ca_cond_generales = factory.Faker('sentence', nb_words=2)
    text_ca_maitrise_fr = factory.Faker('sentence', nb_words=2)
    text_ca_allegement = factory.Faker('sentence', nb_words=2)
    text_ca_ouv_adultes = factory.Faker('sentence', nb_words=2)

    # English
    text_alert_message_en = factory.Faker('sentence', nb_words=2)
    text_free_en = factory.Faker('sentence', nb_words=2)

    text_university_bachelors_en = factory.Faker('sentence', nb_words=2)

    text_non_university_bachelors_en = factory.Faker('sentence', nb_words=2)

    text_holders_second_university_degree_en = factory.Faker('sentence', nb_words=2)
    text_holders_non_university_second_degree_en = factory.Faker('sentence', nb_words=2,
                                                                 )

    text_adults_taking_up_university_training_en = factory.Faker('sentence', nb_words=2,
                                                                 )
    text_personalized_access_en = factory.Faker('sentence', nb_words=2)
    text_admission_enrollment_procedures_en = factory.Faker('sentence', nb_words=2)

    text_ca_bacs_cond_generales_en = factory.Faker('sentence', nb_words=2)
    text_ca_bacs_cond_particulieres_en = factory.Faker('sentence', nb_words=2)
    text_ca_bacs_examen_langue_en = factory.Faker('sentence', nb_words=2)
    text_ca_bacs_cond_speciales_en = factory.Faker('sentence', nb_words=2)

    text_ca_cond_generales_en = factory.Faker('sentence', nb_words=2)
    text_ca_maitrise_fr_en = factory.Faker('sentence', nb_words=2)
    text_ca_allegement_en = factory.Faker('sentence', nb_words=2)
    text_ca_ouv_adultes_en = factory.Faker('sentence', nb_words=2)


class AdmissionConditionLineFactory(factory.DjangoModelFactory):
    class Meta:
        model = "base.AdmissionConditionLine"

    admission_condition = factory.SubFactory(AdmissionConditionFactory)
    section = factory.Faker('sentence', nb_words=2)
