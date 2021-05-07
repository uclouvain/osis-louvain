from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from rules import predicate

from base.models import session_exam_calendar
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


@predicate(bind=True)
@predicate_failed_msg(message=_("The period to edit scores responsibles is not opened yet"))
def is_scores_responsible_period_opened(self, user: User, obj: GroupYear):
    return bool(session_exam_calendar.current_sessions_academic_year())
