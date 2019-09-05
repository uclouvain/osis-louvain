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
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from base.business.education_groups import delete


def start(education_group, until_year):
    """
    This function will delete all education group year
    """
    education_group_years_to_delete = delete.get_education_group_years_to_delete(education_group, end_year=until_year)
    egy_deleted = []
    for education_group_year in education_group_years_to_delete:
        egy_deleted.append(education_group_year)
        delete.start(education_group_year)
    return egy_deleted


def check_education_group_end_date(education_group, end_year):
    education_group_years_to_delete = delete.get_education_group_years_to_delete(education_group,
                                                                                 end_year=end_year)
    protected_messages = _get_protected_messages(education_group_years_to_delete)
    if protected_messages:
        error_msg = _get_formated_error_msg(end_year, protected_messages)
        raise ValidationError({
            NON_FIELD_ERRORS: error_msg,
            'end_year': ''
        })
    return True


def _get_formated_error_msg(end_year, protected_messages):
    error_msg = _("Cannot set end year to %(end_year)s :") % {'end_year': end_year}
    error_msg += "<ul>"
    for protected_message in protected_messages:
        error_msg += "<li> {education_group_year} : {msg_str} </li>".format(
            education_group_year=protected_message['education_group_year'],
            msg_str=", ".join([str(lazy_msg) for lazy_msg in protected_message['messages']])
        )
    error_msg += "</ul>"
    return mark_safe(error_msg)


def _get_protected_messages(education_group_years):
    protected_messages = []
    for education_group_year in education_group_years:
        protected_message = delete.get_protected_messages_by_education_group_year(education_group_year)
        if protected_message:
            protected_messages.append({
                'education_group_year': education_group_year,
                'messages': protected_message
            })
    return protected_messages
