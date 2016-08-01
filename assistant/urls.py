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
from assistant.views import mandate, home, assistant_form, assistant
from assistant.views import mandates_list, reviewer_mandates_list, reviewer_review, reviewer_delegation

urlpatterns = [
    # S'il vous plaît, organiser les urls par ordre alphabétique.
    url(r'^home$', home.assistant_home, name='assistants_home'),
    url(r'^manager/mandates/(?P<mandate_id>\d+)/edit/$', mandate.mandate_edit, name='mandate_read'),
    url(r'^manager/mandates/(?P<mandate_id>\d+)/save/$', mandate.mandate_save, name='mandate_save'),
    url(r'^manager/mandates/load/$', mandate.load_mandates, name='load_mandates'),
    url(r'^manager/mandates/$', mandates_list.MandatesListView.as_view(), name='mandates_list'),
    url(r'^pst/access_denied$', home.access_denied, name='access_denied'),
    url(r'^pst/form_part1/edit/(?P<mandate_id>\d+)/$', assistant_form.form_part1_edit, name='form_part1_edit'),
    url(r'^pst/form_part1/save/(?P<mandate_id>\d+)/$', assistant_form.form_part1_save, name='form_part1_save'),
    url(r'^pst/form_part5/edit/(?P<mandate_id>\d+)/$', assistant_form.form_part5_edit, name='form_part5_edit'),
    url(r'^pst/form_part5/save/(?P<mandate_id>\d+)/$', assistant_form.form_part5_save, name='form_part5_save'),
    url(r'^pst/form_part6/edit/(?P<mandate_id>\d+)/$', assistant_form.form_part6_edit, name='form_part6_edit'),
    url(r'^pst/form_part6/save/(?P<mandate_id>\d+)/$', assistant_form.form_part6_save, name='form_part6_save'),
    url(r'^pst/mandate/(?P<mandate_id>\d+)/state/$', assistant.mandate_change_state, name='mandate_change_state'),
    url(r'^pst/mandates/$', assistant.AssistantMandatesListView.as_view(), name='assistant_mandates'),
    url(r'^reviewer/delegation/$', reviewer_delegation.StructuresListView.as_view(), name='reviewer_delegation'),
    url(r'^reviewer/structure/(?P<structure_id>\d+)/add_reviewer$', reviewer_delegation.addReviewerForStructure, name='reviewer_delegation_add'),
    url(r'^reviewer/mandates/$', reviewer_mandates_list.MandatesListView.as_view(), name='reviewer_mandates_list'),
    url(r'^reviewer/review/edit/(?P<mandate_id>\d+)/$', reviewer_review.review_edit, name='review_edit'),
    url(r'^reviewer/review/save/(?P<review_id>\d+)/(?P<mandate_id>\d+)/$',
        reviewer_review.review_save, name='review_save'),
    url(r'^reviewer/review/view/(?P<review_id>\d+)/$', reviewer_review.review_view, name='review_view'),
    
]
