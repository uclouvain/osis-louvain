##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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
import operator
import random
import string

import exrex
import factory.fuzzy

from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_categories, active_status, schedule_type
from base.models.enums.constraint_type import CREDITS
from base.models.enums.duration_unit import DURATION_UNIT
from base.models.enums.education_group_types import TrainingType, MiniTrainingType
from base.models.learning_unit_year import MAXIMUM_CREDITS, MINIMUM_CREDITS
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.campus import CampusFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.entity import EntityFactory
from reference.tests.factories.language import LanguageFactory


def string_generator(nb_char=8):
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(nb_char))


def generate_title(education_group_year):
    if education_group_year.acronym:
        return '{obj.academic_year} {obj.acronym}'.format(obj=education_group_year).lower()
    return '{obj.academic_year} {gen_str}'.format(obj=education_group_year, gen_str=string_generator()).lower()


def generate_partial_acronym():
    sigle_ele = "".join(random.sample(string.ascii_uppercase, k=5))
    cnum = "".join(random.sample(string.digits, k=3))
    subdivision = random.choice(string.ascii_uppercase)
    return "{sigle_ele}{cnum}{subdivision}".format(
        sigle_ele=sigle_ele,
        cnum=cnum,
        subdivision=subdivision
    )


class EducationGroupYearFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EducationGroupYear
        django_get_or_create = ('partial_acronym', 'academic_year',)

    education_group = factory.SubFactory("base.tests.factories.education_group.EducationGroupFactory")
    academic_year = factory.SubFactory(AcademicYearFactory)
    acronym = ""
    partial_acronym = ""
    title = factory.LazyAttribute(generate_title)
    title_english = factory.LazyAttribute(generate_title)
    partial_title = ""
    partial_title_english = ""
    education_group_type = factory.SubFactory(EducationGroupTypeFactory)
    management_entity = factory.SubFactory(EntityFactory)
    administration_entity = factory.SubFactory(EntityFactory)
    main_teaching_campus = factory.SubFactory(CampusFactory)
    credits = factory.fuzzy.FuzzyInteger(MINIMUM_CREDITS, MAXIMUM_CREDITS)
    min_constraint = factory.fuzzy.FuzzyInteger(1, MAXIMUM_CREDITS)
    max_constraint = factory.lazy_attribute(lambda a: a.min_constraint)
    remark = factory.fuzzy.FuzzyText(length=255)
    remark_english = factory.fuzzy.FuzzyText(length=255)
    active = active_status.ACTIVE
    schedule_type = schedule_type.DAILY
    weighting = True
    default_learning_unit_enrollment = False
    duration_unit = factory.Iterator(DURATION_UNIT, getter=operator.itemgetter(0))
    duration = factory.fuzzy.FuzzyInteger(1, 5)
    constraint_type = CREDITS
    linked_with_epc = False
    primary_language = factory.SubFactory(LanguageFactory)
    enrollment_campus = factory.SubFactory(CampusFactory)
    diploma_printing_title = "Yolo"

    @factory.post_generation
    def gen_acronym(self, create, extracted, **kwargs):
        try:
            if self.acronym == '':
                self.acronym = exrex.getone(self.rules['acronym'].regex_rule).upper()
        except KeyError:
            self.acronym = string_generator(6)

    @factory.post_generation
    def gen_partial_acronym(self, create, extracted, **kwargs):
        try:
            if self.partial_acronym == "":
                self.partial_acronym = exrex.getone(self.rules['partial_acronym'].regex_rule).upper()
        except KeyError:
            self.partial_acronym = generate_partial_acronym()


class MiniTrainingFactory(EducationGroupYearFactory):
    education_group_type__minitraining = True


class TrainingFactory(EducationGroupYearFactory):
    education_group_type = factory.SubFactory('base.tests.factories.education_group_type.EducationGroupTypeFactory',
                                              category=education_group_categories.TRAINING)


class GroupFactory(EducationGroupYearFactory):
    education_group_type__group = True


class EducationGroupYearCommonBachelorFactory(EducationGroupYearFactory):
    acronym = 'common-1ba'
    partial_acronym = 'common-1ba'
    education_group_type = factory.SubFactory(
        'base.tests.factories.education_group_type.EducationGroupTypeFactory',
        name=TrainingType.BACHELOR.name,
        category=education_group_categories.TRAINING
    )


class EducationGroupYearBachelorFactory(EducationGroupYearCommonBachelorFactory):
    acronym = 'actu1ba'
    partial_acronym = 'actu1ba'


class EducationGroupYearCommonAgregationFactory(EducationGroupYearFactory):
    acronym = 'common-2a'
    partial_acronym = 'common-2a'
    education_group_type = factory.SubFactory(
        'base.tests.factories.education_group_type.EducationGroupTypeFactory',
        name=TrainingType.AGGREGATION.name,
        category=education_group_categories.TRAINING
    )


class EducationGroupYearCommonSpecializedMasterFactory(EducationGroupYearFactory):
    acronym = 'common-2mc'
    partial_acronym = 'common-2mc'
    education_group_type = factory.SubFactory(
        'base.tests.factories.education_group_type.EducationGroupTypeFactory',
        name=TrainingType.MASTER_MC.name,
        category=education_group_categories.TRAINING
    )


class EducationGroupYearCommonMasterFactory(EducationGroupYearFactory):
    acronym = 'common-2m'
    partial_acronym = 'common-2m'
    education_group_type = factory.SubFactory(
        'base.tests.factories.education_group_type.EducationGroupTypeFactory',
        name=TrainingType.PGRM_MASTER_120.name,
        category=education_group_categories.TRAINING
    )


class EducationGroupYearMasterFactory(EducationGroupYearCommonMasterFactory):
    acronym = 'actu2m'
    partial_acronym = 'actu2m'


class EducationGroupYearCommonFactory(EducationGroupYearFactory):
    acronym = 'common'
    partial_acronym = 'common'
    education_group_type = factory.SubFactory(
        'base.tests.factories.education_group_type.EducationGroupTypeFactory',
        name=MiniTrainingType.DEEPENING.name,
        category=education_group_categories.MINI_TRAINING
    )
