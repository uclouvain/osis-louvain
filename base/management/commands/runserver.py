##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.conf import settings
from django.contrib.staticfiles.management.commands.runserver import Command as StaticfilesRunserverCommand
from voluptuous import Schema, Required, Range, All, Length


class Command(StaticfilesRunserverCommand):
    def add_arguments(self, parser):
        parser.add_argument('--validate-settings',
                            action='store_false',
                            dest='validate_settings',
                            default=True,
                            help='Check if the settings file is in a right format')
        super(Command, self).add_arguments(parser)

    def handle(self, *args, **options):
        validate_settings = options.get('validate_settings')
        if validate_settings:
            self.check_settings()
        return super(Command, self).handle(*args, **options)

    def check_settings(self):
        is_queue_setting_valid()


def is_queue_setting_valid():
    if hasattr(settings, "QUEUES"):
        return Schema({
            Required("QUEUE_URL"): str,
            Required("QUEUE_USER"): str,
            Required("QUEUE_PASSWORD"): str,
            Required("QUEUE_PORT"): Range(min=1, max=65536, min_included=True, max_included=True),
            Required("QUEUE_CONTEXT_ROOT"): str,
            Required("QUEUES_NAME"): All({}, Length(min=1), extra=True)
        })(settings.QUEUES)
