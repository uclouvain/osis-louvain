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
from django.utils.translation import gettext_lazy as _

from attribution.views.learning_unit.common import AttributionBaseViewMixin
from base.business.learning_units import perms
from base.forms.learning_unit.attribution_charge_repartition import AttributionCreationForm, \
    LecturingAttributionChargeForm, PracticalAttributionChargeForm
from base.models.learning_component_year import LearningComponentYear
from base.views.mixins import AjaxTemplateMixin, MultiFormsSuccessMessageMixin, MultiFormsView


class CreateAttribution(AttributionBaseViewMixin, AjaxTemplateMixin, MultiFormsSuccessMessageMixin, MultiFormsView):
    rules = [perms.is_eligible_to_manage_attributions]
    template_name = "attribution/learning_unit/attribution_inner.html"
    form_classes = {
        "attribution_form": AttributionCreationForm,
        "lecturing_charge_form": LecturingAttributionChargeForm,
        "practical_charge_form": PracticalAttributionChargeForm
    }
    prefixes = {
        "attribution_form": "attribution_form",
        "lecturing_charge_form": "lecturing_form",
        "practical_charge_form": "practical_form"
    }

    def get_form_classes(self):
        form_classes = self.form_classes.copy()
        if LearningComponentYear.objects.filter(learning_unit_year=self.luy, type=None).exists():
            del form_classes["practical_charge_form"]
        return form_classes

    def forms_valid(self, forms):
        attribution_form = forms["attribution_form"]
        attribution_form.save()
        return super().forms_valid(forms)

    def get_success_message(self, forms):
        attribution = forms["attribution_form"].instance
        return _("Attribution added for %(tutor)s (%(function)s)") % {"tutor": attribution.tutor.person,
                                                                      "function": _(attribution.get_function_display())}

    def lecturing_charge_form_valid(self, lecturing_charge_form):
        attribution_form = self.instantiated_forms["attribution_form"]
        lecturing_charge_form.save(attribution=attribution_form.instance)

    def practical_charge_form_valid(self, practical_charge_form):
        attribution_form = self.instantiated_forms["attribution_form"]
        practical_charge_form.save(attribution=attribution_form.instance)