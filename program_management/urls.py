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

from program_management.views import groupelementyear_create, groupelementyear_delete, groupelementyear_update, \
    groupelementyear_read, prerequisite_update, prerequisite_read, element_utilization, groupelementyear_postpone, \
    groupelementyear_management, excel, search, tree
from program_management.views.quick_search import QuickSearchLearningUnitYearView, QuickSearchEducationGroupYearView

urlpatterns = [
    url(r'^management/$', groupelementyear_management.management, name='education_groups_management'),
    url(r'^(?P<root_id>[0-9]+)/(?P<education_group_year_id>[0-9]+)/', include([
        url(r'^content/', include([
            url(u'^attach/', groupelementyear_create.PasteElementFromCacheToSelectedTreeNode.as_view(),
                name='education_group_attach'),
            url(r'^check_attach/', groupelementyear_create.AttachCheckView.as_view(),
                name="check_education_group_attach"),
            url(u'^create/$', groupelementyear_create.CreateGroupElementYearView.as_view(),
                name='group_element_year_create'),
            url(r'^(?P<group_element_year_id>[0-9]+)/', include([
                url(r'^delete/$', groupelementyear_delete.DetachGroupElementYearView.as_view(),
                    name='group_element_year_delete'),
                url(r'^move/$', groupelementyear_create.MoveGroupElementYearView.as_view(),
                    name='group_element_year_move'),
                url(r'^update/$', groupelementyear_update.UpdateGroupElementYearView.as_view(),
                    name="group_element_year_update")
            ]))
        ])),
        url(r'^group_content/', groupelementyear_read.ReadEducationGroupTypeView.as_view(), name="group_content"),
        url(r'^pdf_content/(?P<language>[a-z\-]+)', groupelementyear_read.pdf_content, name="pdf_content"),
        url(r'^postpone/', groupelementyear_postpone.PostponeGroupElementYearView.as_view(),
            name="postpone_education_group"),
        url(r'^quick_search/', include([
            url(r'^learning_unit/$', QuickSearchLearningUnitYearView.as_view(),
                name="quick_search_learning_unit"),
            url(r'^education_group/$', QuickSearchEducationGroupYearView.as_view(),
                name="quick_search_education_group"),
        ])),
    ])),
    url(r'^(?P<root_id>[0-9]+)/(?P<learning_unit_year_id>[0-9]+)/learning_unit/', include([
        url(r'^utilization/$',
            element_utilization.LearningUnitUtilization.as_view(),
            name='learning_unit_utilization'),
        url(r'^prerequisite/$',
            prerequisite_read.LearningUnitPrerequisite.as_view(),
            name='learning_unit_prerequisite'),
        url(r'^prerequisite/update/$',
            prerequisite_update.LearningUnitPrerequisite.as_view(),
            name='learning_unit_prerequisite_update'),
    ])),
    url(
        r'reporting/(?P<education_group_year_pk>[0-9]+)/prerequisites/$',
        excel.get_learning_unit_prerequisites_excel,
        name="education_group_learning_units_prerequisites"
    ),
    url(
        r'reporting/(?P<education_group_year_pk>[0-9]+)/is_prerequisite_of/$',
        excel.get_learning_units_is_prerequisite_for_excel,
        name="education_group_learning_units_is_prerequisite_for"
    ),
    url(
        r'reporting/(?P<root_id>[0-9]+)/(?P<education_group_year_pk>[0-9]+)/contains/$',
        excel.get_learning_units_of_training_for_excel,
        name="education_group_learning_units_contains"
    ),
    url(r'^$', search.EducationGroupSearch.as_view(), name='version_program'),

    # NEW VERSION URL - Program management
    url(r'^(?P<root_id>[0-9]+)/', include([
        url(u'^create', tree.create.CreateLinkView.as_view(), name='tree_create_link'),
        url(u'^update', tree.update.UpdateLinkView.as_view(), name='tree_update_link'),
        url(u'^attach', tree.attach.AttachMultipleNodesView.as_view(), name='tree_attach_node'),
        url(u'^detach', tree.detach.DetachNodeView.as_view(), name='tree_detach_node'),
        url(u'^move', tree.move.MoveNodeView.as_view(), name='tree_move_node'),
    ])),
]
