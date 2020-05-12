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

from django.test import SimpleTestCase
from django.utils.translation import gettext_lazy as _
from mock import patch

from base.models.enums.education_group_types import TrainingType
from base.templatetags import education_group_pdf
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeLearningUnitYearFactory, NodeEducationGroupYearFactory


class TestGetVerboseLink(SimpleTestCase):

    def test_when_child_link_is_group(self):
        link = LinkFactory(
            child=NodeEducationGroupYearFactory(
                credits=5,
                offer_title_fr='Offer title',
                offer_title_en='Offer title',
                node_type=TrainingType.BACHELOR
            ),
            relative_credits=6,
        )

        expected_result = "Offer title (6 {})".format(_('credits'))
        self.assertEqual(expected_result, education_group_pdf.get_verbose_link(link))

    @patch('base.templatetags.education_group_pdf.get_verbose_title_ue', return_value="Title learning unit")
    @patch('base.templatetags.education_group_pdf.get_volume_total_verbose', return_value="15 + 20")
    def test_when_child_link_is_learning_unit(self, *mocks):
        link = LinkFactory(
            child=NodeLearningUnitYearFactory(
                code='LDROI1001',
                credits=4,
            ),
            relative_credits=6,
        )

        expected_result = "LDROI1001 Title learning unit [15 + 20] (6 {})".format(_('credits'))
        self.assertEqual(expected_result, education_group_pdf.get_verbose_link(link))
