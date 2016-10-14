##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
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
from datetime import datetime
import subprocess
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.views import login as django_login
from django.contrib.auth import authenticate, logout
from django.shortcuts import redirect
from django.utils import translation
from . import layout
from django.utils.translation import ugettext_lazy as _
from osis_common.models import document_file as doc_file_mdl
from base.models import person as person_mdl, academic_year as academic_year_mdl, \
    academic_calendar as academic_calendar_mdl, native as native_mdl


def page_not_found(request):
    return layout.render(request, 'page_not_found.html', {})


def access_denied(request):
    return layout.render(request, 'access_denied.html', {})


def server_error(request):
    return layout.render(request, 'server_error.html', {})


def noscript(request):
    return layout.render(request, 'noscript.html', {})


def environnement_request_processor(request):
    try:
        env = settings.ENVIRONMENT
        sentry_dns = settings.SENTRY_DNS
    except AttributeError:
        env = 'DEV'
        sentry_dns = ''
    return {'environment': env, 'sentry_dns': sentry_dns}


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        person = person_mdl.find_by_user(user)
        # ./manage.py createsuperuser (in local) doesn't create automatically a Person associated to User
        if person:
            if person.language:
                user_language = person.language
                translation.activate(user_language)
                request.session[translation.LANGUAGE_SESSION_KEY] = user_language
    return django_login(request)

@login_required
def home(request):
    academic_yr = academic_year_mdl.current_academic_year()
    calendar_events = None
    if academic_yr:
        calendar_events = academic_calendar_mdl.find_academic_calendar_by_academic_year_with_dates(academic_yr.id)
    return layout.render(request, "home.html", {'academic_calendar': calendar_events,
                                                'highlights': academic_calendar_mdl.find_highlight_academic_calendars()})


def log_out(request):
    logout(request)
    return redirect('logged_out')


def logged_out(request):
    return layout.render(request,'logged_out.html', {})


@login_required
@permission_required('base.can_access_student_path', raise_exception=True)
def studies(request):
    return layout.render(request, "studies.html", {'section': 'studies'})


@login_required
@permission_required('base.can_access_evaluation', raise_exception=True)
def assessments(request):
    return layout.render(request, "assessments/assessments.html", {'section': 'assessments'})


@login_required
@permission_required('base.can_access_catalog', raise_exception=True)
def catalog(request):
    return layout.render(request, "catalog.html", {'section': 'catalog'})


@login_required
@user_passes_test(lambda u: u.is_staff and u.has_perm('base.is_administrator'))
def data(request):
    return layout.render(request, "admin/data.html", {'section': 'data'})


@login_required
@user_passes_test(lambda u: u.is_staff and u.has_perm('base.is_administrator'))
def data_maintenance(request):
    sql_command = request.POST.get('sql_command')
    results = native_mdl.execute(sql_command)
    return layout.render(request, "admin/data_maintenance.html", {'section': 'data_maintenance',
                                                                  'sql_command': sql_command,
                                                                  'results': results})


@login_required
@permission_required('base.can_access_academicyear', raise_exception=True)
def academic_year(request):
    return layout.render(request, "academic_year.html", {'section': 'academic_year'})


@login_required
@permission_required('base.is_administrator', raise_exception=True)
def storage(request):
    df = subprocess.Popen(["df", "-h"], stdout=subprocess.PIPE)
    output = df.communicate()[0]
    lines = output.splitlines()
    lines[0] = lines[0].decode("utf-8").replace('Mounted on', 'Mounted')
    lines[0] = lines[0].replace('Avail', 'Available')
    table = []
    num_cols = 0
    for line in lines:
        row = line.split()
        if num_cols < len(row):
            num_cols = len(row)
        table.append(row)

    # This fixes a presentation problem on MacOS. It shows what looks like an alias at the end of the line.
    if len(table[0]) < num_cols:
        table[0].append('Alias')

    for row in table[1:]:
        if len(row) < num_cols:
            row.append('')

    return layout.render(request, "admin/storage.html", {'table': table})


@login_required
@permission_required('base.is_administrator', raise_exception=True)
def files(request):
    return layout.render(request, "admin/files.html", {})


@login_required
@permission_required('base.is_administrator', raise_exception=True)
def files_search(request):
    registration_date = request.GET['registration_date']
    username = request.GET['user']
    message = None
    files = None
    if registration_date or username :
        if registration_date :
            registration_date = datetime.strptime(request.GET['registration_date'], '%Y-%m-%d')
        files = doc_file_mdl.search(username=username, creation_date=registration_date)
    else :
        message = "%s" % _('minimum_one_criteria')

    return layout.render(request, "admin/files.html", {'files': files,
                                                       'message': message})


@login_required
@permission_required('base.is_administrator', raise_exception=True)
def document_file_read(request, document_file_id):
    document_file = doc_file_mdl.find_by_id(document_file_id)
    return layout.render(request, "admin/file.html", {'file': document_file})
