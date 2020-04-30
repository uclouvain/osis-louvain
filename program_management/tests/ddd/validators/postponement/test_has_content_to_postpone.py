##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.test import SimpleTestCase
from django.utils.translation import gettext as _

from program_management.ddd.validators.postponement._has_content_to_postpone import HasContentToPostponeValidator
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestHasContentToPostponeValidator(SimpleTestCase):

    def setUp(self):
        self.end_postponement_year = 2020

    def test_when_has_content_to_postpone(self):
        postpone_from = ProgramTreeFactory(root_node__year=self.end_postponement_year + 1)
        LinkFactory(parent=postpone_from.root_node)
        validator = HasContentToPostponeValidator(postpone_from)
        self.assertTrue(validator.is_valid())

    def test_when_no_content_to_postpone(self):
        postpone_from = ProgramTreeFactory(root_node__year=self.end_postponement_year + 1)
        validator = HasContentToPostponeValidator(postpone_from)
        self.assertFalse(validator.is_valid())
        expected_result = _("This training has no content to postpone.")
        self.assertListEqual([expected_result], validator.error_messages)
