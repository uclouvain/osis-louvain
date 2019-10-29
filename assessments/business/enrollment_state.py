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

from base import models as mdl
from base.models.enums import exam_enrollment_state as enrollment_states

ENROLLED_LATE_COLOR = '#dff0d8'
NOT_ENROLLED_COLOR = '#f2dede'


def get_line_color(enrollment):
    if enrollment.enrollment_state == enrollment_states.ENROLLED:
        current_session = mdl.session_exam_calendar.current_session_exam()
        if enrollment.date_enrollment \
                and enrollment.date_enrollment > current_session.academic_calendar.start_date:
            return ENROLLED_LATE_COLOR
        return None
    else:
        return NOT_ENROLLED_COLOR
