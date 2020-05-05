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
from django.conf.urls import url, include

from program_management.api.views.prerequisite import TrainingPrerequisites, MiniTrainingPrerequisites

app_name = "program_management"

urlpatterns = [
    url(r'^trainings/(?P<year>[\d]{4})/(?P<acronym>[\w]+(?:[/| ]?[a-zA-Z]{1,2})?)/', include([
        url(r'^transition/prerequisites$', TrainingPrerequisites.as_view(), {'transition': True},
            name='{}_transition'.format(TrainingPrerequisites.NAME)),
        url(r'^prerequisites$', TrainingPrerequisites.as_view(), {'transition': False},
            name='{}_official'.format(TrainingPrerequisites.NAME)),
        url(r'^(?P<version_name>[\w]+)/', include([
            url(r'^transition/prerequisites$', TrainingPrerequisites.as_view(), {'transition': True},
                name='{}_version_transition'.format(TrainingPrerequisites.NAME)),
            url(r'^prerequisites$', TrainingPrerequisites.as_view(), {'transition': False},
                name='{}_version'.format(TrainingPrerequisites.NAME)),
        ])),
    ])),
    url(r'^mini_trainings/(?P<year>[\d]{4})/(?P<partial_acronym>[\w]+)/', include([
        url(r'^transition/prerequisites$', MiniTrainingPrerequisites.as_view(), {'transition': True},
            name='{}_transition'.format(MiniTrainingPrerequisites.NAME)),
        url(r'^prerequisites$', MiniTrainingPrerequisites.as_view(), {'transition': False},
            name='{}_official'.format(MiniTrainingPrerequisites.NAME)),
        url(r'^(?P<version_name>[\w]+)/', include([
            url(r'^transition/prerequisites$', MiniTrainingPrerequisites.as_view(), {'transition': True},
                name='{}_version_transition'.format(MiniTrainingPrerequisites.NAME)),
            url(r'^prerequisites$', MiniTrainingPrerequisites.as_view(), {'transition': False},
                name='{}_version'.format(MiniTrainingPrerequisites.NAME)),
        ])),
    ])),
]
