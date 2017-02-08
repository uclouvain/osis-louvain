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
from django.contrib.auth.decorators import login_required
from django.http import *
from django.shortcuts import redirect
from dissertation import models as mdl
from osis_common import models as mdl_osis_common
from osis_common.models.enum import storage_duration


@login_required
def download(request, proposition_pk):
    proposition = mdl.proposition_dissertation.find_by_id(proposition_pk)
    proposition_document = mdl.proposition_document_file.find_by_proposition(proposition).first()
    if proposition_document:
        filename = proposition_document.document_file.file_name
        response = HttpResponse(proposition_document.document_file.file,
                                content_type=proposition_document.document_file.content_type)
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
        return response
    return redirect('manager_proposition_dissertation_detail', pk=proposition.pk)


@login_required
def save_uploaded_file(request):
    data = request.POST
    if request.method == 'POST':
        if request.POST.get('proposition_dissertation_id'):
            proposition = mdl.proposition_dissertation.find_by_id(request.POST['proposition_dissertation_id'])
        file_selected = request.FILES['file']
        file = file_selected
        file_name = file_selected.name
        content_type = file_selected.content_type
        size = file_selected.size
        description = data['description']
        documents = mdl.proposition_document_file.find_by_proposition(proposition)
        for document in documents:
            document.delete()
            old_document = mdl_osis_common.document_file.find_by_id(document.document_file.id)
            old_document.delete()
        new_document = mdl_osis_common.document_file.DocumentFile(file_name=file_name,
                                                                  file=file,
                                                                  description=description,
                                                                  storage_duration=storage_duration.FIVE_YEARS,
                                                                  application_name='dissertation',
                                                                  content_type=content_type,
                                                                  size=size,
                                                                  update_by=request.user)
        new_document.save()
        proposition_file = mdl.proposition_document_file.PropositionDocumentFile()
        proposition_file.proposition = proposition
        proposition_file.document_file = new_document
        proposition_file.save()
    return HttpResponse('')
