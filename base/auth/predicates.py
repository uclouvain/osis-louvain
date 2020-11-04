from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from rules import predicate

from education_group.models.group_year import GroupYear
from osis_role.errors import predicate_failed_msg


@predicate(bind=True)
@predicate_failed_msg(message=_("The user is not linked to this training"))
def is_linked_to_offer(self, user: User, obj: GroupYear):
    if obj:
        return any(
            obj.educationgroupversion.offer.education_group_id in role.get_person_related_education_groups(role.person)
            for role in self.context['role_qs']
        )
    return None
