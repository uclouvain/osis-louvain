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
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from base.business.education_groups import general_information
from base.business.education_groups.general_information import PublishException
from base.models.learning_unit_year import LearningUnitYear
from base.views.common import display_error_messages, display_success_messages


@login_required
@require_http_methods(['POST'])
def publish(request, code: str, year: int):
    learning_unit_year = get_object_or_404(
        LearningUnitYear,
        acronym=code,
        academic_year__year=year
    )

    try:
        general_information.publish_learning_unit_year(learning_unit_year)
        message = _("The learning unit %(code)s will be published soon") % {'code': learning_unit_year.acronym}
        display_success_messages(request, message, extra_tags='safe')
    except PublishException as e:
        display_error_messages(request, str(e))

    default_redirect_view = reverse(
        'view_educational_information',
        kwargs={'learning_unit_year_id': learning_unit_year.id}
    )
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', default_redirect_view))
