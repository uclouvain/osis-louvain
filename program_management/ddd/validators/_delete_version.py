# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List

from django.utils.translation import ngettext_lazy
from django.utils.translation import gettext_lazy as _
from base.ddd.utils import business_validator
from program_management.ddd.business_types import *
from program_management.ddd.domain.service.offer_enrollments_count import enrollments_count_by_offer
from program_management.models.education_group_version import EducationGroupVersion


class EmptyTreeValidator(business_validator.BusinessValidator):

    def __init__(self, tree: 'ProgramTreeVersion'):
        super(EmptyTreeValidator, self).__init__()
        self.tree_to_delete = tree

    def validate(self):
        validate = self.tree_to_delete.get_tree().is_empty()
        if not validate:
            self.add_error_message(_('The content of the education group is not empty.'))
            return False
        return True


class NoEnrollmentValidator(business_validator.BusinessValidator):

    def __init__(self, education_group_versions: List[EducationGroupVersion]):
        super(NoEnrollmentValidator, self).__init__()

        self.education_group_versions = education_group_versions

    def validate(self):
        """This function will return all protected message ordered by year"""
        protected_messages = []
        for education_group_version in self.education_group_versions:
            education_group_year = education_group_version.offer
            protected_message = get_protected_messages_by_education_group_year(education_group_version)
            if protected_message:
                protected_messages.append({
                    'education_group_year': education_group_year,
                    'messages': protected_message
                })
        if protected_messages:
            for p in protected_messages:
                self.add_error_message(p)
            # raise interface.BusinessException(_("Cannot perform delete action on this version."))
            return False
        return True


def get_protected_messages_by_education_group_year(education_group_version: EducationGroupVersion) -> List:
    protected_message = []

    # Count the number of enrollment
    count_enrollment = enrollments_count_by_offer(education_group_version.offer)
    if count_enrollment:
        protected_message.append(
            ngettext_lazy(
                "%(count_enrollment)d student is enrolled in the offer.",
                "%(count_enrollment)d students are enrolled in the offer.",
                count_enrollment
            ) % {"count_enrollment": count_enrollment}
        )

    return protected_message
