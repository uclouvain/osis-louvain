from rules.contrib.views import PermissionRequiredMixin as PermissionRequiredMixinRules, \
    objectgetter as objectgetterrules, \
    permission_required as permission_requiredrules

# Wraps django-rules
PermissionRequiredMixin = PermissionRequiredMixinRules
objectgetter = objectgetterrules
permission_required = permission_requiredrules
