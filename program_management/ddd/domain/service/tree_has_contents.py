from collections import Counter

from django.db.models import Count

from base.models.authorized_relationship import AuthorizedRelationship
from base.models.group_element_year import GroupElementYear
from education_group.models.group_year import GroupYear


def have_contents_which_are_not_mandatory(group_year: GroupYear):
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
            any(have_contents_which_are_not_mandatory(child.child_element.group_year) for child in children_qs)
    print(type(_have_content))
    return _have_content
