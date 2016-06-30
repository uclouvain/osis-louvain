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

from base.utils import upload_xls_utils
from base.views import learning_unit, offer, common, score_encoding, institution, organization, academic_calendar,\
    my_osis

urlpatterns = [
    url(r'^$', common.home, name='home'),

    # Please, organize the urls in alphabetic order.

    url(r'^academic_year/$', common.academic_year, name='academic_year'),
    url(r'^academic_calendars/$', academic_calendar.academic_calendars, name='academic_calendars'),
    url(r'^academic_calendars/search$', academic_calendar.academic_calendars_search, name='academic_calendars_search'),
    url(r'^academic_calendars/([0-9]+)/$', academic_calendar.academic_calendar_read, name='academic_calendar_read'),
    url(r'^academic_calendars/edit/([0-9]+)/$', academic_calendar.academic_calendar_edit, name='academic_calendar_edit'),
    url(r'^academic_calendars/save/([0-9]+)/$', academic_calendar.academic_calendar_save, name='academic_calendar_save'),
    url(r'^academic_calendars/save/$', academic_calendar.academic_calendar_new, name='academic_calendar_save_new'),
    url(r'^academic_calendars/create/$', academic_calendar.academic_calendar_create, name='academic_calendar_create'),

    url(r'^admin/data/$', common.data, name='data'),
    url(r'^admin/data/maintenance$', common.data_maintenance, name='data_maintenance'),
    url(r'^admin/storage/$', common.storage, name='storage'),
    url(r'^admin/storage/files$', common.files, name='files'),
    url(r'^admin/storage/files/search$', common.files_search, name='files_search'),
    url(r'^admin/storage/files/([0-9]+)/$', common.document_file_read, name='document_file_read'),

    url(r'^catalog/$', common.catalog, name='catalog'),

    url(r'^institution/$', institution.institution, name='institution'),
    url(r'^institution/mandates/$', institution.mandates, name='mandates'),

    url(r'^learning_units/$', learning_unit.learning_units, name='learning_units'),
    url(r'^learning_units/search$', learning_unit.learning_units_search, name='learning_units_search'),
    url(r'^learning_units/([0-9]+)/$', learning_unit.learning_unit_read, name='learning_unit_read'),

    url(r'^my_osis/$', my_osis.my_osis_index, name="my_osis"),
    url(r'^my_osis/management_tasks/messages_templates', my_osis.messages_templates_index, name="messages_templates"),
    url(r'^my_osis/my_messages/$', my_osis.my_messages_index, name="my_messages"),
    url(r'^my_osis/my_messages/action/$', my_osis.my_messages_action, name="my_messages_action"),
    url(r'^my_osis/my_messages/read/([0-9]+)/$', my_osis.read_message, name="read_my_message"),
    url(r'^my_osis/my_messages/delete/([0-9]+)/$', my_osis.delete_from_my_messages, name="delete_my_message"),
    url(r'^my_osis/my_messages/send_message_again/([0-9]+)/$', my_osis.send_message_again,
        name='send_message_again'),
    url(r'^my_osis/profile/$', my_osis.profile, name='profile'),
    url(r'^my_osis/profile/lang$', my_osis.profile_lang, name='profile_lang'),

    url(r'^noscript/$', common.noscript, name='noscript'),

    url(r'^offers/$', offer.offers, name='offers'),
    url(r'^offers/search$', offer.offers_search, name='offers_search'),
    url(r'^offers/([0-9]+)/$', offer.offer_read, name='offer_read'),
    url(r'^offers/([0-9]+)/score_encoding$', offer.score_encoding, name='offer_score_encoding'),

    url(r'^offer_year_calendars/([0-9]+)/$', offer.offer_year_calendar_read, name='offer_year_calendar_read'),
    url(r'^offer_year_calendars/edit/([0-9]+)/$', offer.offer_year_calendar_edit, name='offer_year_calendar_edit'),
    url(r'^offer_year_calendars/save/([0-9]+)/$', offer.offer_year_calendar_save, name='offer_year_calendar_save'),

    url(r'^organizations/$', organization.organizations, name='organizations'),
    url(r'^organizations/search$', organization.organizations_search, name='organizations_search'),
    url(r'^organizations/([0-9]+)/$', organization.organization_read, name='organization_read'),
    url(r'^organization/edit/([0-9]+)/$', organization.organization_edit, name='organization_edit'),
    url(r'^organization/save/([0-9]+)/$', organization.organization_save, name='organization_save'),
    url(r'^organization/save/$', organization.organization_new, name='organization_save_new'),
    url(r'^organization/create/$', organization.organization_create, name='organization_create'),

    url(r'^organization_address/read/([0-9]+)/$', organization.organization_address_read,
        name='organization_address_read'),
    url(r'^organization_address/edit/([0-9]+)/$', organization.organization_address_edit,
        name='organization_address_edit'),
    url(r'^organization_address/save/([0-9]+)/$', organization.organization_address_save,
        name='organization_address_save'),
    url(r'^organization_address/save/$', organization.organization_address_new, name='organization_address_save_new'),
    url(r'^organization_address/create/([0-9]+)/$', organization.organization_address_create,
        name='organization_address_create'),
    url(r'^organization_address/delete/([0-9]+)/$', organization.organization_address_delete,
        name='organization_address_delete'),

    url(r'^structures/$', institution.structures, name='structures'),
    url(r'^structures/search$', institution.structures_search, name='structures_search'),
    url(r'^structures/([0-9]+)/$', institution.structure_read, name='structure_read'),
    url(r'^structure/([0-9]+)/diagram/$', institution.structure_diagram, name='structure_diagram'),
    url(r'^structure/([0-9]+)/address/$', institution.structure_address, name='structure_address'),

    url(r'^studies/$', common.studies, name='studies'),
    url(r'^studies/assessments/$', common.assessments, name='assessments'),
    url(r'^studies/assessments/outside_scores_encodings_period/$',
        score_encoding.outside_scores_encodings_period, name='outside_scores_encodings_period'),
    url(r'^studies/assessments/scores_encoding/$', score_encoding.scores_encoding, name='scores_encoding'),
    url(r'^studies/assessments/scores_encoding/online/(?P<learning_unit_year_id>[0-9]+)/$',
        score_encoding.online_encoding, name='online_encoding'),
    url(r'^studies/assessments/scores_encoding/search/$', score_encoding.refresh_list, name='refresh_list'),
    url(r'^studies/assessments/scores_encoding/specific_criteria/$',
        score_encoding.specific_criteria, name='specific_criteria'),
    url(r'^studies/assessments/scores_encoding/specific_criteria/submission/$',
        score_encoding.specific_criteria_submission, name='specific_criteria_submission'),
    url(r'^studies/assessments/scores_encoding/search_specific_criteria/$',
        score_encoding.search_by_specific_criteria, name='search_by_specific_criteria'),

    url(r'^studies/assessments/scores_encoding/online/(?P<learning_unit_year_id>[0-9]+)/form$',
        score_encoding.online_encoding_form, name='online_encoding_form'),
    url(r'^studies/assessments/scores_encoding/online/([0-9]+)/submission$',
        score_encoding.online_encoding_submission, name='online_encoding_submission'),
    url(r'^studies/assessments/scores_encoding/online/(?P<learning_unit_year_id>[0-9]+)/double_form$',
        score_encoding.online_double_encoding_form, name='online_double_encoding_form'),

    url(r'^studies/assessments/scores_encoding/online/(?P<learning_unit_year_id>[0-9]+)(?:/(?P<tutor_id>[0-9]+))?/double_validation$',
        score_encoding.online_double_encoding_validation, name='online_double_encoding_validation'),
    url(r'^studies/assessments/scores_encoding/notes_printing_all(?:/(?P<tutor_id>[0-9]+))?(?:/(?P<offer_id>[0-9]+))?/$',
        score_encoding.notes_printing_all, name='notes_printing_all'),
    url(r'^studies/assessments/scores_encoding/notes_printing/(?P<learning_unit_year_id>[0-9]+)(?:/(?P<tutor_id>[0-9]+))?/$',
        score_encoding.notes_printing, name='notes_printing'),
    url(r'^studies/assessments/scores_encoding/xlsdownload/([0-9]+)/([0-9]+)/$',
        score_encoding.export_xls, name='scores_encoding_download'),
    url(r'^studies/assessments/scores_encoding/upload/(?P<learning_unit_year_id>[0-9]+)/$',
        upload_xls_utils.upload_scores_file, name='upload_encoding'),

]
