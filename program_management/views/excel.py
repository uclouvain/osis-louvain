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
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from base.models.education_group_year import EducationGroupYear
from osis_common.document.xls_build import CONTENT_TYPE_XLS
from program_management.business.excel import EducationGroupYearLearningUnitsPrerequisitesToExcel, \
    EducationGroupYearLearningUnitsIsPrerequisiteOfToExcel
from program_management.business.excel_ue_in_of import EducationGroupYearLearningUnitsContainedToExcel
from program_management.forms.custom_xls import CustomXlsForm


@login_required
@permission_required('base.can_access_education_group', raise_exception=True)
def get_learning_unit_prerequisites_excel(request, education_group_year_pk):
    education_group_year = get_object_or_404(EducationGroupYear, pk=education_group_year_pk)
    excel = EducationGroupYearLearningUnitsPrerequisitesToExcel(education_group_year).to_excel()
    response = HttpResponse(excel, content_type=CONTENT_TYPE_XLS)
    filename = "{workbook_name}.xlsx".format(
        workbook_name=str(_("prerequisites-%(year)s-%(acronym)s") % {
            "year": education_group_year.academic_year.year,
            "acronym": education_group_year.acronym
        })
    )
    response['Content-Disposition'] = "%s%s" % ("attachment; filename=", filename)
    return response


@login_required
@permission_required('base.can_access_education_group', raise_exception=True)
def get_learning_units_is_prerequisite_for_excel(request, education_group_year_pk):
    education_group_year = get_object_or_404(EducationGroupYear, pk=education_group_year_pk)
    excel = EducationGroupYearLearningUnitsIsPrerequisiteOfToExcel(education_group_year).to_excel()
    response = HttpResponse(excel, content_type=CONTENT_TYPE_XLS)
    filename = "{workbook_name}.xlsx".format(
        workbook_name=str(_("is_prerequisite_of-%(year)s-%(acronym)s") % {
            "year": education_group_year.academic_year.year,
            "acronym": education_group_year.acronym
        })
    )
    response['Content-Disposition'] = "%s%s" % ("attachment; filename=", filename)
    return response


@login_required
@permission_required('base.can_access_education_group', raise_exception=True)
def get_learning_units_of_training_for_excel(request, root_id, education_group_year_pk):
    education_group_year = get_object_or_404(EducationGroupYear, pk=education_group_year_pk)
    root = get_object_or_404(EducationGroupYear, pk=root_id)
    custom_xls_form = CustomXlsForm(
        request.POST or None)
    excel = EducationGroupYearLearningUnitsContainedToExcel(root, education_group_year, custom_xls_form).to_excel()
    response = HttpResponse(excel, content_type=CONTENT_TYPE_XLS)
    filename = "{workbook_name}.xlsx".format(
        workbook_name=str(_("LearningUnitList-%(year)s-%(acronym)s") % {
            "year": education_group_year.academic_year.year,
            "acronym": education_group_year.acronym
        })
    )
    response['Content-Disposition'] = "%s%s" % ("attachment; filename=", filename)
    return response
