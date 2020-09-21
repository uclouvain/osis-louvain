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
from django.urls import include, path

import program_management.views.tree.copy_cut
import program_management.views.tree_version.check_version_name
from program_management.views import quick_search, create_element, publish_general_information, content
from program_management.views.proxy.content import ContentRedirectView
from program_management.views.proxy.identification import IdentificationRedirectView
from program_management.views import groupelementyear_read, element_utilization, excel, search, \
    tree, prerequisite_read, prerequisite_update
from program_management.views import quick_search, create_element, publish_general_information
from program_management.views.proxy.identification import IdentificationRedirectView
from program_management.views.tree_version import create as create_program_tree_version
from program_management.views.tree_version.delete import TreeVersionDeleteView
from program_management.views.tree_version import create as create_program_tree_version, update_training, \
    update_mini_training

urlpatterns = [
    url(r'^group_pdf_content/(?P<year>[0-9]+)/(?P<code>[A-Za-z0-9]+)/',
        groupelementyear_read.ReadEducationGroupTypeView.as_view(), name="group_pdf_content"),
    url(r'^pdf_content/(?P<year>[0-9]+)/(?P<code>[A-Za-z0-9]+)/(?P<language>[a-z\-]+)',
        groupelementyear_read.pdf_content, name="pdf_content"),
    url(
        r'reporting/(?P<year>[0-9]+)/(?P<code>[A-Za-z0-9]+)/prerequisites/$',
        excel.get_learning_unit_prerequisites_excel,
        name="education_group_learning_units_prerequisites"
    ),
    url(
        r'reporting/(?P<year>[0-9]+)/(?P<code>[A-Za-z0-9]+)/is_prerequisite_of/$',
        excel.get_learning_units_is_prerequisite_for_excel,
        name="education_group_learning_units_is_prerequisite_for"
    ),
    url(
        r'reporting/(?P<year>[0-9]+)/(?P<code>[A-Za-z0-9]+)/contains/$',
        excel.get_learning_units_of_training_for_excel,
        name="education_group_learning_units_contains"
    ),
    url(r'^$', search.EducationGroupSearch.as_view(), name='version_program'),
    # NEW VERSION URL - Program management
    path('<int:root_id>/', include([
        path('create/', tree.create.CreateLinkView.as_view(), name='tree_create_link'),
        path('update/', tree.update.UpdateLinkView.as_view(), name='tree_update_link'),
        path('detach/', tree.detach.DetachNodeView.as_view(), name='tree_detach_node'),
        path('move/', tree.paste.PasteNodesView.as_view(), name='group_element_year_move'),
        path('<int:link_id>/', include([
            path('up/', tree.move.up, name="group_element_year_up"),
            path('down/', tree.move.down, name="group_element_year_down")
        ])),
    ])),
    path('<int:year>/<str:code>/content/update/', content.update.ContentUpdateView.as_view(), name='content_update'),
    path('up/', tree.move.up, name="content_up"),
    path('down/', tree.move.down, name="content_down"),
    path('create_element/<str:category>', create_element.SelectTypeCreateElementView.as_view(),
         name='create_element_select_type'),
    path('check_paste/', tree.paste.CheckPasteView.as_view(), name="check_tree_paste_node"),
    path('paste/', tree.paste.PasteNodesView.as_view(), name='tree_paste_node'),
    path('update/<str:parent_code>/<int:parent_year>/<str:child_code>/<int:child_year>',
         tree.update.UpdateLinkView.as_view(), name='tree_update_link'),
    path('cut_element/', tree.copy_cut.cut_to_cache, name='cut_element'),
    path('copy_element/', tree.copy_cut.copy_to_cache, name='copy_element'),
    path('<int:year>/quick_search/', include([
        path(
            'learning_unit/',
            quick_search.QuickSearchLearningUnitYearView.as_view(),
            name="quick_search_learning_unit"
        ),
        path(
            'education_group/',
            quick_search.QuickSearchGroupYearView.as_view(),
            name="quick_search_education_group"
        ),
    ])),
    path('<int:root_element_id>/', include([
        path('<int:child_element_id>/', include([
            path('learning_unit/', include([
                path('utilization/',
                     element_utilization.LearningUnitUtilization.as_view(),
                     name='learning_unit_utilization'),
                path('prerequisite/',
                     prerequisite_read.LearningUnitPrerequisite.as_view(),
                     name='learning_unit_prerequisite'),
                path('prerequisite/update/',
                     prerequisite_update.LearningUnitPrerequisite.as_view(),
                     name='learning_unit_prerequisite_update'),
            ]))
        ]))
    ])),

    path(
        'training_version/<int:year>/<str:code>/update',
        update_training.TrainingVersionUpdateView.as_view(),
        name="training_version_update"
    ),
    path(
        'mini_training_version/<int:year>/<str:code>/update',
        update_mini_training.MiniTrainingVersionUpdateView.as_view(),
        name="mini_training_version_update"
    ),

    path('<int:year>/<str:code>/', include([
        path('', IdentificationRedirectView.as_view(), name='element_identification'),
        path('content/', ContentRedirectView.as_view(), name='element_content'),
        path(
            'create_education_group_version/',
            create_program_tree_version.CreateProgramTreeVersion.as_view(),
            name="create_education_group_version"
        ),
        path('publish', publish_general_information.publish, name='publish_general_information'),
        path('delete/', TreeVersionDeleteView.as_view(), name='delete_permanently_tree_version'),
    ])),

    path('<int:year>/<acronym:acronym>/', include([
        path(
            'check_version_name/',
            program_management.views.tree_version.check_version_name.check_version_name,
            name="check_version_name"
        ),
    ])),
]
