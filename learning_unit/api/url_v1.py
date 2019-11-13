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
from django.conf import settings
from django.conf.urls import url
from django.urls import include

from learning_unit.api.views.attribution import LearningUnitAttribution
from learning_unit.api.views.learning_achievement import LearningAchievementList
from learning_unit.api.views.learning_unit import LearningUnitDetailed, LearningUnitList, LearningUnitTitle
from learning_unit.api.views.summary_specification import LearningUnitSummarySpecification
from learning_unit.api.views.teaching_materials import LearningUnitTeachingMaterials

app_name = "learning_unit"

urlpatterns = [
    url(r'^learning_units$', LearningUnitList.as_view(), name=LearningUnitList.name),
    url(
        r'^learning_units/(?P<year>[0-9]{4})/(?P<acronym>[a-zA-Z0-9]+)$',
        LearningUnitDetailed.as_view(),
        name=LearningUnitDetailed.name
    ),
    url(r'^learning_units/(?P<year>[0-9]{4})/(?P<acronym>[a-zA-Z0-9]+)/', include([
        url(r'^title$', LearningUnitTitle.as_view(), name=LearningUnitTitle.name),
        url(r'^attributions$', LearningUnitAttribution.as_view(), name=LearningUnitAttribution.name),
        url(r'^achievements$', LearningAchievementList.as_view(), name=LearningAchievementList.name),
        url(r'^teaching_materials$', LearningUnitTeachingMaterials.as_view(), name=LearningUnitTeachingMaterials.name),
        url(
            r'^summary_specification$',
            LearningUnitSummarySpecification.as_view(),
            name=LearningUnitSummarySpecification.name
        ),
    ])),
]

if 'education_group' in settings.INSTALLED_APPS:
    from education_group.api.views.learning_unit import EducationGroupRootsList, LearningUnitPrerequisitesList

    urlpatterns += (
        url(
            r'^learning_units/(?P<year>[0-9]{4})/(?P<acronym>[a-zA-Z0-9]+)/education_group_roots$',
            EducationGroupRootsList.as_view(),
            name=EducationGroupRootsList.name
        ),
        url(
            r'^learning_units/(?P<year>[0-9]{4})/(?P<acronym>[a-zA-Z0-9]+)/prerequisites$',
            LearningUnitPrerequisitesList.as_view(),
            name=LearningUnitPrerequisitesList.name
        ),
    )
