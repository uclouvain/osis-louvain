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
from django.conf.urls import url, include

from base.views import education_group
from base.views.education_groups.clear_clipboard import clear_clipboard
from base.views.education_groups.publication_contact import CreateEducationGroupPublicationContactView, \
    UpdateEducationGroupPublicationContactView, EducationGroupPublicationContactDeleteView, \
    UpdateEducationGroupEntityPublicationContactView
from base.views.education_groups.search import EducationGroupTypeAutoComplete
from base.views.education_groups.select import copy_education_group_to_cache, copy_learning_unit_to_cache
from base.views.education_groups.update import CertificateAimAutocomplete
from . import search, create, detail, update, delete
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

    url(r'^$', search.EducationGroupSearch.as_view(), name='education_groups'),
    url(
        r'^select_lu/(?P<learning_unit_year_id>[0-9]+)$',
        copy_learning_unit_to_cache,
        name='copy_learning_unit_to_cache'
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


    url(
        r'^select_type/(?P<category>[A-Z_]+)/$',
        create.SelectEducationGroupTypeView.as_view(),
        name='select_education_group_type'
    ),
    url(
        r'^select_type/(?P<category>[A-Z_]+)/(?P<root_id>[0-9]+)/(?P<parent_id>[0-9]+)/$',
        create.SelectEducationGroupTypeView.as_view(),
        name='select_education_group_type'
    ),

    url(r'^(?P<root_id>[0-9]+)/(?P<education_group_year_id>[0-9]+)/', include([

        url(r'^identification/$', detail.EducationGroupRead.as_view(), name='education_group_read'),
        url(r'^update/$', update.update_education_group, name="update_education_group"),
        url(r'^diplomas/$', detail.EducationGroupDiplomas.as_view(),
            name='education_group_diplomas'),
        url(r'^informations/$', detail.EducationGroupGeneralInformation.as_view(),
            name='education_group_general_informations'),
        url(r'^informations/edit/$', education_group.education_group_year_pedagogy_edit,
            name="education_group_pedagogy_edit"),
        url(r'^informations/publish/$', detail.publish,
            name="education_group_publish"),
        url(r'^administrative/', include([
            url(u'^$', detail.EducationGroupAdministrativeData.as_view(), name='education_group_administrative'),
            url(u'^edit/$', education_group.education_group_edit_administrative_data,
                name='education_group_edit_administrative')
        ])),
        url(r'^select/$', copy_education_group_to_cache, name='copy_education_group_to_cache'),
        url(r'^content/', include([
            url(u'^$', detail.EducationGroupContent.as_view(), name='education_group_content'),
        ])),
        url(r'^utilization/$', detail.EducationGroupUsing.as_view(), name='education_group_utilization'),

        url(r'^skills_achievements/', include(urlpatterns_achievement)),

        url(r'^admission_conditions/$',
            detail.EducationGroupYearAdmissionCondition.as_view(),
            name='education_group_year_admission_condition_edit'),
        url(r'^admission_conditions/remove_line$',
            education_group.education_group_year_admission_condition_remove_line,
            name='education_group_year_admission_condition_remove_line'),

        url(r'^admission_conditions/update_line$',
            education_group.education_group_year_admission_condition_update_line,
            name='education_group_year_admission_condition_update_line'),

        url(r'^admission_conditions/update_text$',
            education_group.education_group_year_admission_condition_update_text,
            name='education_group_year_admission_condition_update_text'),

        url(r'^admission_conditions/line/order$',
            education_group.education_group_year_admission_condition_line_order,
            name='education_group_year_admission_condition_line_order'),
        url(r'^admission_conditions/lang/edit/(?P<language>[A-Za-z-]+)/$',
            education_group.education_group_year_admission_condition_tab_lang_edit,
            name='tab_lang_edit'),
        url(r'^delete/$', delete.DeleteGroupEducationView.as_view(), name="delete_education_group"),

        url(r'^publication_contact/', include([
            url(r'^edit_entity/$',
                UpdateEducationGroupEntityPublicationContactView.as_view(),
                name='publication_contact_entity_edit'),
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
]
