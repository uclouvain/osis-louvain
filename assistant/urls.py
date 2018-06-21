##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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

from assistant.business.assistant_mandate import find_assistant_mandate_step_backward_state
from assistant.views import manager_assistant_form
from assistant.views import mandate, home, assistant_form, assistant, phd_supervisor_review
from assistant.views import manager_settings, reviewers_management, upload_assistant_file
from assistant.views import mandates_list, reviewer_mandates_list, reviewer_review, reviewer_delegation
from assistant.utils import get_persons
from assistant.views import messages, phd_supervisor_assistants_list
from assistant.views import assistant_mandate_reviews
from assistant.views import manager_reviews_view
from assistant.utils import send_email, import_xls_file_data, export_utils_pdf

urlpatterns = [
    url(r'^$', home.assistant_home, name='assistants_home'),
    url(r'^access_denied$', home.access_denied, name='access_denied'),
    url(r'^api/get_persons/', get_persons.get_persons, name='get_persons'),


    url(r'^assistant/', include([
        url(r'^$', assistant.AssistantMandatesListView.as_view(), name='assistant_mandates'),
        url(r'^document_file/', include([
            url(r'^delete/(?P<document_file_id>\d+)/(?P<url>[\w\-]+)/$',
                upload_assistant_file.delete, name='assistant_file_delete'),
            url(r'^download/(?P<document_file_id>\d+)/$', upload_assistant_file.download,
                name='assistant_file_download'),
            url(r'^upload/$', upload_assistant_file.save_uploaded_file, name='assistant_file_upload'),
        ])),
        url(r'^export_pdf/$', export_utils_pdf.export_mandate, name='export_mandate_pdf'),
        url(r'^form/', include([
            url(r'^part1/', include([
                url(r'^edit/$', assistant_form.form_part1_edit, name='form_part1_edit'),
                url(r'^save/$', assistant_form.form_part1_save, name='form_part1_save'),
            ])),
            url(r'^part2/', include([
                url(r'^get_learning_units_year/', assistant_form.get_learning_units_year,
                    name='get_learning_units_year'),
                url(r'^$', assistant.AssistantLearningUnitsListView.as_view(),
                    name='mandate_learning_units'),
                url(r'^add/$', assistant_form.tutoring_learning_unit_add,
                    name='tutoring_learning_unit_add'),
                url(r'^(?P<tutoring_learning_unit_id>\d+)/delete/$', assistant_form.tutoring_learning_unit_delete,
                    name='tutoring_learning_unit_delete'),
                url(r'^(?P<tutoring_learning_unit_id>\d+)/edit/$', assistant_form.tutoring_learning_unit_edit,
                    name='tutoring_learning_unit_edit'),
                url(r'^save/$', assistant_form.tutoring_learning_unit_save,
                    name='tutoring_learning_unit_save'),
            ])),
            url(r'^part3/', include([
                url(r'^edit/$', assistant_form.form_part3_edit, name='form_part3_edit'),
                url(r'^save/$', assistant_form.form_part3_save, name='form_part3_save'),
            ])),
            url(r'^part4/', include([
                url(r'^edit/$', assistant_form.form_part4_edit, name='form_part4_edit'),
                url(r'^save/$', assistant_form.form_part4_save, name='form_part4_save'),
            ])),
            url(r'^part5/', include([
                url(r'^edit/$', assistant_form.form_part5_edit, name='form_part5_edit'),
                url(r'^save/$', assistant_form.form_part5_save, name='form_part5_save'),
            ])),
            url(r'^part6/', include([
                url(r'^edit/$', assistant_form.form_part6_edit, name='form_part6_edit'),
                url(r'^save/$', assistant_form.form_part6_save, name='form_part6_save'),
            ])),
        ])),
        url(r'^mandate/', include([
            url(r'^change_state/$', assistant.mandate_change_state, name='mandate_change_state'),
            url(r'^reviews/$', assistant_mandate_reviews.reviews_view,
                name='assistant_mandate_reviews'),
        ])),
    ])),

    url(r'^manager/', include([
        url(r'^$', home.manager_home, name='manager_home'),
        url(r'^assistant_form/(?P<mandate_id>\d+)/$', manager_assistant_form.assistant_form_view,
            name='manager_assistant_form_view'),
        url(r'^mandates/', include([
            url(r'^$', mandates_list.MandatesListView.as_view(), name='mandates_list'),
            url(r'^edit/$', mandate.mandate_edit, name='mandate_read'),
            url(r'^save/$', mandate.mandate_save, name='mandate_save'),
            url(r'^go_backward/$', find_assistant_mandate_step_backward_state, name='assistant_mandate_step_back'),
            url(r'^load/$', mandate.load_mandates, name='load_mandates'),
            url(r'^upload/$', import_xls_file_data.upload_mandates_file, name='upload_mandates_file'),
            url(r'^export/$', mandate.export_mandates, name='export_mandates'),
            url(r'^export_pdf/$', export_utils_pdf.export_mandates, name='export_mandates_pdf'),
        ])),
        url(r'^messages/', include([
            url(r'^history/$', messages.show_history, name='messages_history'),
            url(r'^send/to_all_assistants/$', send_email.send_message_to_assistants, name='send_message_to_assistants'),
            url(r'^send/to_reviewers/$', send_email.send_message_to_reviewers, name='send_message_to_reviewers'),
        ])),
        url(r'^reviewers/', include([
            url(r'^$', reviewers_management.reviewers_index, name='reviewers_list'),
            url(r'^action/$', reviewers_management.reviewer_action, name="reviewer_action"),
            url(r'^add/$', reviewers_management.reviewer_add, name='reviewer_add'),
            url(r'^replace/$', reviewers_management.reviewer_replace, name='reviewer_replace'),
        ])),
        url(r'^reviews/(?P<mandate_id>\d+)/$', manager_reviews_view.reviews_view, name='manager_reviews_view'),
        url(r'^settings/', include([
            url(r'^edit/$', manager_settings.settings_edit, name='settings_edit'),
            url(r'^save/$', manager_settings.settings_save, name='settings_save'),
        ])),
    ])),

    url(r'^phd_supervisor/', include([
        url(r'^assistants/$', phd_supervisor_assistants_list.AssistantsListView.as_view(),
            name='phd_supervisor_assistants_list'),
        url(r'^pst_form/$', phd_supervisor_review.pst_form_view,
            name='phd_supervisor_pst_form_view'),
        url(r'^review/', include([
            url(r'^view/$', phd_supervisor_review.review_view, name='phd_supervisor_review_view'),
            url(r'^edit/$', phd_supervisor_review.review_edit, name='phd_supervisor_review_edit'),
            url(r'^save/$', phd_supervisor_review.review_save,
                name='phd_supervisor_review_save'),
        ])),
    ])),

    url(r'^reviewer/', include([
        url(r'^$', reviewer_mandates_list.MandatesListView.as_view(), { 'filter': False },
            name='reviewer_mandates_list'),
        url(r'^todo/$', reviewer_mandates_list.MandatesListView.as_view(), { 'filter': True },
            name='reviewer_mandates_list_todo'),
        url(r'^delegation/$', reviewer_delegation.StructuresListView.as_view(), name='reviewer_delegation'),
        url(r'^pst_form/$', reviewer_review.pst_form_view, name='pst_form_view'),
        url(r'^delegate/add/$', reviewer_delegation.add_reviewer_for_structure,
            name='reviewer_delegation_add'),
        url(r'^review/', include([
            url(r'^view/$', reviewer_review.review_view, name='review_view'),
            url(r'^edit/$', reviewer_review.review_edit, name='review_edit'),
            url(r'^save/$', reviewer_review.review_save, name='review_save'),
        ])),
    ])),
]
