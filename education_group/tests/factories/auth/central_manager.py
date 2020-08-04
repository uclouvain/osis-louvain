from education_group.auth.scope import Scope
from osis_role.contrib.tests.factories import EntityModelFactory


class CentralManagerFactory(EntityModelFactory):
    class Meta:
        model = 'education_group.CentralManager'
        django_get_or_create = ('person', 'entity',)

    scopes = [Scope.ALL.name]
