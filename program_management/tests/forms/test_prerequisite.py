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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import mock
from django.test import SimpleTestCase

from program_management.forms.prerequisite import PrerequisiteForm
from program_management.tests.ddd.factories.node import NodeLearningUnitYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestPrerequisiteForm(SimpleTestCase):
    @mock.patch("program_management.forms.prerequisite.UpdatePrerequisiteValidatorList")
    def test_is_valid_call_prerequisite_validators(self, mock_prerequisite_validator):
        prerequisite_string = "LOSIS1452 OU LPORT5896"
        program_tree = ProgramTreeFactory(),
        node = NodeLearningUnitYearFactory()

        form = PrerequisiteForm(
            program_tree,
            node,
            data={"prerequisite_string": prerequisite_string}
        )
        form.is_valid()
        self.assertTrue(mock_prerequisite_validator.called)
