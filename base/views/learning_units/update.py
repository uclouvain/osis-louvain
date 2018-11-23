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
from dal import autocomplete
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from waffle.decorators import waffle_flag

from base.business import learning_unit_year_with_context
from base.business.learning_unit_year_with_context import ENTITY_TYPES_VOLUME
from base.business.learning_units.edition import ConsistencyError
from base.forms.learning_unit.edition import LearningUnitEndDateForm
from base.forms.learning_unit.edition_volume import VolumeEditionFormsetContainer
from base.forms.learning_unit.learning_unit_postponement import LearningUnitPostponementForm
from base.models.entity_version import find_pedagogical_entities_version, \
    find_all_current_entities_version
from base.models.enums import learning_unit_year_subtypes
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import Person
from base.views import layout
from base.views.common import display_error_messages, display_success_messages, display_warning_messages
from base.views.learning_unit import learning_unit_components
from base.views.learning_units import perms
from base.views.learning_units.common import get_learning_unit_identification_context, \
    get_common_context_learning_unit_year


@login_required
@waffle_flag("learning_unit_update")
@permission_required('base.can_edit_learningunit_date', raise_exception=True)
@perms.can_perform_end_date_modification
def learning_unit_edition_end_date(request, learning_unit_year_id):
    learning_unit_year = get_object_or_404(LearningUnitYear, pk=learning_unit_year_id)
    person = get_object_or_404(Person, user=request.user)

    context = get_learning_unit_identification_context(learning_unit_year_id, person)

    learning_unit_to_edit = learning_unit_year.learning_unit
    form = LearningUnitEndDateForm(request.POST or None, learning_unit_year=learning_unit_year)
    if form.is_valid():
        try:
            result = form.save()
            display_success_messages(request, result, extra_tags='safe')

            learning_unit_year_id = _get_current_learning_unit_year_id(learning_unit_to_edit, learning_unit_year_id)

            return HttpResponseRedirect(reverse('learning_unit', args=[learning_unit_year_id]))

        except IntegrityError as e:
            display_error_messages(request, e.args[0])

    context['form'] = form
    return render(request, 'learning_unit/simple/update_end_date.html', context)


def _get_current_learning_unit_year_id(learning_unit_to_edit, learning_unit_year_id):
    if not LearningUnitYear.objects.filter(pk=learning_unit_year_id).exists():
        result = LearningUnitYear.objects.filter(learning_unit=learning_unit_to_edit).last().pk
    else:
        result = learning_unit_year_id
    return result


@login_required
@waffle_flag("learning_unit_update")
@permission_required('base.can_edit_learningunit', raise_exception=True)
@perms.can_perform_learning_unit_modification
def update_learning_unit(request, learning_unit_year_id):
    learning_unit_year = get_object_or_404(LearningUnitYear, pk=learning_unit_year_id)
    person = get_object_or_404(Person, user=request.user)

    learning_unit_full_instance = None
    if learning_unit_year.subtype == learning_unit_year_subtypes.PARTIM:
        learning_unit_full_instance = learning_unit_year.parent.learning_unit

    # TODO :: clean code ; end_postponement could be removed from kwargs in this following
    # LearningUnitPostponementForm instantiation + in the template form
    end_postponement = learning_unit_year.academic_year if not bool(int(request.POST.get('postponement', 1))) else None
    postponement_form = LearningUnitPostponementForm(
        person=person,
        start_postponement=learning_unit_year.academic_year,
        end_postponement=end_postponement,
        learning_unit_instance=learning_unit_year.learning_unit,
        learning_unit_full_instance=learning_unit_full_instance,
        data=request.POST or None,
        external=learning_unit_year.is_external(),
    )

    if postponement_form.is_valid():
        # Update current learning unit year
        _save_form_and_display_messages(request, postponement_form)
        return redirect('learning_unit', learning_unit_year_id=learning_unit_year_id)

    context = postponement_form.get_context()
    context["learning_unit_year"] = learning_unit_year
    context["is_update"] = True

    if learning_unit_year.is_external():
        template = "learning_unit/external/update.html"
    else:
        template = 'learning_unit/simple/update.html'

    return render(request, template, context)


@login_required
@waffle_flag("learning_unit_update")
@permission_required('base.can_edit_learningunit', raise_exception=True)
@perms.can_perform_learning_unit_modification
def learning_unit_volumes_management(request, learning_unit_year_id, form_type):
    person = get_object_or_404(Person, user=request.user)
    context = get_common_context_learning_unit_year(learning_unit_year_id, person)

    context['learning_units'] = _get_learning_units_for_context(luy=context['learning_unit_year'],
                                                                with_family=form_type == "full")

    volume_edition_formset_container = VolumeEditionFormsetContainer(request, context['learning_units'], person)

    if volume_edition_formset_container.is_valid() and not request.is_ajax():
        _save_form_and_display_messages(request, volume_edition_formset_container)
        if form_type == "full":
            return HttpResponseRedirect(reverse(learning_unit_components, args=[learning_unit_year_id]))
        else:
            return HttpResponseRedirect(reverse("learning_unit", args=[learning_unit_year_id]))

    context['formsets'] = volume_edition_formset_container.formsets
    context['tab_active'] = 'components'
    context['entity_types_volume'] = ENTITY_TYPES_VOLUME
    context['luy_url'] = 'learning_unit_components' if form_type == "full" else 'learning_unit'
    context['experimental_phase'] = True
    if request.is_ajax():
        return JsonResponse({'errors': volume_edition_formset_container.errors})

    return layout.render(request, "learning_unit/volumes_management.html", context)


def _get_learning_units_for_context(luy, with_family=False):
    if with_family:
        return learning_unit_year_with_context.get_with_context(
            learning_container_year_id=luy.learning_container_year_id
        )
    else:
        return learning_unit_year_with_context.get_with_context(
            learning_unit_year_id=luy.id
        )


def _save_form_and_display_messages(request, form):
    records = None
    try:
        records = form.save()
        display_warning_messages(request, getattr(form, 'warnings', []))
        display_success_messages(request, _('The learning unit has been updated.'))

    except ConsistencyError as e:
        error_list = e.error_list
        error_list.insert(0, _('The learning unit has been updated until %(year)s.')
                          % {'year': e.last_instance_updated.academic_year})
        display_error_messages(request, e.error_list)
    return records


class EntityAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        country = self.forwarded.get('country', None)
        if country and country == "all":
            qs = find_all_current_entities_version().order_by('acronym')
        elif country:
            qs = find_all_current_entities_version().filter(entity__country__id=country).order_by('acronym')
        else:
            qs = find_pedagogical_entities_version()
        if self.q:
            qs = qs.filter(acronym__icontains=self.q).order_by('acronym')
        return qs

    def get_result_label(self, result):
        return format_html(result.verbose_title)
