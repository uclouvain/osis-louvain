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
import factory.fuzzy

from base.models.enums.academic_type import AcademicTypes
from base.models.enums.activity_presence import ActivityPresence
from base.models.enums.decree_category import DecreeCategories
from base.models.enums.duration_unit import DurationUnitsEnum
from base.models.enums.education_group_types import TrainingType
from base.models.enums.internship_presence import InternshipPresence
from base.models.enums.rate_code import RateCode
from base.models.enums.schedule_type import ScheduleTypeEnum
from education_group.ddd.domain.training import Training, TrainingIdentity, TrainingIdentityThroughYears
from education_group.tests.ddd.factories.campus import CampusIdentityFactory
from education_group.tests.ddd.factories.co_graduation import CoGraduationFactory
from education_group.tests.ddd.factories.diploma import DiplomaFactory
from education_group.tests.ddd.factories.entity import EntityFactory
from education_group.tests.ddd.factories.funding import FundingFactory
from education_group.tests.ddd.factories.hops import HOPSFactory
from education_group.tests.ddd.factories.isced_domain import IscedDomainFactory
from education_group.tests.ddd.factories.language import LanguageFactory
from education_group.tests.ddd.factories.study_domain import StudyDomainFactory
from education_group.tests.ddd.factories.titles import TitlesFactory


def generate_end_date(training):
    return training.entity_identity.year + 10


class TrainingIdentityFactory(factory.Factory):
    class Meta:
        model = TrainingIdentity
        abstract = False

    acronym = factory.Sequence(lambda n: 'Acronym%02d' % n)
    year = factory.fuzzy.FuzzyInteger(1999, 2099)


class TrainingIdentityThroughYearsFactory(factory.Factory):
    class Meta:
        model = TrainingIdentityThroughYears
        abstract = False

    uuid = factory.Sequence(lambda n: n + 1)


class TrainingFactory(factory.Factory):
    class Meta:
        model = Training
        abstract = False

    entity_identity = factory.SubFactory(TrainingIdentityFactory)
    entity_id = factory.LazyAttribute(lambda o: o.entity_identity)
    identity_through_years = factory.SubFactory(TrainingIdentityThroughYearsFactory)
    type = factory.fuzzy.FuzzyChoice(TrainingType)
    credits = factory.fuzzy.FuzzyDecimal(0, 10, precision=1)
    schedule_type = factory.fuzzy.FuzzyChoice(ScheduleTypeEnum)
    duration = factory.fuzzy.FuzzyInteger(1, 5)
    start_year = factory.fuzzy.FuzzyInteger(1999, 2099)
    titles = factory.SubFactory(TitlesFactory)
    keywords = factory.fuzzy.FuzzyText()
    internship_presence = factory.fuzzy.FuzzyChoice(InternshipPresence)
    is_enrollment_enabled = True
    has_online_re_registration = True
    has_partial_deliberation = True
    has_admission_exam = True
    has_dissertation = True
    produce_university_certificate = True
    decree_category = factory.fuzzy.FuzzyChoice(DecreeCategories)
    rate_code = factory.fuzzy.FuzzyChoice(RateCode)
    main_language = factory.SubFactory(LanguageFactory)
    english_activities = factory.fuzzy.FuzzyChoice(ActivityPresence)
    other_language_activities = factory.fuzzy.FuzzyChoice(ActivityPresence)
    internal_comment = factory.fuzzy.FuzzyText()
    main_domain = factory.SubFactory(StudyDomainFactory)
    secondary_domains = None
    isced_domain = factory.SubFactory(IscedDomainFactory)
    management_entity = factory.SubFactory(EntityFactory)
    administration_entity = factory.SubFactory(EntityFactory)
    end_year = factory.LazyAttribute(generate_end_date)
    teaching_campus = factory.SubFactory(CampusIdentityFactory)
    enrollment_campus = factory.SubFactory(CampusIdentityFactory)
    other_campus_activities = factory.fuzzy.FuzzyChoice(ActivityPresence)
    funding = factory.SubFactory(FundingFactory)
    hops = factory.SubFactory(HOPSFactory)
    co_graduation = factory.SubFactory(CoGraduationFactory)
    co_organizations = []
    academic_type = factory.fuzzy.FuzzyChoice(AcademicTypes)
    duration_unit = factory.fuzzy.FuzzyChoice(DurationUnitsEnum)
    diploma = factory.SubFactory(DiplomaFactory)
