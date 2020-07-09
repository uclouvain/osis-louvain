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

from attribution.views import manage_my_courses, attribution
from attribution.views.charge_repartition.create import SelectAttributionView, AddChargeRepartition
from attribution.views.charge_repartition.update import EditChargeRepartition
from attribution.views.learning_unit.create import CreateAttribution
from attribution.views.learning_unit.delete import DeleteAttribution
from attribution.views.learning_unit.update import UpdateAttributionView

urlpatterns = [
    url(r'^manage_my_courses/', include([
        url(r'^$', manage_my_courses.list_my_attributions_summary_editable,
            name='list_my_attributions_summary_editable'),
        url(r'^(?P<learning_unit_year_id>[0-9]+)/', include([
            url(r'^educational_information/$', manage_my_courses.view_educational_information,
                name='view_educational_information'),
            url(r'^edit_educational_information/$',
                manage_my_courses.edit_educational_information,
                name='tutor_edit_educational_information'),
            url(r'^teaching_materials/', include([
                url(r'^create', manage_my_courses.create_teaching_material, name="tutor_teaching_material_create"),
                url(r'^(?P<teaching_material_id>[0-9]+)/edit/', manage_my_courses.update_teaching_material,
                    name="tutor_teaching_material_edit"),
                url(r'^(?P<teaching_material_id>[0-9]+)/delete/', manage_my_courses.delete_teaching_material,
                    name="tutor_teaching_material_delete")
            ])),
        ]))
    ])),
    url(r'^(?P<learning_unit_year_id>[0-9]+)/attributions/', include([
        url(r'^$', attribution.learning_unit_attributions,
            name="learning_unit_attributions"),
        url(r'^select/$', SelectAttributionView.as_view(), name="select_attribution"),
        url(r'^update/(?P<attribution_id>[0-9]+)/$', UpdateAttributionView.as_view(),
            name="update_attribution"),
        url(r'^create/$', CreateAttribution.as_view(),
            name="add_attribution"),
        url(r'^remove/(?P<attribution_id>[0-9]+)/$', DeleteAttribution.as_view(),
            name="remove_attribution"),
        url(r'^charge_repartition/', include([
            url(r'^add/(?P<attribution_id>[0-9]+)/$', AddChargeRepartition.as_view(),
                name="add_charge_repartition"),
            url(r'^edit/(?P<attribution_id>[0-9]+)/$', EditChargeRepartition.as_view(),
                name="edit_charge_repartition"),
        ])),
    ])),
]
