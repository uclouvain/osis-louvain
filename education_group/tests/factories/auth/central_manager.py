from education_group.auth.scope import Scope
from osis_role.contrib.tests.factories import EntityRoleModelFactory


class CentralManagerFactory(EntityRoleModelFactory):
    class Meta:
        model = 'education_group.CentralManager'
        django_get_or_create = ('person', 'entity',)

    scopes = [Scope.ALL.name]
