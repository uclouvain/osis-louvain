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
import logging
import subprocess
from typing import List

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, logout
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import redirect, render
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from base import models as mdl
from base.models.utils import native
from osis_common.models import application_notice
from program_management.ddd.business_types import *

ITEMS_PER_PAGE = 25

logger = logging.getLogger(settings.DEFAULT_LOGGER)


def page_not_found(request, exception, **kwargs):
    response = render(request, 'page_not_found.html', {})
    response.status_code = 404
    return response


def method_not_allowed(request, **kwargs):
    response = render(request, 'method_not_allowed.html', {})
    response.status_code = 405
    return response


def access_denied(request, exception, **kwargs):
    response = render(request, 'access_denied.html', {'exception': exception})
    response.status_code = 403
    return response


def server_error(request, **kwargs):
    response = render(request, 'server_error.html', {})
    response.status_code = 500
    return response


def noscript(request):
    return render(request, 'noscript.html', {})


def common_context_processor(request):
    if hasattr(settings, 'ENVIRONMENT'):
        env = settings.ENVIRONMENT
    else:
        env = 'LOCAL'
    if hasattr(settings, 'SENTRY_PUBLIC_DNS'):
        sentry_dns = settings.SENTRY_PUBLIC_DNS
    else:
        sentry_dns = ''
    release_tag = settings.RELEASE_TAG if hasattr(settings, 'RELEASE_TAG') else None

    context = {'installed_apps': settings.INSTALLED_APPS,
               'environment': env,
               'sentry_dns': sentry_dns,
               'release_tag': release_tag}
    _check_notice(request, context)
    return context


def _check_notice(request, values):
    if 'subject' not in request.session and 'notice' not in request.session:
        notice = application_notice.find_current_notice()
        if notice:
            request.session.set_expiry(3600)
            request.session['subject'] = notice.subject
            request.session['notice'] = notice.notice

    if 'subject' in request.session and 'notice' in request.session:
        values['subject'] = request.session['subject']
        values['notice'] = request.session['notice']


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        person = mdl.person.find_by_user(user)
        # ./manage.py createsuperuser (in local) doesn't create automatically a Person associated to User
        if person:
            if person.language:
                user_language = person.language
                translation.activate(user_language)
                request.session[translation.LANGUAGE_SESSION_KEY] = user_language
    elif settings.OVERRIDED_LOGIN_URL:
        return redirect(settings.OVERRIDED_LOGIN_URL)
    return LoginView.as_view()(request)


@login_required
def home(request):
    return render(request, "home.html", {
        'highlights': mdl.academic_calendar.find_highlight_academic_calendar()
    })


def log_out(request):
    logout(request)
    if settings.OVERRIDED_LOGOUT_URL:
        return redirect(settings.OVERRIDED_LOGOUT_URL)
    return redirect('logged_out')


def logged_out(request):
    return render(request, 'logged_out.html', {})


@login_required
@permission_required('base.can_access_student_path', raise_exception=True)
def studies(request):
    return render(request, "studies.html", {'section': 'studies'})


@login_required
@permission_required('base.can_access_catalog', raise_exception=True)
def catalog(request):
    return render(request, "catalog.html", {'section': 'catalog'})


@login_required
@user_passes_test(lambda u: u.is_staff and u.has_perm('base.is_administrator'))
def data(request):
    return render(request, "admin/data.html", {'section': 'data'})


@login_required
@user_passes_test(lambda u: u.is_staff and u.has_perm('base.is_administrator'))
def data_maintenance(request):
    sql_command = request.POST.get('sql_command')
    results = native.execute(sql_command)
    return render(request, "admin/data_maintenance.html", {'section': 'data_maintenance',
                                                           'sql_command': sql_command,
                                                           'results': results})


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

    return render(request, "admin/storage.html", {'table': table})


def display_error_messages(request, messages_to_display, extra_tags=None):
    display_messages(request, messages_to_display, messages.ERROR, extra_tags=extra_tags)


def display_success_messages(request, messages_to_display, extra_tags=None):
    display_messages(request, messages_to_display, messages.SUCCESS, extra_tags=extra_tags)


def display_info_messages(request, messages_to_display, extra_tags=None):
    display_messages(request, messages_to_display, messages.INFO, extra_tags=extra_tags)


def display_warning_messages(request, messages_to_display, extra_tags=None):
    display_messages(request, messages_to_display, messages.WARNING, extra_tags=extra_tags)


def display_business_messages(request, messages_to_display: List['BusinessValidationMessage'], extra_tags=None):
    display_success_messages(request, [m.message for m in messages_to_display if m.is_success()], extra_tags=extra_tags)
    display_error_messages(request, [m.message for m in messages_to_display if m.is_error()], extra_tags=extra_tags)
    display_warning_messages(request, [m.message for m in messages_to_display if m.is_warning()], extra_tags=extra_tags)


def display_business_warning_messages(request, messages_to_display: List['BusinessValidationMessage'], extra_tags=None):
    warning_messages = [m for m in messages_to_display if m.is_warning()]
    display_business_messages(request, warning_messages, extra_tags=extra_tags)


def display_messages(request, messages_to_display, level, extra_tags=None):
    if not isinstance(messages_to_display, (tuple, list)):
        messages_to_display = [messages_to_display]

    for msg in messages_to_display:
        messages.add_message(request, level, str(msg), extra_tags=extra_tags)


def check_if_display_message(request, results):
    if not results:
        messages.add_message(request, messages.WARNING, _('No result!'))
    return True


def display_messages_by_level(request, messages_by_level):
    for level, msgs in messages_by_level.items():
        display_messages(request, msgs, level, extra_tags='safe')


def paginate_queryset(qs, request_get, items_per_page=None):
    items_per_page = items_per_page or ITEMS_PER_PAGE
    paginator = Paginator(qs, items_per_page)

    page = request_get.get('page')
    try:
        paginated_qs = paginator.page(page)
    except PageNotAnInteger:
        paginated_qs = paginator.page(1)
    except EmptyPage:
        paginated_qs = paginator.page(paginator.num_pages)
    return paginated_qs


def remove_from_session(request, session_key):
    if session_key in request.session:
        del request.session[session_key]


def add_to_session(request, session_key, value):
    if session_key not in request.session:
        request.session[session_key] = value


def show_error_message_for_form_invalid(request):
    msg = _("Error(s) in form: The modifications are not saved")
    display_error_messages(request, msg)
