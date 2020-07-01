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
import waffle
from django import template
from django.utils.translation import gettext as _

from base.models import program_manager

register = template.Library()

UN_VERSIONED_OF_FIELD = "of_unversioned_field"


# TODO: Remove when migration of Program Manager is done with OSIS-Role Module
@register.simple_tag
def have_only_access_to_certificate_aims(user, education_group_year):
    """
    [Backward-compatibility] This templatetag as been created in order to allow
    program_manager to be redirected to update_certificate_aims
    """
    return program_manager.is_program_manager(user, education_group=education_group_year.education_group) \
        and not any((user.is_superuser, user.person.is_faculty_manager, user.person.is_central_manager))


@register.simple_tag(takes_context=True)
def url_resolver_match(context):
    return context.request.resolver_match.url_name


@register.inclusion_tag('blocks/button/li_template.html')
def link_pdf_content_education_group(url):
    action = _("Generate pdf")
    if waffle.switch_is_active('education_group_year_generate_pdf'):
        disabled = ''
        title = action
        load_modal = True
    else:
        disabled = 'disabled'
        title = _('Generate PDF not available. Please use EPC.')
        load_modal = False
        url = '#'

    return {
        "class_li": disabled,
        "load_modal": load_modal,
        "url": url,
        "id_li": "btn_operation_pdf_content",
        "title": title,
        "text": action,
    }
