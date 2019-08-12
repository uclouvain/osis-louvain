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
from collections import Counter

from django.db.models import Count
from django.utils.translation import ngettext_lazy, gettext_lazy as _

from base.models.authorized_relationship import AuthorizedRelationship
from base.models.education_group_year import EducationGroupYear
from base.models.group_element_year import GroupElementYear
from base.models.offer_enrollment import OfferEnrollment


def start(education_group_year):
    """
    This function will delete education group year and the default structure
    """
    child_links_to_delete = GroupElementYear.objects.filter(
        parent=education_group_year,
        child_branch__education_group_type__in=AuthorizedRelationship.objects.filter(
            parent_type=education_group_year.education_group_type,
            min_count_authorized=1
        ).values('child_type')
    )

    for child_link in child_links_to_delete:
        # Remove link between parent/child
        child_link.delete()
        start(child_link.child_branch)

    if not GroupElementYear.objects.filter(child_branch=education_group_year).exists():
        # No reuse
        education_group_year.delete()


def get_protected_messages_by_education_group_year(education_group_year):
    protected_message = []

    # Count the number of enrollment
    count_enrollment = OfferEnrollment.objects.filter(education_group_year=education_group_year).count()
    if count_enrollment:
        protected_message.append(
            ngettext_lazy(
                "%(count_enrollment)d student is enrolled in the offer.",
                "%(count_enrollment)d students are enrolled in the offer.",
                count_enrollment
            ) % {"count_enrollment": count_enrollment}
        )

    # Check if content is not empty
    if _have_contents_which_are_not_mandatory(education_group_year):
        protected_message.append(_("The content of the education group is not empty."))

    if education_group_year.linked_with_epc:
        protected_message.append(_("Linked with EPC"))

    return protected_message


def get_education_group_years_to_delete(education_group, end_year=None):
    qs = EducationGroupYear.objects.filter(education_group=education_group)
    if end_year is not None:
        qs = qs.filter(academic_year__year__gt=end_year)
    return qs.order_by('academic_year__year')


def _have_contents_which_are_not_mandatory(education_group_year):
    """
    An education group year is empty if:
        - it has no children
        - all of his children are mandatory groups and they are empty [=> Min 1]
    """
    mandatory_groups = AuthorizedRelationship.objects.filter(
        parent_type=education_group_year.education_group_type,
        min_count_authorized=1
    ).values_list('child_type', 'min_count_authorized')

    children_count = GroupElementYear.objects \
        .filter(parent=education_group_year) \
        .values('child_branch__education_group_type') \
        .annotate(count=Count('child_branch__education_group_type')) \
        .values_list('child_branch__education_group_type', 'count')

    _have_content = bool(Counter(children_count) - Counter(mandatory_groups))
    if not _have_content:
        children_qs = GroupElementYear.objects.filter(parent=education_group_year)
        _have_content = any(_have_contents_which_are_not_mandatory(child.child_branch) for child in children_qs)
    return _have_content
