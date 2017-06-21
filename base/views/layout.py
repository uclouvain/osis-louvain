##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django import shortcuts
from base import models as mdl
from random import randint


def _check_notice(request, values):
    if 'subject' not in request.session and 'notice' not in request.session:
        notice = mdl.application_notice.find_current_notice()
        if notice:
            request.session.set_expiry(3600)
            request.session['subject'] = notice.subject
            request.session['notice'] = notice.notice

    if 'subject' in request.session and 'notice' in request.session:
        values['subject'] = request.session['subject']
        values['notice'] = request.session['notice']


def render(request, template, values):
    _check_notice(request, values)

    values['js'] = randint(0, 100)

    return shortcuts.render(request, template, values)


def render_to_response(request, template, values):
    _check_notice(request, values)

    return shortcuts.render_to_response(template, values)