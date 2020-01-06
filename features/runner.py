# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
import collections

from behave_django.environment import BehaveHooksMixin
from behave_django.runner import BehaviorDrivenTestRunner
from behave_django.testcase import ExistingDatabaseTestCase, BehaviorDrivenTestCase
from django.conf import settings
from django.db import connections, DEFAULT_DB_ALIAS, connection
from django.test.runner import DiscoverRunner
from django.test.utils import dependency_ordered


class OsisTestCase(BehaviorDrivenTestCase):
    def _fixture_teardown(self):
        pass

    def _flush_db(self):
        super()._fixture_teardown()


class OsisRunner(BehaviorDrivenTestRunner):
    testcase_class = OsisTestCase

    def teardown_databases(self, old_config, **kwargs):

        return super().teardown_databases(old_config, **kwargs)
