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
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static

import base.views.education_groups.create
import base.views.education_groups.search
import base.views.learning_units.common
import base.views.learning_units.create
import base.views.learning_units.delete
import base.views.learning_units.educational_information
import base.views.learning_units.proposal.consolidate
import base.views.learning_units.proposal.delete
import base.views.learning_units.search
import base.views.learning_units.update
from attribution.views import attribution, tutor_application
from base.views import learning_achievement, search
from base.views import learning_unit, offer, common, institution, organization, academic_calendar, \
    my_osis, entity, student, education_group
from base.views.education_groups.update import update_education_group
from base.views.learning_units.external import create as create_external
from base.views.learning_units.external.search import filter_cities_by_country, filter_campus_by_city
from base.views.learning_units.pedagogy.read import learning_unit_pedagogy
from base.views.learning_units.pedagogy.update import learning_unit_pedagogy_edit
from base.views.learning_units.proposal import create, update
from base.views.learning_units.update import update_learning_unit, learning_unit_edition_end_date

urlpatterns = [
    url(r'^$', common.home, name='home'),

    url(r'^academic_actors/$', institution.academic_actors, name='academic_actors'),

    url(r'^academic_calendars/', include([
        url(r'^$', academic_calendar.academic_calendars, name='academic_calendars'),
        url(r'^search$', academic_calendar.academic_calendars_search, name='academic_calendars_search'),
        url(r'^(?P<academic_calendar_id>[0-9]+)/$', academic_calendar.academic_calendar_read,
            name='academic_calendar_read'),
        url(r'^form(?:/(?P<academic_calendar_id>[0-9]+))?/$', academic_calendar.academic_calendar_form,
            name='academic_calendar_form'),
    ])),

    url(r'^academic_year/$', common.academic_year, name='academic_year'),

    url(r'^admin/', include([
        url(r'^data/$', common.data, name='data'),
        url(r'^data/maintenance$', common.data_maintenance, name='data_maintenance'),
        url(r'^storage/$', common.storage, name='storage'),
    ])),

    url(r'^api/v1/', include([
        url(r'^entities/$', entity.post_entities, name='post_entities'),
        url(r'^tutor_application/recompute_portal$', tutor_application.recompute_portal,
            name='recompute_tutor_application_portal'),
        url(r'^attribution/recompute_portal$', attribution.recompute_portal, name='recompute_attribution_portal'),
    ])),

    url(r'^catalog/$', common.catalog, name='catalog'),

    url(r'^entities/', include([
        url(r'^$', institution.entities_search, name='entities'),
        url(r'^(?P<entity_version_id>[0-9]+)/', include([
            url(r'^$', institution.entity_read, name='entity_read'),
            url(r'^address/$', institution.get_entity_address, name='entity_address'),
            url(r'^diagram/$', institution.entity_diagram, name='entity_diagram'),
            url(r'^versions/$', institution.entities_version, name='entities_version'),
        ]))
    ])),

    url(r'^institution/', include([
        url(r'^$', institution.institution, name='institution'),
        url(r'^mandates/$', institution.mandates, name='mandates'),
    ])),

    url(r'^learning_units/', include([
        url(r'^by_activity/', base.views.learning_units.search.learning_units, name='learning_units'),
        url(r'^by_service_course/', base.views.learning_units.search.learning_units_service_course,
            name='learning_units_service_course'),
        url(r'^by_proposal/', base.views.learning_units.search.learning_units_proposal_search,
            name='learning_units_proposal'),
        url(r'^by_borrowed_course/', base.views.learning_units.search.learning_units_borrowed_course,
            name='learning_units_borrowed_course'),
        url(r'^by_summary/', base.views.learning_units.educational_information.learning_units_summary_list,
            name='learning_units_summary'),
        url(r'^by_external/', base.views.learning_units.search.learning_units_external_search,
            name='learning_units_external'),
        url(r'^new/', include([
            url(r'^academic_year_id=(?P<academic_year_id>[0-9]+)$',
                base.views.learning_units.create.create_learning_unit,
                name="learning_unit_create"),
            url(r'^proposal/academic_year_id=(?P<academic_year>[0-9]+)$',
                create.get_proposal_learning_unit_creation_form,
                name="proposal_learning_unit_creation_form"),
            url(r'^external/academic_year_id=(?P<academic_year>[0-9]+)$',
                create_external.get_external_learning_unit_creation_form,
                name="learning_unit_create_external"),
            url(r'^filter_cities_by_country$', filter_cities_by_country, name="filter_cities_by_country"),
            url(r'^filter_campus_by_city$', filter_campus_by_city, name="filter_campus_by_city"),
        ])),

        url(r'^(?P<learning_unit_year_id>[0-9]+)/', include([
            url(r'^$', learning_unit.learning_unit_identification, name='learning_unit'),
            url(r'^formations/$', learning_unit.learning_unit_formations, name="learning_unit_formations"),
            url(r'^components/$', learning_unit.learning_unit_components, name="learning_unit_components"),
            url(r'^pedagogy/$', learning_unit_pedagogy, name="learning_unit_pedagogy"),
            url(r'^pedagogy/edit/$', learning_unit_pedagogy_edit, name="learning_unit_pedagogy_edit"),
            url(r'^attributions/$', learning_unit.learning_unit_attributions, name="learning_unit_attributions"),
            url(r'^proposal/', include([
                url(r'^modification/$', update.learning_unit_modification_proposal,
                    name="learning_unit_modification_proposal"),
                url(r'^suppression/$', update.learning_unit_suppression_proposal,
                    name="learning_unit_suppression_proposal"),
                url(r'^edit/$', update.update_learning_unit_proposal, name="edit_proposal"),
                url(r'^cancel/$', base.views.learning_units.proposal.delete.cancel_proposal_of_learning_unit,
                    name="learning_unit_cancel_proposal"),
            ])),
            url(r'^update_end_date/$', learning_unit_edition_end_date, name="learning_unit_edition"),
            url(r'^update/$', update_learning_unit, name="edit_learning_unit"),
            url(r'^specifications/$', learning_unit.learning_unit_specifications, name="learning_unit_specifications"),
            url(r'^specifications/edit/$', learning_unit.learning_unit_specifications_edit,
                name="learning_unit_specifications_edit"),
            url(r'^component/edit/$', learning_unit.learning_unit_component_edit, name="learning_unit_component_edit"),
            url(r'^class/edit/$', learning_unit.learning_class_year_edit, name="learning_class_year_edit"),
            url(r'^volumes/', base.views.learning_units.update.learning_unit_volumes_management,
                name="learning_unit_volumes_management"),
            url(r'^delete_full/$', base.views.learning_units.delete.delete_all_learning_units_year,
                name="learning_unit_delete_all"),
            url(r'^partim/', include([
                url(r'^new/$', base.views.learning_units.create.create_partim_form, name="learning_unit_create_partim"),
            ])),
            url(r'^achievements/', include([
                url(r'^management/', learning_achievement.management, name="achievement_management"),
                url(r'^(?P<learning_achievement_id>[0-9]+)/edit/', learning_achievement.update,
                    name="achievement_edit"),
                url(r'^create/', learning_achievement.create_first,
                    name="achievement_create_first"),

                url(r'^(?P<learning_achievement_id>[0-9]+)/create/', learning_achievement.create,
                    name="achievement_create"),

            ])),
        ])),
        url(r'^check/(?P<subtype>[A-Z]+)$', base.views.learning_units.common.check_acronym, name="check_acronym"),
        url(r'^outside_period/$', learning_unit.outside_period, name='outside_summary_submission_period'),
        url(r'^email_educational_information_update/$',
            base.views.learning_units.educational_information.send_email_educational_information_needs_update,
            name='email_educational_information_update'),
        url(r'^proposal/consolidate/$', base.views.learning_units.proposal.consolidate.consolidate_proposal,
            name="learning_unit_consolidate_proposal"),
    ])),
    url(r'^proposals/search/$', base.views.learning_units.search.learning_units_proposal_search,
        name="learning_unit_proposal_search"),

    url(r'^my_osis/', include([
        url(r'^$', my_osis.my_osis_index, name="my_osis"),
        url(r'^management_tasks/messages_templates', my_osis.messages_templates_index, name="messages_templates"),
        url(r'^my_messages/', include([
            url(r'^$', my_osis.my_messages_index, name="my_messages"),
            url(r'^action/$', my_osis.my_messages_action, name="my_messages_action"),
            url(r'^(?P<message_id>[0-9]+)/', include([
                url(r'^read/$', my_osis.read_message, name="read_my_message"),
                url(r'^delete/$', my_osis.delete_from_my_messages, name="delete_my_message"),
                url(r'^send_message_again/$', my_osis.send_message_again, name='send_message_again')
            ]))
        ])),
        url(r'^profile/', include([
            url(r'^$', my_osis.profile, name='profile'),
            url(r'^lang/$', my_osis.profile_lang, name='profile_lang'),
            url(r'^lang/edit/([A-Za-z-]+)/$', my_osis.profile_lang_edit, name='lang_edit'),
            url(r'^attributions/$', my_osis.profile_attributions, name='profile_attributions'),
        ]))
    ])),

    url(r'^noscript/$', common.noscript, name='noscript'),

    url(r'^offers/', include([
        url(r'^$', offer.offers, name='offers'),
        url(r'^search$', offer.offers_search, name='offers_search'),
        url(r'^(?P<offer_year_id>[0-9]+)/', include([
            url(r'^$', offer.offer_read, name='offer_read'),
            url(r'^academic_calendar/$', offer.offer_academic_calendar_tab, name='offer_academic_calendar_tab'),
            url(r'^program_managers/$', offer.offer_program_managers_tab, name='offer_program_managers_tab'),
        ]))
    ])),
    url(r'^educationgroups/', include([
        url(r'^$', base.views.education_groups.search.education_groups, name='education_groups'),
        url(r'^new/$', base.views.education_groups.create.create_education_group, name='new_education_group'),
        url(r'^new/(?P<parent_id>[0-9]+)/$', base.views.education_groups.create.create_education_group,
            name='new_education_group'),
        url(r'^(?P<education_group_year_id>[0-9]+)/', include([
            url(r'^$', education_group.education_group_read, name='education_group_read'),
            url(r'^update/$', update_education_group, name="update_education_group"),
            url(r'^diplomas/$', education_group.education_group_diplomas, name='education_group_diplomas'),
            url(r'^informations/$', education_group.education_group_general_informations,
                name='education_group_general_informations'),
            url(r'^informations/edit/$', education_group.education_group_year_pedagogy_edit,
                name="education_group_pedagogy_edit"),

            url(r'^informations/remove$', education_group.education_group_year_pedagogy_remove_term,
                name="education_group_pedagogy_remove_term"),
            url(r'^informations/add$', education_group.education_group_year_pedagogy_add_term,
                name="education_group_pedagogy_add_term"),
            url(r'^informations/get_terms/(?P<language>[a-z\-]+)',
                education_group.education_group_year_pedagogy_get_terms,
                name="education_group_pedagogy_get_terms"),

            url(r'^administrative/', include([
                url(u'^$', education_group.education_group_administrative_data, name='education_group_administrative'),
                url(u'^edit/$', education_group.education_group_edit_administrative_data,
                    name='education_group_edit_administrative')])),
            url(r'^content/$', education_group.education_group_content, name='education_group_content'),
            url(r'^admission_conditions/$',
                education_group.education_group_year_admission_condition_edit,
                name='education_group_year_admission_condition_edit'),
            url(r'^admission_conditions/add_line$',
                education_group.education_group_year_admission_condition_add_line,
                name='education_group_year_admission_condition_add_line'),

            url(r'^admission_conditions/modify_text$',
                education_group.education_group_year_admission_condition_modify_text,
                name='education_group_year_admission_condition_modify_text'),

            url(r'^admission_conditions/get_text$',
                education_group.education_group_year_admission_condition_get_text,
                name='education_group_year_admission_condition_get_text'),

            url(r'^admission_conditions/remove_line$',
                education_group.education_group_year_admission_condition_remove_line,
                name='education_group_year_admission_condition_remove_line'),

            url(r'^admission_conditions/update_line$',
                education_group.education_group_year_admission_condition_update_line,
                name='education_group_year_admission_condition_update_line'),

            url(r'^admission_conditions/get_line$',
                education_group.education_group_year_admission_condition_get_line,
                name='education_group_year_admission_condition_get_line'),
        ])),
    ])),

    url(r'^offer_year_calendars/([0-9]+)/$', offer.offer_year_calendar_read, name='offer_year_calendar_read'),

    url(r'^organizations/', include([
        url(r'^$', organization.organizations, name='organizations'),
        url(r'^search$', organization.organizations_search, name='organizations_search'),
        url(r'^save/$', organization.organization_new, name='organization_save_new'),
        url(r'^create/$', organization.organization_create, name='organization_create'),
        url(r'^(?P<organization_id>[0-9]+)/', include([
            url(r'^$', organization.organization_read, name='organization_read'),
            url(r'^edit/$', organization.organization_edit, name='organization_edit'),
            url(r'^save/$', organization.organization_save, name='organization_save'),
        ])),
    ])),

    url(r'^organization_address/', include([
        url(r'^save/$', organization.organization_address_new, name='organization_address_save_new'),
        url(r'^(?P<organization_address_id>[0-9]+)/', include([
            url(r'^read/$', organization.organization_address_read,
                name='organization_address_read'),
            url(r'^edit/$', organization.organization_address_edit,
                name='organization_address_edit'),
            url(r'^save/$', organization.organization_address_save,
                name='organization_address_save'),
            url(r'^create/$', organization.organization_address_create,
                name='organization_address_create'),
            url(r'^delete/$', organization.organization_address_delete,
                name='organization_address_delete')
        ]))
    ])),

    url(r'^search/', include([
        url(r'^tutors/$', search.search_tutors, name="search_tutors"),
    ])),

    url(r'^studies/$', common.studies, name='studies'),
    url(r'^students/', include([
        url(r'^$', student.students, name='students'),
        url(r'^search$', student.student_search, name='students_search'),
        url(r'^(?P<student_id>[0-9]+)/', include([
            url(r'^$', student.student_read, name='student_read'),
            url(r'^picture$', student.student_picture, name='student_picture'),
        ]))
    ])),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
