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
from assistant.views import mandate, home, assistant_form, assistant, phd_supervisor_review
from assistant.views import manager_settings, reviewers_management, upload_assistant_file
from assistant.views import mandates_list, reviewer_mandates_list, reviewer_review, reviewer_delegation
from assistant.utils import get_persons
from assistant.views import messages, phd_supervisor_assistants_list
from assistant.utils import send_email, import_xls_file_data

urlpatterns = [
    # S'il vous plaît, organiser les urls par ordre alphabétique.
    url(r'^api/get_persons/', get_persons.get_persons, name='get_persons'),
    url(r'^home$', home.assistant_home, name='assistants_home'),
    url(r'^manager$', home.manager_home, name='manager_home'),
    url(r'^manager/mandates/(?P<mandate_id>\d+)/edit/$', mandate.mandate_edit, name='mandate_read'),
    url(r'^manager/mandates/(?P<mandate_id>\d+)/save/$', mandate.mandate_save, name='mandate_save'),
    url(r'^manager/mandates/load/$', mandate.load_mandates, name='load_mandates'),
    url(r'^manager/mandates/upload/$', import_xls_file_data.upload_mandates_file, name='upload_mandates_file'),
    url(r'^manager/mandates/$', mandates_list.MandatesListView.as_view(), name='mandates_list'),
    url(r'^manager/messages/history/$', messages.show_history, name='messages_history'),
    url(r'^manager/messages/send/to_all_assistants/$', send_email.send_message_to_assistants,
        name='send_message_to_assistants'),
    url(r'^manager/messages/send/to_all_deans/$', send_email.send_message_to_deans, name='send_message_to_deans'),
    url(r'^manager/reviewers/add/$', reviewers_management.reviewer_add, name='reviewer_add'),
    url(r'^manager/reviewers/(?P<reviewer_id>\d+)/delete/$', reviewers_management.reviewer_delete,
        name='reviewer_delete'),
    url(r'^manager/reviewers/$', reviewers_management.ReviewersListView.as_view(), name='reviewers_list'),
    url(r'^manager/settings/edit/$', manager_settings.settings_edit, name='settings_edit'),
    url(r'^manager/settings/save/$', manager_settings.settings_save, name='settings_save'),
    url(r'^phd_supervisor/assistants/$', phd_supervisor_assistants_list.AssistantsListView.as_view(),
        name='phd_supervisor_assistants_list'),
    url(r'^phd_supervisor/pst_form/view/(?P<mandate_id>\d+)/$', phd_supervisor_review.pst_form_view,
        name='phd_supervisor_pst_form_view'),
    url(r'^phd_supervisor/review/edit/(?P<mandate_id>\d+)/$', phd_supervisor_review.review_edit,
        name='phd_supervisor_review_edit'),
    url(r'^phd_supervisor/review/view/(?P<mandate_id>\d+)/$', phd_supervisor_review.review_view,
        name='phd_supervisor_review_view'),
    url(r'^pst/access_denied$', home.access_denied, name='access_denied'),
    url(r'^pst/document_file/delete/(?P<mandate_id>\d+)/(?P<document_file_id>\d+)/(?P<url>[\w\-]+)/$',
        upload_assistant_file.delete,
        name='assistant_file_delete'),
    url(r'^pst/document_file/download/(?P<document_file_id>\d+)/$', upload_assistant_file.download,
        name='assistant_file_download'),
    url(r'^pst/document_file/upload/$', upload_assistant_file.save_uploaded_file,
        name='assistant_file_upload'),
    url(r'^pst/form_part1/edit/(?P<mandate_id>\d+)/$', assistant_form.form_part1_edit, name='form_part1_edit'),
    url(r'^pst/form_part1/save/(?P<mandate_id>\d+)/$', assistant_form.form_part1_save, name='form_part1_save'),
    url(r'^pst/form_part3/edit/(?P<mandate_id>\d+)/$', assistant_form.form_part3_edit, name='form_part3_edit'),
    url(r'^pst/form_part3/save/(?P<mandate_id>\d+)/$', assistant_form.form_part3_save, name='form_part3_save'),
    url(r'^pst/form_part4/edit/(?P<mandate_id>\d+)/$', assistant_form.form_part4_edit, name='form_part4_edit'),
    url(r'^pst/form_part4/save/(?P<mandate_id>\d+)/$', assistant_form.form_part4_save, name='form_part4_save'),
    url(r'^pst/form_part5/edit/(?P<mandate_id>\d+)/$', assistant_form.form_part5_edit, name='form_part5_edit'),
    url(r'^pst/form_part5/save/(?P<mandate_id>\d+)/$', assistant_form.form_part5_save, name='form_part5_save'),
    url(r'^pst/form_part6/edit/(?P<mandate_id>\d+)/$', assistant_form.form_part6_edit, name='form_part6_edit'),
    url(r'^pst/form_part6/save/(?P<mandate_id>\d+)/$', assistant_form.form_part6_save, name='form_part6_save'),
    url(r'^pst/mandate/(?P<mandate_id>\d+)/state/$', assistant.mandate_change_state, name='mandate_change_state'),
    url(r'^pst/mandates/$', assistant.AssistantMandatesListView.as_view(), name='assistant_mandates'),
    url(r'^pst/mandate/tutoring_learning_unit/add/(?P<mandate_id>\d+)$', assistant_form.tutoring_learning_unit_add,
        name='tutoring_learning_unit_add'),
    url(r'^pst/mandate/tutoring_learning_unit/delete/(?P<tutoring_learning_unit_id>\d+)/$',
        assistant_form.tutoring_learning_unit_delete, name='tutoring_learning_unit_delete'),
    url(r'^pst/mandate/tutoring_learning_unit/edit/(?P<tutoring_learning_unit_id>\d+)/$',
        assistant_form.tutoring_learning_unit_edit, name='tutoring_learning_unit_edit'),
    url(r'^pst/mandate/tutoring_learning_unit/save/(?P<mandate_id>\d+)/$',
        assistant_form.tutoring_learning_unit_save, name='tutoring_learning_unit_save'),
    url(r'^pst/mandate/tutoring_learning_units/(?P<mandate_id>\d+)/$',
        assistant.AssistantLearningUnitsListView.as_view(), name='mandate_learning_units'),
    url(r'^reviewer/delegation/$', reviewer_delegation.StructuresListView.as_view(), name='reviewer_delegation'),
    url(r'^reviewer/pst_form/view/(?P<mandate_id>\d+)/$', reviewer_review.pst_form_view, name='pst_form_view'),
    url(r'^reviewer/structure/(?P<structure_id>\d+)/add_reviewer$',
        reviewer_delegation.add_reviewer_for_structure, name='reviewer_delegation_add'),
    url(r'^reviewer/mandates/$', reviewer_mandates_list.MandatesListView.as_view(), name='reviewer_mandates_list'),
    url(r'^reviewer/review/edit/(?P<mandate_id>\d+)/$', reviewer_review.review_edit, name='review_edit'),
    url(r'^reviewer/review/save/(?P<review_id>\d+)/(?P<mandate_id>\d+)/$',
        reviewer_review.review_save, name='review_save'),
    url(r'^reviewer/review/view/(?P<mandate_id>\d+)/(?P<role>[\w{}.-]{1,40})/$',
        reviewer_review.review_view, name='review_view'),
]
