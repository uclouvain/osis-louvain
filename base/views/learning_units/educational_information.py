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
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django_filters.views import FilterView

from base.business.learning_units.xls_generator import generate_xls_teaching_material
from base.forms.learning_unit.search_form import LearningUnitDescriptionFicheFilter
from base.models.learning_unit_year import LearningUnitYear
from base.utils.cache import CacheFilterMixin
from base.views.common import display_warning_messages, remove_from_session
from base.views.learning_units.search import SUMMARY_LIST


class LearningUnitDescriptionFicheSearch(PermissionRequiredMixin, CacheFilterMixin, FilterView):
    model = LearningUnitYear
    paginate_by = 2000
    template_name = "learning_units.html"
    raise_exception = True

    filterset_class = LearningUnitDescriptionFicheFilter
    permission_required = 'base.can_access_learningunit'
    cache_exclude_params = 'xls_status',

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.request.session['ue_search_type'] = str(_('Description fiche status'))
        remove_from_session(self.request, 'search_url')
        context.update({
            'form': context['filter'].form,
            'is_faculty_manager': self.request.user.person.is_faculty_manager,
            'search_type': SUMMARY_LIST,
            'learning_units_count': context['paginator'].count
        })
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get('xls_status') == "xls_teaching_material":
            try:
                return generate_xls_teaching_material(self.request.user, context['object_list'])
            except ObjectDoesNotExist:
                display_warning_messages(self.request, _("the list to generate is empty.").capitalize())
        return super().render_to_response(context, **response_kwargs)
