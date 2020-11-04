# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import transaction, Error

from base.business.education_groups.postponement import ConsistencyError
from base.business.utils.model import update_related_object
from base.business.utils.postponement import AutomaticPostponement

from base.models.education_group_year import EducationGroupYear
from cms.enums import entity_name
from cms.models.translated_text import TranslatedText


class ReddotEducationGroupAutomaticPostponement(AutomaticPostponement):
    """ When the academic calendar Education group edition is open,
    We have to copy all the reddot data from N-1 to N.

    That copy included :
        Related data from CMS
        EducationGroupPublicationContact
        publication_contact_entity
        EducationGroupsAchievements
        AdmissionCondition

    We'll override the data so if there are some data in N, there'll be deleted before the copy of the N-1 data.
    """
    model = EducationGroupYear

    def get_queryset(self, queryset=None):
        """ By default, we can copy the data only for the current academic_year,
        but it is possible to override that behavior if a query is given.
        """
        if not queryset:
            queryset = self.model.objects.filter(academic_year=self.current_year)

        return queryset

    def postpone(self):

        for obj in self.to_duplicate:
            try:
                with transaction.atomic():
                    old_obj = obj.previous_year()
                    if not old_obj:
                        # If old obj is empty, there are no data in the past.
                        continue

                    self._postpone_cms(old_obj, obj)
                    self._postpone_publication(old_obj, obj)
                    self._postpone_achievement(old_obj, obj)
                    self._postpone_admission(old_obj, obj)

                    self.result.append(obj)

            # General catch to be sure to not stop the rest of the duplication
            except (Error, ObjectDoesNotExist, MultipleObjectsReturned, ConsistencyError):
                self.errors.append(obj)

        return self.result, self.errors

    @staticmethod
    def _postpone_cms(old_egy, new_egy):
        TranslatedText.objects.filter(entity=entity_name.OFFER_YEAR, reference=str(new_egy.pk)).delete()

        for text in TranslatedText.objects.filter(entity=entity_name.OFFER_YEAR, reference=str(old_egy.pk)):
            update_related_object(text, "reference", str(new_egy.pk))

    @staticmethod
    def _postpone_publication(old_egy: EducationGroupYear, new_egy: EducationGroupYear):
        new_egy.educationgrouppublicationcontact_set.all().delete()

        for publication in old_egy.educationgrouppublicationcontact_set.all():
            update_related_object(publication, "education_group_year", new_egy)

        new_egy.publication_contact_entity = old_egy.publication_contact_entity
        new_egy.save()

    @staticmethod
    def _postpone_achievement(old_egy: EducationGroupYear, new_egy: EducationGroupYear):
        new_egy.educationgroupachievement_set.all().delete()

        for achievement in old_egy.educationgroupachievement_set.all():
            new_achievement = update_related_object(achievement, "education_group_year", new_egy)

            for detail in achievement.educationgroupdetailedachievement_set.all():
                update_related_object(detail, "education_group_achievement", new_achievement)

    @staticmethod
    def _postpone_admission(old_egy: EducationGroupYear, new_egy: EducationGroupYear):
        if hasattr(new_egy, "admissioncondition"):
            new_egy.admissioncondition.delete()

        if not hasattr(old_egy, "admissioncondition"):
            return

        new_admission = update_related_object(old_egy.admissioncondition, "education_group_year", new_egy)

        for line in old_egy.admissioncondition.admissionconditionline_set.all():
            update_related_object(line, "admission_condition", new_admission)
