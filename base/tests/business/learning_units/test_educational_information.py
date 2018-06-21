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
import datetime
from django.test import TestCase

from base.tests.factories.person import PersonFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFakerFactory
from attribution.tests.factories.attribution import AttributionFactory
from base.business.learning_units.educational_information import get_responsible_and_learning_unit_yr_list, PERSON, \
    LEARNING_UNIT_YEARS, _update_responsible_data_with_new_learning_unit_yr, _is_updating_period_opening_today, \
    get_summary_responsible_list
from base.tests.factories.tutor import TutorFactory
from base.tests.factories.academic_year import create_current_academic_year
from base.models.enums.academic_calendar_type import SUMMARY_COURSE_SUBMISSION
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_calendar import EntityCalendarFactory
from base.tests.factories.entity_version import EntityVersionFactory
from django.utils import timezone
from base.tests.factories.business.learning_units import GenerateContainer
from attribution.tests.models import test_attribution
from base.tests.factories.tutor import TutorFactory
from base.tests.factories.person import PersonFactory
from base.models.tutor import Tutor


class TestEducationalInformation(TestCase):

    def setUp(self):
        self.learning_unit_year_1 = LearningUnitYearFakerFactory()
        self.person_lu_1 = PersonFactory()
        self.tutor_lu1_1 = TutorFactory(person=self.person_lu_1)
        self.attribution_lu1 = AttributionFactory(learning_unit_year=self.learning_unit_year_1, tutor=self.tutor_lu1_1)
        self.learning_unit_year_1.summary_status = False
        self.learning_unit_year_1.summary_responsibles = [self.attribution_lu1]

        self.learning_unit_year_2 = LearningUnitYearFakerFactory()
        self.person_lu_2 = PersonFactory()
        self.tutor_lu1_2_1 = TutorFactory(person=self.person_lu_2)
        self.person_lu_3 = PersonFactory()
        self.tutor_lu2_2_2 = TutorFactory(person=self.person_lu_3)
        self.attribution_lu2_1 = AttributionFactory(learning_unit_year=self.learning_unit_year_2,
                                                    tutor=self.tutor_lu1_2_1)
        self.attribution_lu2_2 = AttributionFactory(learning_unit_year=self.learning_unit_year_2,
                                                    tutor=self.tutor_lu2_2_2)
        self.learning_unit_year_2.summary_status = False
        self.learning_unit_year_2.summary_responsibles = [self.attribution_lu2_1, self.attribution_lu2_2]

        self.learning_unit_year_3 = LearningUnitYearFakerFactory()
        self.attribution_lu3 = AttributionFactory(learning_unit_year=self.learning_unit_year_3, tutor=self.tutor_lu1_1)
        self.learning_unit_year_3.summary_status = False
        self.learning_unit_year_3.summary_responsibles = [self.attribution_lu3]

    def test_get_learning_unit_yr_list_with_one_responsible(self):
        learning_units = get_responsible_and_learning_unit_yr_list([self.learning_unit_year_1])
        self.assertCountEqual(learning_units, [
            {PERSON: self.attribution_lu1.tutor.person, LEARNING_UNIT_YEARS: [self.learning_unit_year_1]}])

    def test_get_learning_unit_yr_list_with_two_responsibles(self):
        learning_units = get_responsible_and_learning_unit_yr_list([self.learning_unit_year_2])
        self.assertCountEqual(learning_units, [
            {PERSON: self.attribution_lu2_1.tutor.person, LEARNING_UNIT_YEARS: [self.learning_unit_year_2]},
            {PERSON: self.attribution_lu2_2.tutor.person, LEARNING_UNIT_YEARS: [self.learning_unit_year_2]}])

    def test_get_learning_unit_yr_one_person_with_several_learning_unit_for_which_he_is_responsible(self):
        learning_units = get_responsible_and_learning_unit_yr_list(
            [self.learning_unit_year_1, self.learning_unit_year_3])
        self.assertCountEqual(learning_units, [
            {PERSON: self.tutor_lu1_1.person,
             LEARNING_UNIT_YEARS: [self.learning_unit_year_1, self.learning_unit_year_3]}])

    def test_get_learning_unit_yr_list_with_summary_already_updated(self):
        learning_unit_year_updated = LearningUnitYearFakerFactory()
        learning_unit_year_updated.summary_status = True
        learning_units = get_responsible_and_learning_unit_yr_list([learning_unit_year_updated])
        self.assertCountEqual(learning_units, [])

    def test_update_responsible_data_with_new_learning_unit_yr(self):
        list_before_update = [{PERSON: self.person_lu_2,
                               LEARNING_UNIT_YEARS: []}]
        self.assertEqual(_update_responsible_data_with_new_learning_unit_yr(self.person_lu_1,
                                                                            self.learning_unit_year_2,
                                                                            list_before_update), list_before_update)


class TestOpenedPeriod(TestCase):

    def setUp(self):
        self.current_academic_year = create_current_academic_year()
        self.now_date = timezone.now().date()
        self.NOT_TODAY_DATE = timezone.now() - datetime.timedelta(days=1)
        self.an_academic_calendar = AcademicCalendarFactory.build(academic_year=self.current_academic_year,
                                                                  reference=SUMMARY_COURSE_SUBMISSION,
                                                                  start_date=timezone.now(),
                                                                  end_date=timezone.now())
        self.an_academic_calendar.save()

    def test_no_entity_calendar(self):
        an_orphan_entity = EntityFactory()
        EntityVersionFactory(entity=an_orphan_entity,
                             start_date=self.current_academic_year.start_date,
                             end_date=self.current_academic_year.end_date)
        # If no entity calendar check the academic calendar
        self.assertTrue(_is_updating_period_opening_today(an_orphan_entity))
        self.an_academic_calendar.start_date = datetime.date(self.current_academic_year.year + 1, 1, 1)
        self.an_academic_calendar.end_date = datetime.date(self.current_academic_year.year + 1, 1, 2)
        self.an_academic_calendar.save()
        self.assertFalse(_is_updating_period_opening_today(an_orphan_entity))

    def test_with_entity_calendar(self):
        an_entity = EntityFactory()
        EntityVersionFactory(entity=an_entity,
                             start_date=self.current_academic_year.start_date,
                             end_date=self.current_academic_year.end_date)
        an_entity_calendar = EntityCalendarFactory(entity=an_entity,
                                                   academic_calendar=self.an_academic_calendar,
                                                   start_date=self.an_academic_calendar.start_date)
        self.assertTrue(_is_updating_period_opening_today(an_entity))
        self.modify_entity_calendar_dates_to_not_today(an_entity_calendar)
        self.assertFalse(_is_updating_period_opening_today(an_entity))

    def modify_entity_calendar_dates_to_not_today(self, an_entity_calendar):
        an_entity_calendar.start_date = self.NOT_TODAY_DATE
        an_entity_calendar.end_date = self.NOT_TODAY_DATE + datetime.timedelta(days=1)
        an_entity_calendar.save()

    def test_a_child_entity_without_entity_calendar(self):
        # If no entity calendar for a child entity check the parent entity calendar
        a_parent_entity = EntityFactory()
        EntityVersionFactory(entity=a_parent_entity,
                             start_date=self.current_academic_year.start_date,
                             end_date=self.current_academic_year.end_date)

        EntityCalendarFactory(entity=a_parent_entity,
                              academic_calendar=self.an_academic_calendar,
                              start_date=self.an_academic_calendar.start_date,
                              end_date=self.an_academic_calendar.end_date)

        a_children_entity_without_entity_calendar = EntityFactory()
        EntityVersionFactory(entity=a_children_entity_without_entity_calendar,
                             start_date=self.current_academic_year.start_date,
                             end_date=self.current_academic_year.end_date,
                             parent=a_parent_entity)

        self.assertTrue(_is_updating_period_opening_today(a_children_entity_without_entity_calendar))
        # If the parent has no entity calendar either check the academic calendar
        a_parent_entity_without_entity_calendar = EntityFactory()
        EntityVersionFactory(entity=a_parent_entity_without_entity_calendar,
                             start_date=self.current_academic_year.start_date,
                             end_date=self.current_academic_year.end_date,
                             parent=a_parent_entity)

    def test_a_child_entity_without_entity_calendar_check_academic_calendar(self):
        # If no entity calendar for a child entity check the parent calendar
        # If the parent has no entity calendar either check the academic calendar
        a_parent_entity = EntityFactory()
        EntityVersionFactory(entity=a_parent_entity,
                             start_date=self.current_academic_year.start_date,
                             end_date=self.current_academic_year.end_date)

        a_children_entity_without_entity_calendar = EntityFactory()
        EntityVersionFactory(entity=a_children_entity_without_entity_calendar,
                             start_date=self.current_academic_year.start_date,
                             end_date=self.current_academic_year.end_date,
                             parent=a_parent_entity)

        self.assertTrue(_is_updating_period_opening_today(a_children_entity_without_entity_calendar))
        self.an_academic_calendar.start_date = self.NOT_TODAY_DATE
        self.an_academic_calendar.save()
        self.assertFalse(_is_updating_period_opening_today(a_children_entity_without_entity_calendar))


class TestSummaryResponsibleList(TestCase):

    def setUp(self):
        current_academic_year = create_current_academic_year()
        generated_container = GenerateContainer(start_year=current_academic_year.year,
                                                end_year=current_academic_year.year)
        generated_container_first_year = generated_container.generated_container_years[0]
        self.allocation_entity_1 = generated_container_first_year.allocation_entity_container_year.entity
        self.luy = generated_container_first_year.learning_unit_year_full
        self.person = PersonFactory()
        create_attribution(self.person, True, self.luy)
        self.person_2 = PersonFactory()
        create_attribution(self.person_2, False, self.luy)
        generated_container_2 = GenerateContainer(start_year=current_academic_year.year,
                                                  end_year=current_academic_year.year)
        generated_container_first_year_2 = generated_container_2.generated_container_years[0]
        self.allocation_entity_2 = generated_container_first_year_2.allocation_entity_container_year.entity
        self.luy_2 = generated_container_first_year_2.learning_unit_year_full
        # self.person_3 = PersonFactory()
        # create_attribution(self.person, True, self.luy_2)

        tutor_1 = Tutor.objects.get(person=self.person)
        test_attribution.create_attribution(
            tutor=tutor_1,
            learning_unit_year=self.luy_2,
            summary_responsible=True)

    def test_get_summary_responsible_list_with_one_entity(self):
        l = get_summary_responsible_list(self.allocation_entity_1, {})
        self.assertEqual(l, {self.person: [self.allocation_entity_1]})

    def test_get_summary_responsible_list_with_several_entities_for_a_person(self):
        l_1 = get_summary_responsible_list(self.allocation_entity_1, {})
        l_2 = get_summary_responsible_list(self.allocation_entity_2, l_1)
        self.assertEqual(l_2, {self.person: [self.allocation_entity_1, self.allocation_entity_2]})


def create_attribution(a_person, summary_responsible, a_luy):
    tutor = TutorFactory(person=a_person)
    test_attribution.create_attribution(
        tutor=tutor,
        learning_unit_year=a_luy,
        summary_responsible=summary_responsible)
