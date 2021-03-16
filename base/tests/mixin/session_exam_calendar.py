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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from unittest.mock import patch

from base.business.event_perms import AcademicSessionEvent
from base.models import session_exam_calendar

# TODO :: to remove
class SessionExamCalendarMockMixin:
    """
        This mixin allow mocking function current_session_exam() in order to decouple test from system time
    """
    def mock_session_exam_calendar(self, current_session_exam=None):
        return_value = None
        if current_session_exam:
            return_value = AcademicSessionEvent(
                session=current_session_exam.number_session,
                start_date=current_session_exam.academic_calendar.start_date,
                end_date=current_session_exam.academic_calendar.end_date,
                id=current_session_exam.id,
                title=current_session_exam.academic_calendar.title,
                authorized_target_year=current_session_exam.academic_calendar.data_year.year,
                type=current_session_exam.academic_calendar.reference,
            )
        self.patch_session_exam_calendar = patch.multiple(
            session_exam_calendar,
            current_session_exam=lambda *args, **kwargs: return_value
        )
        self.patch_session_exam_calendar.start()
        self.addCleanup(self.patch_session_exam_calendar.stop)
