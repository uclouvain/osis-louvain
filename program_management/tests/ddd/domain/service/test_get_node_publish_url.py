# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from base.models.enums.education_group_types import MiniTrainingType, TrainingType
from program_management.ddd.domain.service.get_node_publish_url import GetNodePublishUrl
from program_management.tests.ddd.factories.node import NodeGroupYearFactory


@override_settings(
    ESB_API_URL="api.esb.com",
    ESB_REFRESH_PEDAGOGY_ENDPOINT="offer/{year}/{code}/refresh",
)
class TestGetNodePublishUrl(SimpleTestCase):
    def setUp(self) -> None:
        self.minor = NodeGroupYearFactory(node_type=MiniTrainingType.ACCESS_MINOR)
        self.deepening = NodeGroupYearFactory(node_type=MiniTrainingType.DEEPENING)
        self.major = NodeGroupYearFactory(node_type=MiniTrainingType.FSA_SPECIALITY)
        self.training = NodeGroupYearFactory(node_type=TrainingType.PGRM_MASTER_120)

    @override_settings(ESB_REFRESH_PEDAGOGY_ENDPOINT=None)
    def test_publish_case_missing_settings(self):
        with self.assertRaises(ImproperlyConfigured):
            GetNodePublishUrl.get_url_from_node(self.minor)

    def test_assert_training_publish_url(self):
        code = self.training.title
        expected_publish_url = "api.esb.com/offer/{year}/{code}/refresh".format(year=self.training.year, code=code)

        self.assertEqual(
            GetNodePublishUrl.get_url_from_node(self.training),
            expected_publish_url
        )
