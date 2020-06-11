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
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from base import models as mdl
from base.business.learning_unit import CMS_LABEL_PEDAGOGY_FR_ONLY
from base.business.learning_units.pedagogy import is_pedagogy_data_must_be_postponed
from base.business.learning_units.perms import is_eligible_to_update_learning_unit_pedagogy
from base.forms.learning_unit_pedagogy import LearningUnitPedagogyEditForm
from base.models import learning_unit_year
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import Person
from base.models.proposal_learning_unit import ProposalLearningUnit
from base.views import learning_unit
from base.views.common import display_success_messages
from base.views.learning_units import perms
from base.views.learning_units.common import get_common_context_learning_unit_year, get_text_label_translated
from base.views.learning_units.perms import PermissionDecorator
from cms.models.text_label import TextLabel
from reference.models.language import find_language_in_settings


@login_required
@require_http_methods(["POST"])
@perms.can_edit_summary_locked_field
def toggle_summary_locked(request, learning_unit_year_id):
    luy = learning_unit_year.toggle_summary_locked(learning_unit_year_id)
    success_msg = "Update for teacher locked" if luy.summary_locked else "Update for teacher unlocked"
    display_success_messages(request, success_msg)
    return redirect(reverse("learning_unit_pedagogy", kwargs={'learning_unit_year_id': learning_unit_year_id}))


@login_required
@require_http_methods(["GET", "POST"])
@PermissionDecorator(is_eligible_to_update_learning_unit_pedagogy, "learning_unit_year_id", LearningUnitYear)
def learning_unit_pedagogy_edit(request, learning_unit_year_id):
    redirect_url = reverse("learning_unit_pedagogy", kwargs={'learning_unit_year_id': learning_unit_year_id})
    return edit_learning_unit_pedagogy(request, learning_unit_year_id, redirect_url)


def edit_learning_unit_pedagogy(request, learning_unit_year_id, redirect_url):
    if request.method == 'POST':
        _post_learning_unit_pedagogy_form(request)
        return redirect(redirect_url)

    context = get_common_context_learning_unit_year(
        learning_unit_year_id,
        get_object_or_404(Person, user=request.user)
    )
    label_name = request.GET.get('label')
    language = request.GET.get('language')
    text_lb = TextLabel.objects.prefetch_related(
        Prefetch('translatedtextlabel_set', to_attr="translated_text_labels")
    ).get(label=label_name)
    form = LearningUnitPedagogyEditForm(**{
        'learning_unit_year': context['learning_unit_year'],
        'language': language,
        'text_label': text_lb
    })
    form.load_initial()  # Load data from database
    context['form'] = form
    user_language = mdl.person.get_user_interface_language(request.user)
    context['text_label_translated'] = get_text_label_translated(text_lb, user_language)
    context['language_translated'] = find_language_in_settings(language)
    context['cms_label_pedagogy_fr_only'] = CMS_LABEL_PEDAGOGY_FR_ONLY
    context['label_name'] = label_name
    return render(request, "learning_unit/pedagogy_edit.html", context)


def _post_learning_unit_pedagogy_form(request):
    form = LearningUnitPedagogyEditForm(request.POST)
    if form.is_valid():
        form.save()
        last_academic_year_reported = form.luys[-1] if len(form.luys) >= 2 else None
        msg = build_success_message(last_academic_year_reported, form.luys[0])
        display_success_messages(request, msg)


def build_success_message(last_luy_reported, luy):
    default_message = _("The learning unit has been updated (without report).")
    proposal = ProposalLearningUnit.objects.filter(learning_unit_year__learning_unit=luy.learning_unit).first()

    if last_luy_reported and is_pedagogy_data_must_be_postponed(luy):
        msg = "{} {}.".format(
            _("The learning unit has been updated"),
            _("and postponed until %(year)s") % {
                "year": last_luy_reported.academic_year
            }
        )
    elif proposal and learning_unit.proposal_is_on_same_year(proposal=proposal, base_luy=luy):
        msg = "{}. {}.".format(
            _("The learning unit has been updated"),
            _("The learning unit is in proposal, the report from %(proposal_year)s will be done at "
              "consolidation") % {
                'proposal_year': proposal.learning_unit_year.academic_year
            }
        )
    elif proposal and learning_unit.proposal_is_on_future_year(proposal=proposal, base_luy=luy):
        msg = "{} ({}).".format(
            _("The learning unit has been updated"),
            _("the report has not been done from %(proposal_year)s because the LU is in proposal") % {
                'proposal_year': proposal.learning_unit_year.academic_year
            }
        )
    else:
        msg = "{}".format(default_message)

    return msg
