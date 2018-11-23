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
from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from base.views import common
from django.views.i18n import JavaScriptCatalog

packages = ('assessments', 'base')

urlpatterns = (
    url(r'^login/$', common.login, name='login'),
    url(r'^logout/$', common.log_out, name='logout'),
    url(r'^logged_out/$', common.logged_out, name='logged_out'),

    url(r'^' + settings.ADMIN_URL, admin.site.urls),
    url(r'', include('base.urls')),
    url(r'^jsi18n/$', JavaScriptCatalog.as_view(packages=packages), name='javascript-catalog'),
    url(r'^hijack/', include('hijack.urls', namespace='hijack')),
)

if 'assistant' in settings.INSTALLED_APPS:
    urlpatterns += (url(r'^assistants/', include('assistant.urls')),)
if 'internship' in settings.INSTALLED_APPS:
    urlpatterns += (url(r'^internships/', include('internship.urls')),)
if 'dissertation' in settings.INSTALLED_APPS:
    urlpatterns += (url(r'^dissertation/', include('dissertation.urls')),)
if 'assessments' in settings.INSTALLED_APPS:
    urlpatterns += (url(r'^assessments/', include('assessments.urls')),)
if 'attribution' in settings.INSTALLED_APPS:
    urlpatterns += (url(r'^attribution/', include('attribution.urls')),)
if 'webservices' in settings.INSTALLED_APPS:
    urlpatterns += (url(r'^api/', include('webservices.urls')),)
if 'partnership' in settings.INSTALLED_APPS:
    urlpatterns += (url(r'^partnerships/', include('partnership.urls', namespace='partnerships')),)
if 'continuing_education' in settings.INSTALLED_APPS:
    urlpatterns += (url(r'^continuing_education/', include('continuing_education.urls')),)

handler404 = 'base.views.common.page_not_found'
handler403 = 'base.views.common.access_denied'
handler405 = 'base.views.common.method_not_allowed'
handler500 = 'base.views.common.server_error'

admin.site.site_header = 'OSIS'
admin.site.site_title = 'OSIS'
admin.site.index_title = 'Louvain'

if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns += (url(r'^__debug__/', include(debug_toolbar.urls)),)
