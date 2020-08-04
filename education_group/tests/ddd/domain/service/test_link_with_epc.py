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
import mock
from django.test import SimpleTestCase

from education_group.ddd.domain.service.link_with_epc import LinkWithEPC
from education_group.ddd.domain.training import TrainingIdentity


class TestLinkWithEPC(SimpleTestCase):
    @mock.patch('education_group.ddd.domain.service.link_with_epc.education_group_year.have_link_with_epc')
    def test_assert_qs_exist_called_when_training(self, mock_have_link):
        training_id = TrainingIdentity(acronym="DROI2M", year=2000)
        LinkWithEPC().is_training_have_link_with_epc(training_id)

        self.assertTrue(mock_have_link.called)

    # @mock.patch('education_group.ddd.domain.service.link_with_epc.education_group_year.have_link_with_epc')
    # def test_assert_qs_exist_called_when_mini_training(self, mock_have_link):
    #     mini_training_id = MiniTrainingIdentity(acronym="OPT200M", year=2000)
    #     LinkWithEPC().mini_training_have_link_with_epc(mini_training_id)
    #
    #     self.assertTrue(mock_have_link.called)
