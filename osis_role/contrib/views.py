from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.utils.decorators import method_decorator
from rules.contrib.views import PermissionRequiredMixin as PermissionRequiredMixinRules, \
    objectgetter as objectgetterrules, \
    permission_required as permission_requiredrules

# Wraps django-rules
from osis_role.errors import get_permission_error

objectgetter = objectgetterrules
permission_required = permission_requiredrules


class PermissionRequiredMixin(PermissionRequiredMixinRules):
    def handle_no_permission(self):
        """
        Override default django behaviour, if user is not authenticated, redirect to login page
        """
        if not self.request.user.is_authenticated:
            return redirect_to_login(self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())
        super().handle_no_permission()


class AjaxPermissionRequiredMixin(PermissionRequiredMixinRules):

    permission_required = None

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            error_msg = get_permission_error(request.user, self.permission_required)
            if request.is_ajax():
                return render(request, 'education_group/blocks/modal/modal_access_denied.html', {
                    'access_message': error_msg
                })
            else:
                raise PermissionDenied(error_msg)
        return super().dispatch(request, *args, **kwargs)
