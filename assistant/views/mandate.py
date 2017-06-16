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
import time
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext as _
from openpyxl import Workbook
from openpyxl.writer.excel import save_virtual_workbook
from base.models.enums import structure_type
from base.models import academic_year
from base.views import layout
from assistant.forms import MandateForm, structure_inline_formset
from assistant import models as assistant_mdl
from assistant.models import assistant_mandate, mandate_structure, review
from assistant.models.enums import assistant_type, reviewer_role


def user_is_manager(user):
    """Use with a ``user_passes_test`` decorator to restrict access to 
    authenticated users who are manager."""
    
    try:
        if user.is_authenticated():
            return assistant_mdl.manager.Manager.objects.get(person=user.person)
    except ObjectDoesNotExist:
        return False
    

@user_passes_test(user_is_manager, login_url='assistants_home')
def mandate_edit(request, mandate_id):
    mandate = assistant_mdl.assistant_mandate.find_mandate_by_id(mandate_id)
    form = MandateForm(initial={'comment': mandate.comment,
                                'renewal_type': mandate.renewal_type,
                                'absences': mandate.absences,
                                'other_status': mandate.other_status,
                                'contract_duration': mandate.contract_duration,
                                'contract_duration_fte': mandate.contract_duration_fte
                                }, prefix="mand", instance=mandate)
    formset = structure_inline_formset(instance=mandate, prefix="struct")
    
    return layout.render(request, 'mandate_form.html', {'mandate': mandate, 'form': form, 'formset': formset})


@user_passes_test(user_is_manager, login_url='assistants_home')
def mandate_save(request, mandate_id):
    mandate = assistant_mdl.assistant_mandate.find_mandate_by_id(mandate_id)
    form = MandateForm(data=request.POST, instance=mandate, prefix='mand')
    formset = structure_inline_formset(request.POST, request.FILES, instance=mandate, prefix='struct')
    if form.is_valid():
        form.save()
        if formset.is_valid():
            formset.save()
            return mandate_edit(request, mandate.id)
        else:
            return layout.render(request, "mandate_form.html", {'mandate': mandate, 'form': form, 'formset': formset})
    else:
        return layout.render(request, "mandate_form.html", {'mandate': mandate, 'form': form, 'formset': formset})


@user_passes_test(user_is_manager, login_url='assistants_home')
def load_mandates(request):
    return layout.render(request, "load_mandates.html", {})


@user_passes_test(user_is_manager, login_url='assistants_home')
def export_mandates(request):
    xls = generate_xls()
    filename = 'assistants_mandates_{}.xlsx'.format(time.strftime("%Y%m%d_%H%M"))
    response = HttpResponse(xls, content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = "%s%s" % ("attachment; filename=", filename)
    return response


def generate_xls():
    workbook = Workbook(encoding='utf-8')
    worksheet = workbook.active
    worksheet.title = "mandates"
    worksheet.append([_("name"),
                      _("firstname"),
                      _("fgs"),
                      _("sap_id"),
                      _("assistant_type"),
                      _("fulltime_equivalent"),
                      _("entry_date"),
                      _("exit_date"),
                      _("scale"),
                      _("contract_period"),
                      _("eft_contract_period"),
                      _("renewal_type"),
                      _("absences"),
                      _("comments"),
                      _("others_status"),
                      _("sector"),
                      _("faculty"),
                      _("program_commission"),
                      _("institute"),
                      _("pole"),
                      _("phd_supervisor"),
                      _("thesis_title"),
                      _("doctorate_inscription_date"),
                      _("confirmation_test_date"),
                      _("thesis_date"),
                      _("expected_doctorate_date"),
                      _("doctorate_inscription"),
                      _("doctorate_remark"),
                      _("functions_outside_ucl"),
                      _("external_mandate"),
                      _("teaching_percentage"),
                      _("research_percentage"),
                      _("service_percentage"),
                      _("formation_percentage"),
                      _("phd_supervisor_reviewer"),
                      _("phd_supervisor_review"),
                      _("phd_supervisor_justification"),
                      _("phd_supervisor_comment"),
                      _("phd_supervisor_confidential"),
                      _("research_supervisor_reviewer"),
                      _("research_review"),
                      _("research_justification"),
                      _("research_comment"),
                      _("research_confidential"),
                      _("supervision_supervisor_reviewer"),
                      _("supervision_review"),
                      _("supervision_justification"),
                      _("supervision_comment"),
                      _("supervision_confidential"),
                      _("vice_rector_supervisor_reviewer"),
                      _("vice_rector_review"),
                      _("vice_rector_justification"),
                      _("vice_rector_comment"),
                      _("vice_rector_confidential")
                      ])
    mandates = assistant_mandate.find_by_academic_year(academic_year.current_academic_year())
    for mandate in mandates:
        line = construct_line(mandate)
        worksheet.append(line)
    return save_virtual_workbook(workbook)


def construct_line(mandate):
    line = [str(mandate.assistant.person.last_name),
            str(mandate.assistant.person.first_name),
            mandate.assistant.person.global_id,
            mandate.sap_id,
            str(mandate.assistant_type),
            mandate.fulltime_equivalent,
            mandate.entry_date,
            mandate.end_date,
            mandate.scale,
            mandate.contract_duration,
            mandate.contract_duration_fte,
            mandate.renewal_type,
            mandate.absences,
            mandate.comment,
            mandate.other_status,
            ]
    line += get_structures_for_mandate(mandate)
    line += get_assistant_doctorate_details(mandate)
    line += [mandate.external_functions,
             mandate.external_contract]
    line += [mandate.tutoring_percent,
             mandate.research_percent,
             mandate.service_activities_percent,
             mandate.formation_activities_percent
             ]
    line += get_reviews(mandate)
    return line


def get_structures_for_mandate(mandate):
    sector = mandate_structure.find_by_mandate_and_type(mandate, structure_type.SECTOR).first()
    structures = [sector.structure.acronym] if sector is not None else ['']
    faculty = mandate_structure.find_by_mandate_and_type(mandate, structure_type.FACULTY).first()
    structures += [faculty.structure.acronym] if faculty is not None else ['']
    program_commission = mandate_structure.find_by_mandate_and_type(mandate, structure_type.PROGRAM_COMMISSION).first()
    structures += [program_commission.structure.acronym] if program_commission is not None else ['']
    institute = mandate_structure.find_by_mandate_and_type(mandate, structure_type.INSTITUTE).first()
    structures += [institute.structure.acronym] if institute is not None else ['']
    pole = mandate_structure.find_by_mandate_and_type(mandate, structure_type.POLE).first()
    structures += [pole.structure.acronym] if pole is not None else ['']
    return structures


def get_assistant_doctorate_details(mandate):
    if mandate.assistant_type == assistant_type.TEACHING_ASSISTANT:
        return [''] * 8
    else:
        ass = mandate.assistant
        return [
            str(ass.supervisor),
            ass.thesis_title,
            ass.phd_inscription_date,
            ass.confirmation_test_date,
            ass.thesis_date,
            ass.expected_phd_date,
            ass.inscription,
            ass.remark
        ]


def get_reviews(mandate):
    reviews_details = []
    reviews = review.find_by_mandate(mandate.id)
    for idx, rev in enumerate(reviews):
        if rev.reviewer is None:
            reviews_details += [str(rev.mandate.assistant.supervisor)] if rev.mandate.assistant.supervisor is not None \
                else ['']
        elif idx == 0:
            reviews_details.extend(['' for i in range(5)])
            if rev.reviewer.role == reviewer_role.SUPERVISION:
                reviews_details.extend(['' for i in range(5)])
            reviews_details.append(str(rev.reviewer.person))
        reviews_details += [rev.advice] if rev.advice is not None else ['']
        reviews_details += [rev.justification] if rev.justification is not None else ['']
        reviews_details += [rev.remark] if rev.remark is not None else ['']
        reviews_details += [rev.confidential] if rev.confidential is not None else ['']
    return reviews_details
