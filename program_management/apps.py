from django.apps import AppConfig


class ProgramManagementConfig(AppConfig):
    name = 'program_management'

    def ready(self):
        from . import signals
