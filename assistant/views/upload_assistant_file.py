##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib.auth.decorators import login_required
from django.http import *
from assistant import models as mdl
from osis_common.models import document_file as document_file
from django.core.urlresolvers import reverse


@login_required
def download(request, document_file_id):
    assistant_mandate_document = mdl.assistant_document_file.find_by_id(document_file_id)
    document = document_file.find_by_id(assistant_mandate_document.document_file.id)
    filename = document.file_name
    response = HttpResponse(document.file, content_type=document.content_type)
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response


@login_required
def delete(request, mandate_id, document_file_id, url):
    assistant_mandate_document = mdl.assistant_document_file.find_by_id(document_file_id)
    document = document_file.find_by_id(assistant_mandate_document.document_file.id)
    assistant_mandate_document.delete()
    document.delete()
    return HttpResponseRedirect(reverse(url, kwargs={'mandate_id': mandate_id}))


@login_required
def save_uploaded_file(request):
    if request.method == 'POST':
        data = request.POST
        assistant_mandate = None
        if request.POST.get('mandate_id'):
            assistant_mandate = mdl.assistant_mandate.find_mandate_by_id(request.POST['mandate_id'])
        file_selected = request.FILES['file']
        file = file_selected
        file_name = file_selected.name
        content_type = file_selected.content_type
        description = data['description']
        storage_duration = 0
        new_document = document_file.DocumentFile(file_name=file_name,
                                                  file=file,
                                                  description=description,
                                                  storage_duration=storage_duration,
                                                  application_name='assistant',
                                                  content_type=content_type,
                                                  update_by=request.user)
        new_document.save()
        assistant_mandate_document_file = mdl.assistant_document_file.AssistantDocumentFile()
        assistant_mandate_document_file.assistant_mandate = assistant_mandate
        assistant_mandate_document_file.document_file = new_document
        assistant_mandate_document_file.save()
    return
