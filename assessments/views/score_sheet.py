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
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from base import models as mdl
from reference import models as mdl_ref
from base.views import layout
from assessments.forms import score_sheet_address, score_sheet_address_entity
from assessments.business import score_encoding_sheet
from django.utils.translation import ugettext_lazy as _
from assessments.models import score_sheet_address as score_sheet_address_model


@login_required
@permission_required('base.can_access_offer', raise_exception=True)
@permission_required('assessments.can_access_scoreencoding', raise_exception=True)
@require_http_methods(["GET"])
def offer_score_encoding_tab(request, offer_year_id):
    context = _get_common_context(request, offer_year_id)
    dict = score_encoding_sheet.get_score_sheet_address(context.get('offer_year'))
    entity_id_selected = dict['entity_id_selected']
    address = dict['address']
    if not address.get('offer_year'):
        address['offer_year'] = offer_year_id
    form = score_sheet_address.ScoreSheetAddressForm(initial=address)
    context.update({'entity_id_selected': entity_id_selected, 'form': form})
    return layout.render(request, "offer/score_sheet_address_tab.html", context)


def _get_common_context(request, offer_year_id):
    offer_year = mdl.offer_year.find_by_id(offer_year_id)
    countries = mdl_ref.country.find_all()
    is_program_manager = mdl.program_manager.is_program_manager(request.user, offer_year=offer_year)
    entity_versions = score_encoding_sheet.get_entity_version_choices(offer_year)
    return locals()


@login_required
@permission_required('base.can_access_offer', raise_exception=True)
@permission_required('assessments.can_access_scoreencoding', raise_exception=True)
@require_http_methods(["POST"])
def save_score_sheet_address(request, offer_year_id):
    entity_version_id_selected = request.POST.get('related_entity')
    context = _get_common_context(request, offer_year_id)
    if entity_version_id_selected:
        return _save_from_entity_address(context, entity_version_id_selected, offer_year_id, request)
    else:
        form = _save_customized_address(request, offer_year_id)
        context.update({'form': form})
        return layout.render(request, "offer/score_sheet_address_tab.html", context)


def _save_customized_address(request, offer_year_id):
    form = score_sheet_address.ScoreSheetAddressForm(request.POST,
                                                     instance=score_sheet_address_model.get_from_offer_year(offer_year_id))
    if form.is_valid():
        form.save()
        messages.add_message(request, messages.SUCCESS, _("Score sheet address was successfully saved."))
    return form


def _save_from_entity_address(context, entity_version_id_selected, offer_year_id, request):
    email_encode = request.POST.get('email')
    form = score_sheet_address_entity.ScoreSheetAddressEntityForm(request.POST)
    if form.is_valid():
        score_encoding_sheet.save_address_from_entity(context.get('offer_year'), entity_version_id_selected,
                                                      request.POST.get('email'))
        messages.add_message(request, messages.SUCCESS, _("Score sheet address was successfully saved."))
        return HttpResponseRedirect(reverse("offer_score_encoding_tab", args=[offer_year_id]))
    else:
        incorrect_email_management(context, email_encode, offer_year_id)
        return layout.render(request, "offer/score_sheet_address_tab.html", context)


def incorrect_email_management(context_param, email_encode, offer_year_id):
    context = context_param
    dict = score_encoding_sheet.get_score_sheet_address(offer_year_id)
    entity_id_selected = dict['entity_id_selected']
    address = dict['address']
    address['email'] = email_encode
    if not address.get('offer_year'):
        address['offer_year'] = offer_year_id
    form = score_sheet_address.ScoreSheetAddressForm(initial=address)
    form.errors['email'] = _('Enter a valid email address.')
    context.update({'form': form})
    context.update({'entity_id_selected': entity_id_selected})
    return context

