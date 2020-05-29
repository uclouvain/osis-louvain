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
from collections import Counter
from typing import List

from django.db.models import Count
from django.utils.translation import gettext as _
from django.utils.translation import ngettext_lazy, gettext_lazy as _

from base.ddd.utils import business_validator
from base.models.authorized_relationship import AuthorizedRelationship
from base.models.education_group_year import EducationGroupYear
from base.models.group_element_year import GroupElementYear
from base.models.offer_enrollment import OfferEnrollment
from education_group.models.group_year import GroupYear
from program_management.models.education_group_version import EducationGroupVersion


class DeleteVersionValidator(business_validator.BusinessValidator):

    def __init__(self, education_group_versions: List[EducationGroupVersion]):
        super(DeleteVersionValidator, self).__init__()

        self.education_group_versions = education_group_versions

    def validate(self):
        """This function will return all protected message ordered by year"""
        protected_messages = []
        for education_group_version in self.education_group_versions:
            education_group_year = education_group_version.offer
            protected_message = get_protected_messages_by_education_group_year(education_group_year,
                                                                               education_group_version)
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


def get_protected_messages_by_education_group_year(education_group_year: EducationGroupYear,
                                                   education_group_version: EducationGroupVersion) -> List:
    protected_message = []

    # Count the number of enrollment
    count_enrollment = OfferEnrollment.objects.filter(education_group_year=education_group_version.offer).count()

    if count_enrollment:
        protected_message.append(
            ngettext_lazy(
                "%(count_enrollment)d student is enrolled in the offer.",
                "%(count_enrollment)d students are enrolled in the offer.",
                count_enrollment
            ) % {"count_enrollment": count_enrollment}
        )

    # Check if content is not empty
    if _have_contents_which_are_not_mandatory(education_group_version.root_group):
        protected_message.append(_("The content of the education group is not empty."))

    if education_group_year.linked_with_epc:
        protected_message.append(_("Linked with EPC"))

    return protected_message


def _have_contents_which_are_not_mandatory(group_year: GroupYear):
    """
    An education group year is empty if:
        - it has no children
        - all of his children are mandatory groups and they are empty [=> Min 1]
    """
    mandatory_groups = AuthorizedRelationship.objects.filter(
        parent_type=group_year.education_group_type,
        min_count_authorized=1
    ).values_list('child_type', 'min_count_authorized')

    children_count = GroupElementYear.objects \
        .filter(parent_element__group_year=group_year) \
        .values('child_element__group_year__education_group_type') \
        .annotate(count=Count('child_element__group_year__education_group_type')) \
        .values_list('child_element__group_year__education_group_type', 'count')

    _have_content = bool(Counter(children_count) - Counter(mandatory_groups))
    if not _have_content:
        children_qs = GroupElementYear.objects.filter(parent_element__group_year=group_year)
        _have_content = \
            any(_have_contents_which_are_not_mandatory(child.child_element.group_year) for child in children_qs)
    return _have_content
