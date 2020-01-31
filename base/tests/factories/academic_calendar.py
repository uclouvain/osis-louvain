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
import datetime
import operator
import string

import factory.fuzzy

from base.models.enums import academic_calendar_type
from base.tests.factories.academic_year import AcademicYearFactory


class AcademicCalendarFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'base.AcademicCalendar'
        django_get_or_create = ('academic_year', 'title')

    external_id = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    changed = factory.fuzzy.FuzzyNaiveDateTime(datetime.datetime(2016, 1, 1), datetime.datetime(2017, 3, 1))

    academic_year = factory.SubFactory(AcademicYearFactory)
    data_year = factory.SubFactory(AcademicYearFactory)
    title = factory.Sequence(lambda n: 'Academic Calendar - %d' % n)
    start_date = factory.SelfAttribute("academic_year.start_date")
    end_date = factory.SelfAttribute("academic_year.end_date")
    highlight_title = factory.Sequence(lambda n: 'Highlight - %d' % n)
    highlight_description = factory.Sequence(lambda n: 'Description - %d' % n)
    highlight_shortcut = factory.Sequence(lambda n: 'Shortcut Highlight - %d' % n)
    reference = factory.Iterator(academic_calendar_type.ACADEMIC_CALENDAR_TYPES, getter=operator.itemgetter(0))


class OpenAcademicCalendarFactory(AcademicCalendarFactory):
    start_date = factory.Faker('past_date')
    end_date = factory.Faker('future_date')


class CloseAcademicCalendarFactory(AcademicCalendarFactory):
    start_date = factory.LazyAttribute(lambda obj: datetime.date.today() - datetime.timedelta(days=3))
    end_date = factory.LazyAttribute(lambda obj: datetime.date.today() - datetime.timedelta(days=1))


class AcademicCalendarExamSubmissionFactory(AcademicCalendarFactory):
    reference = academic_calendar_type.SCORES_EXAM_SUBMISSION


class AcademicCalendarSummaryCourseSubmissionFactory(AcademicCalendarFactory):
    reference = academic_calendar_type.SUMMARY_COURSE_SUBMISSION


class AcademicCalendarEducationGroupEditionFactory(AcademicCalendarFactory):
    reference = academic_calendar_type.EDUCATION_GROUP_EDITION


class AcademicCalendarLearningUnitCentralEditionFactory(AcademicCalendarFactory):
    reference = academic_calendar_type.LEARNING_UNIT_EDITION_CENTRAL_MANAGERS


class AcademicCalendarLearningUnitFacultyEditionFactory(AcademicCalendarFactory):
    reference = academic_calendar_type.LEARNING_UNIT_EDITION_FACULTY_MANAGERS


class AcademicCalendarCreationEndDateProposalCentralManagerFactory(AcademicCalendarFactory):
    reference = academic_calendar_type.CREATION_OR_END_DATE_PROPOSAL_CENTRAL_MANAGERS


class AcademicCalendarCreationEndDateProposalFacultyManagerFactory(AcademicCalendarFactory):
    reference = academic_calendar_type.CREATION_OR_END_DATE_PROPOSAL_FACULTY_MANAGERS


class AcademicCalendarModificationTransformationProposalCentralManagerFactory(AcademicCalendarFactory):
    reference = academic_calendar_type.MODIFICATION_OR_TRANSFORMATION_PROPOSAL_CENTRAL_MANAGERS


class AcademicCalendarModificationTransformationProposalFacultyManagerFactory(AcademicCalendarFactory):
    reference = academic_calendar_type.MODIFICATION_OR_TRANSFORMATION_PROPOSAL_FACULTY_MANAGERS


def generate_creation_or_end_date_proposal_calendars(academic_years):
    [
        AcademicCalendarCreationEndDateProposalCentralManagerFactory(
            data_year=academic_year,
            start_date=datetime.datetime(academic_year.year - 6, 9, 15),
            end_date=datetime.datetime(academic_year.year + 1, 9, 14)
        )
        for academic_year in academic_years
    ]
    [
        AcademicCalendarCreationEndDateProposalFacultyManagerFactory(
            data_year=academic_year,
            start_date=datetime.datetime(academic_year.year - 6, 9, 15),
            end_date=datetime.datetime(academic_year.year, 9, 14)
        )
        for academic_year in academic_years
    ]


def generate_modification_transformation_proposal_calendars(academic_years):
    [
        AcademicCalendarModificationTransformationProposalCentralManagerFactory(
            data_year=academic_year,
            start_date=datetime.datetime(academic_year.year - 1, 9, 15),
            end_date=datetime.datetime(academic_year.year + 1, 9, 14)
        )
        for academic_year in academic_years
    ]
    [
        AcademicCalendarModificationTransformationProposalFacultyManagerFactory(
            data_year=academic_year,
            start_date=datetime.datetime(academic_year.year - 1, 9, 15),
            end_date=datetime.datetime(academic_year.year, 9, 14)
        )
        for academic_year in academic_years
    ]


def generate_learning_unit_edition_calendars(academic_years):
    [
        AcademicCalendarLearningUnitFacultyEditionFactory(
            data_year=academic_year,
            start_date=datetime.datetime(academic_year.year - 2, 9, 15),
            end_date=datetime.datetime(academic_year.year + 1, 9, 14)
        )
        for academic_year in academic_years
    ]
    [
        AcademicCalendarLearningUnitCentralEditionFactory(
            data_year=academic_year,
            start_date=datetime.datetime(academic_year.year - 6, 9, 15),
            end_date=datetime.datetime(academic_year.year + 1, 9, 14)
        )
        for academic_year in academic_years
    ]
