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
import requests

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import redirect

from backoffice.settings.base import ESB_STUDENT_API, ESB_AUTHORIZATION
from base import models as mdl
from . import layout


@login_required
@permission_required('base.can_access_student', raise_exception=True)
def students(request):
    return layout.render(request, "student/students.html", {'students': None})


@login_required
@permission_required('base.can_access_student', raise_exception=True)
def student_search(request):
    students_list = name = None
    registration_id = request.GET.get('registration_id')
    if registration_id:
        student = mdl.student.find_by_registration_id(registration_id)
        if student:
            students_list = [student]
    else:
        name = request.GET.get('name')
        students_list = mdl.student.search(name)
    return layout.render(request, "student/students.html", {'students': students_list,
                                                            'registration_id': registration_id,
                                                            'name': name})


@login_required
@permission_required('base.can_access_student', raise_exception=True)
def student_read(request, student_id):
    student = mdl.student.find_by_id(student_id)
    if student:
        offers_enrollments = mdl.offer_enrollment.find_by_student(student)
        exams_enrollments = mdl.exam_enrollment.find_by_student(student)
        lu_enrollments = mdl.learning_unit_enrollment.find_by_student(student)
    return layout.render(request, "student/student.html", locals())


@login_required
@permission_required('base.can_access_student', raise_exception=True)
def student_picture(request, student_id):
    student = mdl.student.find_by_id(student_id)
    if student:
        try:
            url = "{url}/{registration_id}/photo".format(url=ESB_STUDENT_API, registration_id=student.registration_id)
            response = requests.get(url, headers={"Authorization": ESB_AUTHORIZATION})
            result = response.json()
            if response.status_code == 200 and result.get('photo_url'):
                return _get_image(result.get('photo_url'), student)
        finally:
            return _default_image(student)
    raise Http404()


def _get_image(url, student):
    response = requests.get(url)
    if response.status_code == 200:
        return HttpResponse(response.content, content_type="image/jpeg")
    return _default_image(student)


def _default_image(student):
    if student.person and student.person.gender == 'F':
        default_image = 'women_unknown'
    else:
        default_image = 'men_unknown'

    path = 'img/{}.png'.format(default_image)
    return redirect(staticfiles_storage.url(path))
