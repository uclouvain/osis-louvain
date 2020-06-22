from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from base.business.education_groups import general_information
from base.business.education_groups.general_information import PublishException
from base.models.enums.education_group_categories import Categories
from base.views.common import display_error_messages, display_success_messages
from education_group.models.group_year import GroupYear


@login_required
@require_http_methods(['POST'])
def publish(request, year, code):
    group_year = get_object_or_404(GroupYear, partial_acronym=code, academic_year__year=year)

    try:
        general_information.publish(group_year)
        message = _("The program %(acronym)s will be published soon") % {'acronym': group_year.acronym}
        display_success_messages(request, message, extra_tags='safe')
    except PublishException as e:
        display_error_messages(request, str(e))

    url_name = __get_redirect_view_name(group_year.education_group_type.category)
    default_redirect_view = reverse(url_name, kwargs={'year': year, 'code': code})

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', default_redirect_view))


def __get_redirect_view_name(category: str):
    if category == Categories.GROUP.name:
        url_name = 'group_general_information'
    elif category == Categories.MINI_TRAINING.name:
        url_name = 'mini_training_general_information'
    else:
        url_name = 'training_general_information'
    return url_name
