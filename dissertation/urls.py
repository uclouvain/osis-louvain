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
from dissertation.views import dissertation, proposition_dissertation, information, offer_proposition

urlpatterns = [
    url(r'^$', dissertation.dissertations, name='dissertations'),

    url(r'^informations/$', information.informations, name='informations'),
    url(r'^informations_detail_stats/$', information.informations_detail_stats, name='informations_detail_stats'),
    url(r'^informations_edit/$', information.informations_edit, name='informations_edit'),

    url(r'^manager_dissertations_delete/(?P<pk>[0-9]+)$', dissertation.manager_dissertations_delete,
        name='manager_dissertations_delete'),
    url(r'^manager_dissertations_detail/(?P<pk>[0-9]+)$', dissertation.manager_dissertations_detail,
        name='manager_dissertations_detail'),
    url(r'^manager_dissertations_detail_updates/(?P<pk>[0-9]+)$', dissertation.manager_dissertations_detail_updates,
        name='manager_dissertations_detail_updates'),
    url(r'^manager_dissertations_edit/(?P<pk>[0-9]+)$', dissertation.manager_dissertations_edit,
        name='manager_dissertations_edit'),
    url(r'^manager_dissertations_jury_edit/(?P<pk>[0-9]+)$', dissertation.manager_dissertations_jury_edit,
        name='manager_dissertations_jury_edit'),
    url(r'^manager_dissertations_jury_new/(?P<pk>[0-9]+)$', dissertation.manager_dissertations_jury_new,
        name='manager_dissertations_jury_new'),
    url(r'^manager_dissertations_list$', dissertation.manager_dissertations_list,
        name='manager_dissertations_list'),
    url(r'^manager_dissertations_new$', dissertation.manager_dissertations_new,
        name='manager_dissertations_new'),
    url(r'^manager_dissertations_role_delete/(?P<pk>[0-9]+)$', dissertation.manager_dissertations_role_delete,
        name='manager_dissertations_role_delete'),
    url(r'^manager_dissertations_search$', dissertation.manager_dissertations_search,
        name='manager_dissertations_search'),
    url(r'^manager_dissertations_to_dir_ko/(?P<pk>[0-9]+)$', dissertation.manager_dissertations_to_dir_ko,
        name='manager_dissertations_to_dir_ko'),
    url(r'^manager_dissertations_to_dir_ok/(?P<pk>[0-9]+)$', dissertation.manager_dissertations_to_dir_ok,
        name='manager_dissertations_to_dir_ok'),
    url(r'^manager_dissertations_to_dir_ok_comm_list/(?P<pk>[0-9]+)$',
        dissertation.manager_dissertations_to_dir_ok_comm_list,
        name='manager_dissertations_to_dir_ok_comm_list'),
    url(r'^manager_dissertations_to_dir_ok_eval_list/(?P<pk>[0-9]+)$',
        dissertation.manager_dissertations_to_dir_ok_eval_list,
        name='manager_dissertations_to_dir_ok_eval_list'),
    url(r'^manager_dissertations_to_dir_submit/(?P<pk>[0-9]+)$', dissertation.manager_dissertations_to_dir_submit,
        name='manager_dissertations_to_dir_submit'),
    url(r'^manager_dissertations_to_dir_submit_list/(?P<pk>[0-9]+)$',
        dissertation.manager_dissertations_to_dir_submit_list,
        name='manager_dissertations_to_dir_submit_list'),
    url(r'^manager_dissertations_wait_list$', dissertation.manager_dissertations_wait_list,
        name='manager_dissertations_wait_list'),
    url(r'^manager_dissertations_wait_comm_list$', dissertation.manager_dissertations_wait_comm_list,
        name='manager_dissertations_wait_comm_list'),
    url(r'^manager_dissertations_wait_eval_list$', dissertation.manager_dissertations_wait_eval_list,
        name='manager_dissertations_wait_eval_list'),
    url(r'^manager_dissertations_wait_recep_list$', dissertation.manager_dissertations_wait_recep_list,
        name='manager_dissertations_wait_recep_list'),


    url(r'^manager_informations/$', information.manager_informations, name='manager_informations'),
    url(r'^manager_informations_add/$', information.manager_informations_add, name='manager_informations_add'),
    url(r'^manager_informations_detail/(?P<pk>[0-9]+)/$', information.manager_informations_detail,
        name='manager_informations_detail'),
    url(r'^manager_informations_detail_list/(?P<pk>[0-9]+)/$', information.manager_informations_detail_list,
        name='manager_informations_detail_list'),
    url(r'^manager_informations_detail_stats/(?P<pk>[0-9]+)/$', information.manager_informations_detail_stats,
        name='manager_informations_detail_stats'),
    url(r'^manager_informations_search$', information.manager_informations_search, name='manager_informations_search'),
    url(r'^manager_informations_list_request/$', information.manager_informations_list_request,
        name='manager_informations_list_request'),

    url(r'^manager_informations/(?P<pk>[0-9]+)/edit/$', information.manager_informations_edit,
        name='manager_informations_edit'),

    url(r'^manager_offer_parameters/$', offer_proposition.manager_offer_parameters, name='manager_offer_parameters'),
    url(r'^manager_offer_parameters_detail/(?P<pk>[0-9]+)/$', offer_proposition.manager_offer_parameters_detail,
        name='manager_offer_parameters_detail'),
    url(r'^manager_offer_parameters/(?P<pk>[0-9]+)/edit/$', offer_proposition.manager_offer_parameters_edit,
        name='manager_offer_parameters_edit'),

    url(r'^manager_proposition_dissertations/$', proposition_dissertation.manager_proposition_dissertations,
        name='manager_proposition_dissertations'),
    url(r'^manager_proposition_dissertation_new$', proposition_dissertation.manager_proposition_dissertation_new,
        name='manager_proposition_dissertation_new'),
    url(r'^manager_proposition_dissertation_detail/(?P<pk>[0-9]+)/$',
        proposition_dissertation.manager_proposition_dissertation_detail,
        name='manager_proposition_dissertation_detail'),
    url(r'^manager_proposition_dissertation/(?P<pk>[0-9]+)/delete/$',
        proposition_dissertation.manager_proposition_dissertation_delete,
        name='manager_proposition_dissertation_delete'),
    url(r'^manager_proposition_dissertation/(?P<pk>[0-9]+)/edit/$',
        proposition_dissertation.manage_proposition_dissertation_edit, name='manager_proposition_dissertation_edit'),

    url(r'^manager_proposition_dissertation_search$', proposition_dissertation.manager_proposition_dissertations_search,
        name='manager_proposition_dissertations_search'),

    url(r'^dissertations_list$', dissertation.dissertations_list,
        name='dissertations_list'),
    url(r'^dissertations_search$', dissertation.dissertations_search,
        name='dissertations_search'),
    url(r'^dissertations_detail/(?P<pk>[0-9]+)$', dissertation.dissertations_detail,
        name='dissertations_detail'),
    url(r'^dissertations_detail_updates/(?P<pk>[0-9]+)$', dissertation.dissertations_detail_updates,
        name='dissertations_detail_updates'),
    url(r'^dissertations_delete/(?P<pk>[0-9]+)$', dissertation.dissertations_delete,
        name='dissertations_delete'),
    url(r'^dissertations_to_dir_submit/(?P<pk>[0-9]+)$', dissertation.dissertations_to_dir_submit,
        name='dissertations_to_dir_submit'),
    url(r'^dissertations_to_dir_ok/(?P<pk>[0-9]+)$', dissertation.dissertations_to_dir_ok,
        name='dissertations_to_dir_ok'),
    url(r'^dissertations_to_dir_ko/(?P<pk>[0-9]+)$', dissertation.dissertations_to_dir_ko,
        name='dissertations_to_dir_ko'),
    url(r'^dissertations_wait_list$', dissertation.dissertations_wait_list,
        name='dissertations_wait_list'),

    url(r'^proposition_dissertations/$', proposition_dissertation.proposition_dissertations,
        name='proposition_dissertations'),
    url(r'^proposition_dissertation/(?P<pk>[0-9]+)/delete/$', proposition_dissertation.proposition_dissertation_delete,
        name='proposition_dissertation_delete'),
    url(r'^proposition_dissertation/(?P<pk>[0-9]+)/edit/$', proposition_dissertation.proposition_dissertation_edit,
        name='proposition_dissertation_edit'),
    url(r'^proposition_dissertation_detail/(?P<pk>[0-9]+)/$', proposition_dissertation.proposition_dissertation_detail,
        name='proposition_dissertation_detail'),
    url(r'^proposition_dissertation_my$', proposition_dissertation.proposition_dissertation_my,
        name='proposition_dissertation_my'),
    url(r'^proposition_dissertation_new$', proposition_dissertation.proposition_dissertation_new,
        name='proposition_dissertation_new'),
    url(r'^proposition_dissertations_search$', proposition_dissertation.proposition_dissertations_search,
        name='proposition_dissertations_search'),
]
