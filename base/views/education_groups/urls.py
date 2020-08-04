##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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

from base.views import education_group
from base.views.education_groups.clear_clipboard import clear_clipboard
from base.views.education_groups.publication_contact import CreateEducationGroupPublicationContactView, \
    UpdateEducationGroupPublicationContactView, EducationGroupPublicationContactDeleteView, \
    UpdateEducationGroupEntityPublicationContactView
from base.views.education_groups.search import EducationGroupTypeAutoComplete
from base.views.education_groups.update import CertificateAimAutocomplete
from education_group import urls as education_group_urls
from . import create, update, delete
from .achievement.urls import urlpatterns as urlpatterns_achievement

urlpatterns = [
    url(
        r'^certificate_aim_autocomplete/$',
        CertificateAimAutocomplete.as_view(),
        name='certificate_aim_autocomplete',
    ),
    url(
        r'^education_group_type_autocomplete/$',
        EducationGroupTypeAutoComplete.as_view(),
        name='education_group_type_autocomplete'
    ),

    url(
        r'^clear_clipboard/$',
        clear_clipboard,
        name='education_group_clear_clipboard'
    ),

    url(
        r'^new/(?P<category>[A-Z_]+)/(?P<education_group_type_pk>[0-9]+)/$',
        create.create_education_group,
        name='new_education_group'
    ),
    url(
        r'^new/(?P<category>[A-Z_]+)/(?P<education_group_type_pk>[0-9]+)/(?P<root_id>[0-9]+)/(?P<parent_id>[0-9]+)/$',
        create.create_education_group,
        name='new_education_group'
    ),
    url(
        r'^validate_field/(?P<category>[A-Z_]+)/', include([
            url(r'^$', create.validate_field, name='validate_education_group_field'),
            url(r'^(?P<education_group_year_pk>[0-9]+)/', create.validate_field, name='validate_education_group_field'),
        ])
    ),
    url(r'^(?P<education_group_year_id>[0-9]+)/', include([
        url(r'^informations/edit/$', education_group.education_group_year_pedagogy_edit,
            name="education_group_pedagogy_edit"),
    ])),
    url(r'^(?P<offer_id>[0-9]+)/(?P<education_group_year_id>[0-9]+)/', include([
        url(r'^update/$', update.update_education_group, name="update_education_group"),
        url(r'^skills_achievements/', include(urlpatterns_achievement)),
        url(r'^delete/$', delete.DeleteGroupEducationView.as_view(), name="delete_education_group"),
    ])),
    url(r'^(?P<year>[0-9]+)/(?P<code>[A-Za-z0-9]+)/', include([
       url(
           r'^admission_conditions/remove_line$',
           education_group.education_group_year_admission_condition_remove_line,
           name='education_group_year_admission_condition_remove_line'),

       url(
           r'^admission_conditions/update_line$',
           education_group.education_group_year_admission_condition_update_line,
           name='education_group_year_admission_condition_update_line'),

       url(
           r'^admission_conditions/update_text$',
           education_group.education_group_year_admission_condition_update_text,
           name='education_group_year_admission_condition_update_text'),

       url(
           r'^admission_conditions/line/order$',
           education_group.education_group_year_admission_condition_line_order,
           name='education_group_year_admission_condition_line_order'),
       url(
           r'^admission_conditions/lang/edit/(?P<language>[A-Za-z-]+)/$',
           education_group.education_group_year_admission_condition_tab_lang_edit,
           name='tab_lang_edit'),
       url(
          r'^publication_contact/(?P<education_group_year_id>[0-9]+)/',
          include([
              url(r'^edit_entity/$',
                  UpdateEducationGroupEntityPublicationContactView.as_view(),
                  name='publication_contact_entity_edit'),
          ])),
       url(r'^publication_contact/', include([
            url(r'^create/$',
                CreateEducationGroupPublicationContactView.as_view(),
                name="publication_contact_create"),
            url(r'^edit/(?P<publication_contact_id>[0-9]+)/$',
                UpdateEducationGroupPublicationContactView.as_view(),
                name="publication_contact_edit"),
            url(r'^delete/(?P<publication_contact_id>[0-9]+)$',
                EducationGroupPublicationContactDeleteView.as_view(),
                name="publication_contact_delete"),
        ])),
    ])),
] + education_group_urls.urlpatterns
