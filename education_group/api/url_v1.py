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

from education_group.api.views.education_group_version import TrainingVersionList, MiniTrainingVersionList
from education_group.api.views.group import GroupDetail, GroupTitle
from education_group.api.views.group_element_year import TrainingTreeView, MiniTrainingTreeView, GroupTreeView
from education_group.api.views.hops import HopsList
from education_group.api.views.mini_training import MiniTrainingDetail, MiniTrainingTitle, MiniTrainingList, \
    OfferRoots
from education_group.api.views.training import TrainingList, TrainingDetail, TrainingTitle

app_name = "education_group"

urlpatterns = [
    url(r'^hops/(?P<year>[\d]{4})$', HopsList.as_view(), name=HopsList.name),
    url(r'^trainings$', TrainingList.as_view(), name=TrainingList.name),
    url(r'^trainings/(?P<year>[\d]{4})/(?P<acronym>[\w]+(?:[/ ]?[\w]{1,2}){0,2})/', include([
        url(r'^tree$', TrainingTreeView.as_view(), name=TrainingTreeView.name),
        url(r'^title$', TrainingTitle.as_view(), name=TrainingTitle.name),
        url(r'^versions$', TrainingVersionList.as_view(), name=TrainingVersionList.name)
    ])),
    url(
        r'^trainings/(?P<year>[\d]{4})/(?P<acronym>[\w]+(?:[/ ]?[a-zA-Z]{1,2}){0,2})/versions/(?P<version_name>[\w]*)$',
        TrainingDetail.as_view(),
        name=TrainingDetail.name
    ),
    url(
        r'^trainings/(?P<year>[\d]{4})/(?P<acronym>[\w]+(?:[/ ]?[a-zA-Z]{1,2}){0,2})/versions/(?P<version_name>[\w]*)/',
        include([
            url(r'^tree$', TrainingTreeView.as_view(), name=TrainingTreeView.name),
            url(r'^title$', TrainingTitle.as_view(), name=TrainingTitle.name),
        ])
    ),
    url(
        r'^trainings/(?P<year>[\d]{4})/(?P<acronym>[\w]+(?:[/ ]?[\w]{1,2}){0,2})$',
        TrainingDetail.as_view(),
        name=TrainingDetail.name
    ),
    url(r'^mini_trainings$', MiniTrainingList.as_view(), name=MiniTrainingList.name),
    url(r'^mini_trainings/(?P<year>[\d]{4})/(?P<official_partial_acronym>[\w]+)/', include([
        url(r'^tree$', MiniTrainingTreeView.as_view(), name=MiniTrainingTreeView.name),
        url(r'^title$', MiniTrainingTitle.as_view(), name=MiniTrainingTitle.name),
        url(r'^offer_roots$', OfferRoots.as_view(), name=OfferRoots.name),
        url(r'^versions$', MiniTrainingVersionList.as_view(), name=MiniTrainingVersionList.name)
    ])),
    url(
        r'^mini_trainings/(?P<year>[\d]{4})/(?P<official_partial_acronym>[\w]+)/versions/(?P<version_name>[\w]*)$',
        MiniTrainingDetail.as_view(),
        name=MiniTrainingDetail.name
    ),
    url(
        r'^mini_trainings/(?P<year>[\d]{4})/(?P<official_partial_acronym>[\w]+)/versions/(?P<version_name>[\w]*)/',
        include([
            url(r'^tree$', MiniTrainingTreeView.as_view(), name=MiniTrainingTreeView.name),
            url(r'^title$', MiniTrainingTitle.as_view(), name=MiniTrainingTitle.name),
        ])
    ),
    url(
        r'^mini_trainings/(?P<year>[\d]{4})/(?P<official_partial_acronym>[\w]+)$',
        MiniTrainingDetail.as_view(),
        name=MiniTrainingDetail.name
    ),
    url(
        r'^groups/(?P<year>[\d]{4})/(?P<partial_acronym>[\w]+)$',
        GroupDetail.as_view(),
        name=GroupDetail.name
    ),
    url(r'^groups/(?P<year>[\d]{4})/(?P<partial_acronym>[\w]+)/', include([
        url(r'^tree$', GroupTreeView.as_view(), name=GroupTreeView.name),
        url(r'^title$', GroupTitle.as_view(), name=GroupTitle.name),
    ])),
]
