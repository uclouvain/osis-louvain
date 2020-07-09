from django.contrib.auth.views import redirect_to_login
from rules.contrib.views import PermissionRequiredMixin as PermissionRequiredMixinRules, \
    objectgetter as objectgetterrules, \
    permission_required as permission_requiredrules

# Wraps django-rules
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
