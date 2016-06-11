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
from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from assistant.views import mandate, home, assistant
from assistant.views import mandates_list
from assistant.models import assistant_mandate

urlpatterns = [
    # S'il vous plaît, organiser les urls par ordre alphabétique.
    url(r'^assistant/access_denied$', home.access_denied, name='access_denied'),
    url(r'^assistant/mandates/$', assistant.AssistantMandatesListView.as_view(), name='assistant_mandates'),
    url(r'^$', home.assistant_home , name='assistants_home'),
    url(r'^manager/mandates/(?P<mandate_id>\d+)/edit/$', mandate.mandate_edit, name='mandate_read'),
    url(r'^manager/mandates/(?P<mandate_id>\d+)/save/$', mandate.mandate_save, name='mandate_save'),
    url(r'^manager/mandates/load/$', mandate.load_mandates, name='load_mandates'),
    url(r'^manager/mandates/$', login_required(mandates_list.MandatesListView.as_view()), name='mandates_list'),
]