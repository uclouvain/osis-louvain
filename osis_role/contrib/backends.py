from django.contrib.auth.backends import RemoteUserBackend as DjangoRemoteUserBackend

from osis_role.contrib.permissions import ObjectPermissionBackend


class RemoteUserBackend(ObjectPermissionBackend, DjangoRemoteUserBackend):
    pass
