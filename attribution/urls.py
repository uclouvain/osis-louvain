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

from attribution.views import summary_responsible, manage_my_courses

urlpatterns = [

    url(r'^summary_responsible_manager/', include([
        url(r'^$', summary_responsible.search,
            name='summary_responsible'),
        url(r'^edit/$', summary_responsible.edit,
            name='summary_responsible_edit'),
        url(r'^update/(?P<pk>[0-9]+)/$', summary_responsible.update,
            name='summary_responsible_update')
    ])),

    url(r'^manage_my_courses/', include([
        url(r'^$', manage_my_courses.list_my_attributions_summary_editable,
            name='list_my_attributions_summary_editable'),
        url(r'^(?P<learning_unit_year_id>[0-9]+)/educational_information$',
            manage_my_courses.view_educational_information,
            name='view_educational_information'),
        url(r'^(?P<learning_unit_year_id>[0-9]+)/edit_educational_information$',
            manage_my_courses.edit_educational_information,
            name='tutor_edit_educational_information'),
    ])),


]
