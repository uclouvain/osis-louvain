############################################################################
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
############################################################################
from django.conf import settings

from base.business.education_groups import perms
from base.views.education_groups.detail import EducationGroupGenericDetailView
from cms.enums import entity_name
from cms.models import translated_text

CMS_LABEL_PROGRAM_AIM = 'skills_and_achievements_introduction'
CMS_LABEL_ADDITIONAL_INFORMATION = 'skills_and_achievements_additional_text'


class EducationGroupSkillsAchievements(EducationGroupGenericDetailView):
    template_name = "education_group/tab_skills_achievements.html"
    cms_translated_texts = None

    def can_show_view(self):
        return self.show_skills_and_achievements()

    def get_achievements(self):
        return self.object.educationgroupachievement_set.all().prefetch_related('educationgroupdetailedachievement_set')

    def find_translated_texts(self, text_label_name, language_code):
        if self.cms_translated_texts is None:
            text_labels = [CMS_LABEL_PROGRAM_AIM, CMS_LABEL_ADDITIONAL_INFORMATION]
            self.cms_translated_texts = translated_text.search(
                entity=entity_name.OFFER_YEAR,
                reference=self.object.pk,
                text_labels_name=text_labels
            ).select_related('text_label')
        return next(
            (obj for obj in self.cms_translated_texts
             if obj.text_label.label == text_label_name and obj.language == language_code),
            None
        )

    def get_french_program_aim(self):
        return self.find_translated_texts(CMS_LABEL_PROGRAM_AIM, settings.LANGUAGE_CODE_FR)

    def get_english_program_aim(self):
        return self.find_translated_texts(CMS_LABEL_PROGRAM_AIM, settings.LANGUAGE_CODE_EN)

    def get_french_additional_info(self):
        return self.find_translated_texts(CMS_LABEL_ADDITIONAL_INFORMATION, settings.LANGUAGE_CODE_FR)

    def get_english_additional_info(self):
        return self.find_translated_texts(CMS_LABEL_ADDITIONAL_INFORMATION, settings.LANGUAGE_CODE_EN)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        perm_name = 'base.change_commonadmissioncondition' if self.object.is_common else \
            'base.change_admissioncondition'

        context.update({
            'LANGUAGE_CODE_FR': settings.LANGUAGE_CODE_FR,
            'LANGUAGE_CODE_EN': settings.LANGUAGE_CODE_EN,
            'can_edit_information': self.request.user.has_perm(perm_name, self.object)
        })

        context["education_group_achievements"] = self.get_achievements()
        context[CMS_LABEL_PROGRAM_AIM] = {
            settings.LANGUAGE_CODE_FR: self.get_french_program_aim(),
            settings.LANGUAGE_CODE_EN: self.get_english_program_aim(),
        }
        context[CMS_LABEL_ADDITIONAL_INFORMATION] = {
            settings.LANGUAGE_CODE_FR: self.get_french_additional_info(),
            settings.LANGUAGE_CODE_EN: self.get_english_additional_info()
        }
        return context
