from education_group.auth.scope import Scope


class EducationGroupTypeScopeRoleMixin:
    """
    This mixin allow a role to be scoped by application which is an grouping of allowed education group types
    """
    def get_allowed_education_group_types(self):
        allowed_education_group_types = []
        for scope in self.scopes:
            allowed_education_group_types += Scope.get_education_group_types(scope)
        return allowed_education_group_types
