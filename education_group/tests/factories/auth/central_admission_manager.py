from osis_role.contrib.tests.factories import RoleModelFactory


class CentralAdmissionManagerFactory(RoleModelFactory):
    class Meta:
        model = 'education_group.CentralAdmissionManager'
        django_get_or_create = ('person',)
