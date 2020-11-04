from education_group.auth.scope import Scope
from osis_role.contrib.tests.factories import EntityRoleModelFactory


class FacultyManagerFactory(EntityRoleModelFactory):
    class Meta:
        model = 'education_group.FacultyManager'
        django_get_or_create = ('person', 'entity',)

    scopes = [Scope.ALL.name]
