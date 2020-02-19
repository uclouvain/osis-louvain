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
from django.template.defaulttags import register


DEFAULT_PAGINATOR_SIZE = 50
PAGINATOR_SIZE_LIST = [10, 25, 50, 100, 250, 500]


@register.inclusion_tag('templatetags/pagination_size_select.html', takes_context=True)
def base_pagination_size_select(context):
    request = context['request']
    paginator_size = get_paginator_size(request)
    return {
        'path': request.get_full_path(),
        'paginator_size_list': PAGINATOR_SIZE_LIST,
        'current_paginator_size': paginator_size,
        'other_params': {k: v for k, v in request.GET.items() if k != 'paginator_size' and k != 'page'}
    }


def store_paginator_size(request):
    if 'paginator_size' in request.GET:
        request.session['paginator_size'] = request.session.setdefault('paginator_size', {})
        request.session['paginator_size'].update({request.path: request.GET.get('paginator_size')})


def get_paginator_size(request):
    if 'paginator_size' in request.session and request.path in request.session['paginator_size']:
        return request.session.get('paginator_size')[request.path]
    elif 'paginator_size' in request.GET:
        return request.GET.get('paginator_size')
    else:
        return DEFAULT_PAGINATOR_SIZE
