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
from gettext import ngettext

from django.contrib.messages import get_messages
from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from base.models import learning_unit
from base.models.enums import learning_unit_year_subtypes
from base.templatetags.learning_unit import academic_years, academic_year
from base.tests.factories.academic_year import AcademicYearFactory, get_current_year
from base.tests.factories.business.learning_units import GenerateAcademicYear
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.user import SuperUserFactory


def create_learning_unit(acronym, title):
    return LearningUnitFactory(acronym=acronym, title=title, start_year=2010)


class LearningUnitTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.start_year_2014 = AcademicYearFactory(year=2014)
        cls.start_year_2015 = AcademicYearFactory(year=2015)
        cls.start_year_2017 = AcademicYearFactory(year=2017)
        cls.end_year_2018 = AcademicYearFactory(year=2018)

    def test_create_learning_unit_with_start_year_higher_than_end_year(self):
        l_unit = LearningUnitFactory.build(start_year=self.start_year_2017, end_year=self.start_year_2015)
        with self.assertRaises(AttributeError):
            l_unit.save()

    def test_get_partims_related(self):
        current_year = datetime.date.today().year
        academic_year = AcademicYearFactory(year=current_year)
        l_container_year = LearningContainerYearFactory(academic_year=academic_year)
        l_container_year_2 = LearningContainerYearFactory(academic_year=academic_year)
        # Create learning unit year attached to learning container year
        LearningUnitYearFactory(academic_year=academic_year,
                                                       learning_container_year=l_container_year,
                                                       subtype=learning_unit_year_subtypes.FULL)
        LearningUnitYearFactory(academic_year=academic_year,
                                learning_container_year=l_container_year,
                                subtype=learning_unit_year_subtypes.PARTIM)
        LearningUnitYearFactory(academic_year=academic_year,
                                learning_container_year=l_container_year,
                                subtype=learning_unit_year_subtypes.PARTIM)
        LearningUnitYearFactory(academic_year=academic_year,
                                                       learning_container_year=l_container_year_2,
                                                       subtype=learning_unit_year_subtypes.FULL)
        LearningUnitYearFactory(academic_year=academic_year, learning_container_year=None)

        all_partims_container_year_1 = l_container_year.get_partims_related()
        self.assertEqual(len(all_partims_container_year_1), 2)
        all_partims_container_year_2 = l_container_year_2.get_partims_related()
        self.assertEqual(len(all_partims_container_year_2), 0)

    def test_academic_years_tags(self):
        self.assertEqual(academic_years(self.start_year_2017, self.end_year_2018), _('From').title() + " 2017-18 " + _('to').lower() + " 2018-19")
        self.assertEqual(academic_years(None, self.end_year_2018), "-")
        self.assertEqual(academic_years(self.start_year_2017, None),
                         _('From').title() + " 2017-18 (" + _('no planned end').lower() + ")")
        self.assertEqual(academic_years(None, None), "-")

    def test_academic_year_tags(self):
        self.assertEqual(academic_year(self.start_year_2017), "2017-18")
        self.assertEqual(academic_year(None), "-")

    def test_learning_unit_start_end_year_constraint(self):
        # Case same year for start/end
        LearningUnitFactory(start_year=self.start_year_2017, end_year=self.start_year_2017)

        # Case end_year < start year
        with self.assertRaises(AttributeError):
            LearningUnitFactory(start_year=self.start_year_2017, end_year=self.start_year_2015)

        # Case end year > start year
        LearningUnitFactory(start_year=self.start_year_2017, end_year=self.end_year_2018)

    def test_delete_before_2015(self):
        lu = LearningUnitFactory(start_year=self.start_year_2014, end_year=self.start_year_2017)

        with self.assertRaises(DatabaseError):
            lu.delete()

        lu.start_year = self.start_year_2015
        lu.delete()

    def test_properties_acronym_and_title(self):
        a_learning_unit = LearningUnitFactory()
        a_learning_unit_year = LearningUnitYearFactory(learning_unit=a_learning_unit)
        self.assertEqual(a_learning_unit.title, a_learning_unit_year.specific_title)
        self.assertEqual(a_learning_unit.acronym, a_learning_unit_year.acronym)


class LearningUnitGetByAcronymWithLatestAcademicYearTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.learning_unit_year_2009 = LearningUnitYearFactory(
            academic_year=AcademicYearFactory(year=2009),
            acronym='LDROI1200'
        )
        cls.learning_unit_year_2017 = LearningUnitYearFactory(
            academic_year=AcademicYearFactory(year=2017),
            acronym='LDROI1200'
        )

    def test_get_by_acronym_with_highest_academic_year(self):
        self.assertEqual(
            learning_unit.get_by_acronym_with_highest_academic_year(acronym='LDROI1200'),
            self.learning_unit_year_2017.learning_unit
        )


class TestLearningUnitAdmin(TestCase):
    def test_apply_learning_unit_year_postponement(self):
        """ Postpone to N+6 in Learning Unit Admin """
        current_year = get_current_year()
        start_year = AcademicYearFactory(year=current_year)
        end_year = AcademicYearFactory(year=current_year + 6)
        academic_years = GenerateAcademicYear(start_year, end_year)

        lu = LearningUnitFactory(end_year=None)
        LearningUnitYearFactory(
            academic_year=academic_years[0],
            learning_unit=lu,
            learning_container_year__requirement_entity=None,
            learning_container_year__allocation_entity=None,
        )

        postpone_url = reverse('admin:base_learningunit_changelist')

        self.client.force_login(SuperUserFactory())
        response = self.client.post(postpone_url, data={'action': 'apply_learning_unit_year_postponement',
                                                        '_selected_action': [lu.pk]})

        msg = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(msg[0], ngettext(
            "%(count)d learning unit has been postponed with success",
            "%(count)d learning units have been postponed with success", 1
        ) % {'count': 1})
