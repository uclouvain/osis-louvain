##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View

from base.views.common import display_success_messages
from ddd.logic.learning_unit.domain.model.learning_unit import LearningUnitIdentity
from workshops_ddd_ue.django.forms.learning_unit import LearningUnitCreateForm


class LearningUnitCreateView(View):

    template_name = "workshop/learning_unit_create.html"

    def get(self, request, *args, **kwargs):
        form = LearningUnitCreateForm(
            user=self.request.user,
        )
        return render(request, self.template_name, {
            "form": form,
        })

    def post(self, request, *args, **kwargs):
        form = LearningUnitCreateForm(request.POST, user=self.request.user)
        learning_unit_identity = form.save()
        if not form.errors:
            display_success_messages(request, self.get_success_msg(learning_unit_identity), extra_tags='safe')

        return render(request, self.template_name, {
            "form": form,
        })

    def get_success_msg(self, learning_unit_identity: 'LearningUnitIdentity'):
        return _("Learning unit %(code)s (%(academic_year)s) successfully created.") % {
            "code": learning_unit_identity.code,
            "academic_year": learning_unit_identity.academic_year,
        }
