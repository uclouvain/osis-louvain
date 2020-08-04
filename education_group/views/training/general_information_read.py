##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
import functools

from django.shortcuts import redirect
from django.urls import reverse

from base.business.education_groups import general_information_sections
from base.models.enums.publication_contact_type import PublicationContactType
from education_group.views import serializers
from education_group.views.training.common_read import TrainingRead, Tab


class TrainingReadGeneralInformation(TrainingRead):
    template_name = "education_group_app/training/general_informations_read.html"
    active_tab = Tab.GENERAL_INFO

    def get(self, request, *args, **kwargs):
        if not self.have_general_information_tab():
            return redirect(reverse('training_identification', kwargs=self.kwargs))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        node = self.get_object()
        return {
            **super().get_context_data(**kwargs),
            "sections": self.get_sections(),
            "update_label_url": self.get_update_label_url(),
            "publish_url": reverse('publish_general_information', args=[node.year, node.code]) +
            "?path={}".format(self.get_path()),
            "can_edit_information":
                self.request.user.has_perm("base.change_pedagogyinformation", self.education_group_version.offer),
            "show_contacts": self.can_have_contacts(),
            "entity_contact": self.get_entity_contact(),
            "academic_responsibles": self.get_academic_responsibles(),
            "other_academic_responsibles": self.get_other_academic_responsibles(),
            "jury_members": self.get_jury_members(),
            "other_contacts": self.get_other_contacts()
        }

    def get_update_label_url(self):
        offer_id = self.education_group_version.offer_id
        return reverse('education_group_pedagogy_edit', args=[offer_id]) + "?path={}".format(self.get_path())

    def get_sections(self):
        return serializers.general_information.get_sections(self.get_object(), self.request.LANGUAGE_CODE)

    def can_have_contacts(self):
        node = self.get_object()
        return general_information_sections.CONTACTS in \
            general_information_sections.SECTIONS_PER_OFFER_TYPE[node.category.name]['specific']

    def get_entity_contact(self):
        return getattr(
            self.education_group_version.offer.publication_contact_entity_version,
            'verbose_title',
            None
        )

    def get_academic_responsibles(self):
        return self._get_contacts().get(PublicationContactType.ACADEMIC_RESPONSIBLE.name) or []

    def get_other_academic_responsibles(self):
        return self._get_contacts().get(PublicationContactType.OTHER_ACADEMIC_RESPONSIBLE.name) or []

    def get_jury_members(self):
        return self._get_contacts().get(PublicationContactType.JURY_MEMBER.name) or []

    def get_other_contacts(self):
        return self._get_contacts().get(PublicationContactType.OTHER_CONTACT.name) or []

    @functools.lru_cache()
    def _get_contacts(self):
        return serializers.general_information.get_contacts(self.get_object())
