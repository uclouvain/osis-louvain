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
from django.conf.urls import url
from django.urls import include

from program_management.views.excel import get_learning_unit_prerequisites_excel, \
    get_learning_units_is_prerequisite_for_excel
from program_management.views.group_element_year import update, create, delete, read
from program_management.views.learning_unit import detail as learning_unit_detail, update as learning_unit_update

urlpatterns = [
    url(r'^management/$', update.management, name='education_groups_management'),
    url(r'^(?P<root_id>[0-9]+)/(?P<education_group_year_id>[0-9]+)/', include([
        url(r'^content/', include([
            url(u'^attach/', create.AttachTypeDialogView.as_view(),
                name='education_group_attach'),
            url(u'^create/$', create.CreateGroupElementYearView.as_view(),
                name='group_element_year_create'),
            url(r'^(?P<group_element_year_id>[0-9]+)/', include([
                url(r'^delete/$', delete.DetachGroupElementYearView.as_view(),
                    name='group_element_year_delete'),
                url(r'^move/$', create.MoveGroupElementYearView.as_view(),
                    name='group_element_year_move'),
                url(r'^update/$', update.UpdateGroupElementYearView.as_view(),
                    name="group_element_year_update")
            ]))
        ])),
        url(r'^group_content/', read.ReadEducationGroupTypeView.as_view(), name="group_content"),
        url(r'^pdf_content/(?P<language>[a-z\-]+)', read.pdf_content, name="pdf_content"),
        url(r'^postpone/', update.PostponeGroupElementYearView.as_view(), name="postpone_education_group"),
    ])),
    url(r'^(?P<root_id>[0-9]+)/(?P<learning_unit_year_id>[0-9]+)/learning_unit/', include([
        url(r'^utilization/$',
            learning_unit_detail.LearningUnitUtilization.as_view(),
            name='learning_unit_utilization'),
        url(r'^prerequisite/$',
            learning_unit_detail.LearningUnitPrerequisite.as_view(),
            name='learning_unit_prerequisite'),
        url(r'^prerequisite/update/$',
            learning_unit_update.LearningUnitPrerequisite.as_view(),
            name='learning_unit_prerequisite_update'),
    ])),
    url(
        r'reporting/(?P<education_group_year_pk>[0-9]+)/prerequisites/$',
        get_learning_unit_prerequisites_excel,
        name="education_group_learning_units_prerequisites"
    ),
    url(
        r'reporting/(?P<education_group_year_pk>[0-9]+)/is_prerequisite_of/$',
        get_learning_units_is_prerequisite_for_excel,
        name="education_group_learning_units_is_prerequisite_for"
    )
]
