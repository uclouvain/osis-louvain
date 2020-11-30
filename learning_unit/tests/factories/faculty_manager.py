from osis_role.contrib.tests.factories import EntityRoleModelFactory


class FacultyManagerFactory(EntityRoleModelFactory):
    class Meta:
        model = 'learning_unit.FacultyManager'
        django_get_or_create = ('person', 'entity',)
