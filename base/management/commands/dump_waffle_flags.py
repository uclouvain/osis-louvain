#!/usr/bin/env python
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        call_command(
            'dumpdata',
            "waffle.flag",
            indent=4,
            use_natural_foreign_keys=True,
            use_natural_primary_keys=True,
            output='base/fixtures/waffle_flags.json'
        )
