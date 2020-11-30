from osis_role.contrib.tests.factories import EntityRoleModelFactory


class CentralManagerFactory(EntityRoleModelFactory):
    class Meta:
        model = 'learning_unit.CentralManager'
        django_get_or_create = ('person', 'entity',)
