from typing import Union

from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _, pgettext
from rules import predicate

from base.business.event_perms import EventPermEducationGroupEdition
from base.models.education_group_type import EducationGroupType
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_categories import Categories
from education_group.auth.scope import Scope
from education_group.models.group_year import GroupYear
from osis_role import errors
from osis_role.errors import predicate_failed_msg, set_permission_error, get_permission_error


@predicate(bind=True)
def are_all_trainings_removable(self, user, education_group_year):
    trainings = education_group_year.education_group.educationgroupyear_set.all()
    return _are_all_removable(self, user, trainings, 'base.delete_training')


@predicate(bind=True)
def are_all_minitrainings_removable(self, user, education_group_year):
    minitrainings = education_group_year.education_group.educationgroupyear_set.all()
    return _are_all_removable(self, user, minitrainings, 'base.delete_minitraining')


@predicate(bind=True)
def are_all_groups_removable(self, user, group_year):
    groups = group_year.group.groupyear_set.all()
    return _are_all_removable(self, user, groups, 'base.delete_group')


def _are_all_removable(self, user, objects, perm):
    # use shortcut break : at least one should not have perm to trigger error
    result = all(
        user.has_perm(perm, object)
        for object in objects.order_by('academic_year__year')
    )
    # transfers last perm error message
    message = get_permission_error(user, perm)
    set_permission_error(user, self.context['perm_name'], message)
    return result


@predicate(bind=True)
@predicate_failed_msg(
    message=pgettext("male", "The user does not have permission to create a %(category)s.") %
    {"category": Categories.GROUP.value}
)
def is_not_orphan_group(self, user, education_group_year=None):
    return education_group_year is not None


@predicate(bind=True)
@predicate_failed_msg(
    message=_("You cannot change/delete a education group existing before %(limit_year)s") %
    {"limit_year": settings.YEAR_LIMIT_EDG_MODIFICATION}
)
def is_education_group_year_older_or_equals_than_limit_settings_year(
        self,
        user: User,
        education_group_year: Union[EducationGroupYear, GroupYear] = None
):
    if education_group_year:
        return education_group_year.academic_year.year >= settings.YEAR_LIMIT_EDG_MODIFICATION
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("The user is not allowed to create/modify this type of education group"))
def is_education_group_type_authorized_according_to_user_scope(
        self,
        user: User,
        egy: Union[EducationGroupYear, GroupYear] = None
):
    if egy:
        return any(
            egy.education_group_type.name in role.get_allowed_education_group_types()
            for role in self.context['role_qs']
            if egy.management_entity_id in self.context['role_qs'].filter(pk=role.pk).get_entities_ids()
        )
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("The user is not attached to the management entity"))
def is_user_attached_to_management_entity(
        self,
        user: User,
        education_group_year: Union[EducationGroupYear, GroupYear] = None
):
    if education_group_year:
        user_entity_ids = self.context['role_qs'].get_entities_ids()
        return education_group_year.management_entity_id in user_entity_ids
    return education_group_year


@predicate(bind=True)
@predicate_failed_msg(message=EventPermEducationGroupEdition.error_msg)
def is_program_edition_period_open(self, user, education_group_year=None):
    return EventPermEducationGroupEdition(obj=education_group_year, raise_exception=False).is_open()


@predicate(bind=True)
def is_continuing_education_group_year(self, user, education_group_year=None):
    return education_group_year and education_group_year.is_continuing_education_education_group_year


@predicate(bind=True)
@predicate_failed_msg(message=_("The scope of the user is limited and prevents this action to be performed"))
def is_user_linked_to_all_scopes_of_management_entity(self, user, education_group_year):
    if education_group_year:
        user_scopes = {
            entity_id: scope for role in self.context['role_qs']
            for scope in role.scopes if hasattr(role, 'scopes')
            for entity_id in self.context['role_qs'].filter(pk=role.pk).get_entities_ids()
        }
        return user_scopes.get(education_group_year.management_entity_id) == Scope.ALL.value
    return None
