# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from datetime import datetime

from django.test import TestCase
from django.utils.translation import gettext

from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.tasks import check_academic_calendar
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory


class TestCheckAcademicCalendar(TestCase):

    def test_check_academic_calendar(self):
        current_egy = EducationGroupYearFactory()
        old_year = AcademicYearFactory(year=current_egy.academic_year.year - 1)

        EducationGroupYearFactory(academic_year=old_year, education_group=current_egy.education_group)

        now = datetime.now().date()
        AcademicCalendarFactory(
            start_date=now, end_date=now,
            reference=AcademicCalendarTypes.EDUCATION_GROUP_EDITION.name,
            data_year=current_egy.academic_year
        )

        result = check_academic_calendar.run()
        self.assertTrue("Copy of Reddot data" in result)
        self.assertEqual(
            result["Copy of Reddot data"]["msg"],
            gettext("%(number_extended)s object(s) extended and %(number_error)s error(s)") % {
                "number_extended": 1,
                "number_error": 0
            })
