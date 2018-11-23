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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import operator

import factory.fuzzy

from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_categories, active_status, schedule_type
from base.models.enums.constraint_type import CREDITS
from base.models.enums.duration_unit import DURATION_UNIT
from base.models.enums.education_group_types import TrainingType
from base.models.learning_unit_year import MAXIMUM_CREDITS, MINIMUM_CREDITS
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.campus import CampusFactory
from base.tests.factories.education_group import EducationGroupFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.entity import EntityFactory


def generate_title(education_group_year):
    return '{obj.academic_year} {obj.acronym}'.format(obj=education_group_year).lower()


class EducationGroupYearFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EducationGroupYear

    education_group = factory.SubFactory(EducationGroupFactory)
    academic_year = factory.SubFactory(AcademicYearFactory)
    acronym = factory.Sequence(lambda n: 'ED%d' % n)
    partial_acronym = factory.Sequence(lambda n: 'SCS%03dT' % n)
    title = factory.LazyAttribute(generate_title)
    title_english = factory.LazyAttribute(generate_title)
    education_group_type = factory.SubFactory(EducationGroupTypeFactory)
    management_entity = factory.SubFactory(EntityFactory)
    administration_entity = factory.SubFactory(EntityFactory)
    main_teaching_campus = factory.SubFactory(CampusFactory)
    credits = factory.fuzzy.FuzzyInteger(MINIMUM_CREDITS, MAXIMUM_CREDITS)
    min_constraint = factory.fuzzy.FuzzyInteger(MINIMUM_CREDITS, MAXIMUM_CREDITS)
    max_constraint = factory.lazy_attribute(lambda a: a.min_constraint)
    remark = factory.fuzzy.FuzzyText(length=255)
    remark_english = factory.fuzzy.FuzzyText(length=255)
    active = active_status.ACTIVE
    schedule_type = schedule_type.DAILY
    weighting = False
    default_learning_unit_enrollment = False
    duration_unit = factory.Iterator(DURATION_UNIT, getter=operator.itemgetter(0))
    duration = factory.fuzzy.FuzzyInteger(1, 5)
    constraint_type = CREDITS


class MiniTrainingFactory(EducationGroupYearFactory):
    education_group_type = factory.SubFactory('base.tests.factories.education_group_type.EducationGroupTypeFactory',
                                              category=education_group_categories.MINI_TRAINING)


class TrainingFactory(EducationGroupYearFactory):
    education_group_type = factory.SubFactory('base.tests.factories.education_group_type.EducationGroupTypeFactory',
                                              category=education_group_categories.TRAINING)


class GroupFactory(EducationGroupYearFactory):
    education_group_type = factory.SubFactory('base.tests.factories.education_group_type.EducationGroupTypeFactory',
                                              category=education_group_categories.GROUP)


class EducationGroupYearCommonBachelorFactory(EducationGroupYearFactory):
    acronym = 'common-1ba'
    education_group_type = factory.SubFactory(
        'base.tests.factories.education_group_type.ExistingEducationGroupTypeFactory',
        name=TrainingType.BACHELOR.name
    )


class EducationGroupYearCommonMasterFactory(EducationGroupYearFactory):
    acronym = 'common-2m'
    education_group_type = factory.SubFactory(
        'base.tests.factories.education_group_type.ExistingEducationGroupTypeFactory',
        name=TrainingType.PGRM_MASTER_120.name
    )


class EducationGroupYearMasterFactory(EducationGroupYearCommonMasterFactory):
    acronym = 'actu2m'
