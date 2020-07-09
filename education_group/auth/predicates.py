from django.conf import settings
from rules import predicate

from base.business.event_perms import EventPermEducationGroupEdition
from base.models.education_group_type import EducationGroupType
from base.models.enums.education_group_categories import Categories
from osis_role import errors
from osis_role.errors import predicate_failed_msg
from django.utils.translation import gettext_lazy as _, pgettext


@predicate(bind=True)
def are_all_education_group_years_removable(self, user, education_group):
    education_group_years = education_group.educationgroupyear_set.all()
    return all(
        user.has_perm('base.delete_educationgroup', education_group_year)
        for education_group_year in education_group_years
    )


@predicate(bind=True)
@predicate_failed_msg(
    message=pgettext("male", "The user does not have permission to create a %(category)s.") %
    {"category": Categories.GROUP.value}
)
def is_not_orphan_group(self, user, education_group_year=None):
    return education_group_year is not None


@predicate(bind=True)
@predicate_failed_msg(
    message=_("You cannot change a education group before %(limit_year)s") %
    {"limit_year": settings.YEAR_LIMIT_EDG_MODIFICATION}
)
def is_education_group_year_older_or_equals_than_limit_settings_year(self, user, education_group_year=None):
    if education_group_year:
        return education_group_year.academic_year.year >= settings.YEAR_LIMIT_EDG_MODIFICATION
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("The user is not allowed to create/modify this type of education group"))
def is_education_group_type_authorized_according_to_user_scope(self, user, education_group_year=None):
    if education_group_year:
        return any(
            education_group_year.education_group_type.name in role_row.get_allowed_education_group_types()
            for role_row in self.context['role_qs']
        )
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("The user is not attached to the management entity"))
def is_user_attached_to_management_entity(self, user, education_group_year=None):
    if education_group_year:
        user_entity_ids = self.context['role_qs'].get_entities_ids()
        return education_group_year.management_entity_id in user_entity_ids
    return education_group_year


@predicate(bind=True)
@predicate_failed_msg(message=EventPermEducationGroupEdition.error_msg)
def is_program_edition_period_open(self, user, education_group_year=None):
    return EventPermEducationGroupEdition(obj=education_group_year, raise_exception=False).is_open()


@predicate(bind=True)
def is_maximum_child_not_reached_for_group_category(self, user, education_group_year=None):
    if education_group_year:
        return _is_maximum_child_not_reached_for_category(self, user, education_group_year, Categories.GROUP.name)
    return None


@predicate(bind=True)
def is_maximum_child_not_reached_for_training_category(self, user, education_group_year=None):
    if education_group_year:
        return _is_maximum_child_not_reached_for_category(self, user, education_group_year, Categories.TRAINING.name)
    return None


@predicate(bind=True)
def is_maximum_child_not_reached_for_mini_training_category(self, user, education_group_year=None):
    if education_group_year:
        return _is_maximum_child_not_reached_for_category(self, user, education_group_year,
                                                          Categories.MINI_TRAINING.name)
    return None


def _is_maximum_child_not_reached_for_category(self, user, education_group_year, category):
    result = EducationGroupType.objects.filter(
        category=category,
        authorized_child_type__parent_type__educationgroupyear=education_group_year
    ).exists()

    if not result:
        message = pgettext(
            "female" if education_group_year.education_group_type.category in [
                Categories.TRAINING,
                Categories.MINI_TRAINING
            ] else "male",
            "No type of %(child_category)s can be created as child of %(category)s of type %(type)s"
        ) % {
            "child_category": Categories[category].name,
            "category": education_group_year.education_group_type.get_category_display(),
            "type": education_group_year.education_group_type.get_name_display(),
        }
        errors.set_permission_error(user, self.context['perm_name'], message)
    return result
