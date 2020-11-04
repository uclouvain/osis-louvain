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
from django.utils.translation import gettext_lazy as _
from django.test.utils import override_settings
from base.models.enums.prerequisite_operator import AND, OR

from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeLearningUnitYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory

from program_management.tests.ddd.factories.prerequisite import PrerequisiteFactory, PrerequisiteItemGroupFactory, \
    PrerequisiteItemFactory
from program_management.tests.ddd.factories.prerequisite import cast_to_prerequisite
from program_management.business.excel import _build_excel_lines
from program_management.business.excel import HeaderLine, OfficialTextLine, LearningUnitYearLine, PrerequisiteItemLine


class TestGeneratePrerequisitesWorkbook(SimpleTestCase):

    def setUp(self):
        self.program_tree = ProgramTreeFactory()
        yr = 2019

        self.links = [
            LinkFactory(parent=self.program_tree.root_node, child=NodeLearningUnitYearFactory(code=code, year=yr)) for code in ['LOSIS1121', 'MARC2547', 'MECK8960', 'BREM5890', 'MARC2548', 'MECK8968', 'BREM5898']
        ]

        self.children = [link.child for link in self.links]
        self.luy_children = list(self.children)

        node_that_is_prerequisite = self.children[1]
        self.children[0].set_prerequisite(cast_to_prerequisite(node_that_is_prerequisite))

        item3 = PrerequisiteItemFactory(code=self.children[3].code, year=self.children[3].year)
        item4 = PrerequisiteItemFactory(code=self.children[4].code, year=self.children[4].year)
        item5 = PrerequisiteItemFactory(code=self.children[5].code, year=self.children[5].year)
        prerequisite = PrerequisiteFactory(
            prerequisite_item_groups=[
                PrerequisiteItemGroupFactory(
                    prerequisite_items=[item3]
                ),
                PrerequisiteItemGroupFactory(
                    prerequisite_items=[item4, item5]
                ),
            ]
        )

        self.children[2].set_prerequisite(prerequisite)

    def test_header_lines(self):
        expected_first_line = HeaderLine(egy_acronym=self.program_tree.root_node.title,
                                         egy_title=self.program_tree.root_node.group_title_fr,
                                         code_header=_('Code'),
                                         title_header=_('Title'),
                                         credits_header=_('Cred. rel./abs.'),
                                         block_header=_('Block'),
                                         mandatory_header=_('Mandatory')
                                         )
        expected_second_line = OfficialTextLine(text=_("Official"))

        headers = _build_excel_lines(self.program_tree)
        self.assertEqual(expected_first_line, headers[0])
        self.assertEqual(expected_second_line, headers[1])

    @override_settings(LANGUAGES=[('en', 'English'), ], LANGUAGE_CODE='en')
    def test_when_learning_unit_year_has_one_prerequisite(self):
        content = _build_excel_lines(self.program_tree)
        learning_unit_year_line = content[2]
        prerequisite_item_line = content[3]

        expected_learning_unit_year_line = LearningUnitYearLine(luy_acronym=self.luy_children[0].code,
                                                                luy_title=self.luy_children[0].full_title_en)
        expected_prerequisite_item_line = PrerequisiteItemLine(text='{} :'.format(_('has as prerequisite')),
                                                               operator=None,
                                                               luy_acronym=self.luy_children[1].code,
                                                               luy_title=self.luy_children[1].title,
                                                               credits=self.links[1].relative_credits_repr,
                                                               block=str(self.links[1].block) if self.links[1].block else '',
                                                               mandatory=_("Yes") if self.links[1].is_mandatory else _("No")
                                                               )
        self.assertEqual(expected_learning_unit_year_line, learning_unit_year_line)
        self.assertEqual(expected_prerequisite_item_line, prerequisite_item_line)

    @override_settings(LANGUAGES=[('en', 'English'), ], LANGUAGE_CODE='en')
    def test_when_learning_unit_year_has_multiple_prerequisites(self):
        content = _build_excel_lines(self.program_tree)

        prerequisite_item_line_1 = content[5]
        expected_prerequisite_item_line1 = PrerequisiteItemLine(
            text='{} :'.format(_('has as prerequisite')),
            operator=None,
            luy_acronym=self.luy_children[3].code,
            luy_title=self.luy_children[3].title,
            credits=self.links[3].relative_credits_repr,
            block=str(self.links[3].block) if self.links[3].block else '',
            mandatory=_("Yes") if self.links[3].is_mandatory else _("No")
        )
        self.assertEqual(prerequisite_item_line_1, expected_prerequisite_item_line1)

        prerequisite_item_line_2 = content[6]
        expected_prerequisite_item_line2 = PrerequisiteItemLine(
            text=None,
            operator=_(AND),
            luy_acronym="({}".format(self.luy_children[4].code),
            luy_title=self.luy_children[4].title,
            credits=self.links[4].relative_credits_repr,
            block=str(self.links[4].block) if self.links[4].block else '',
            mandatory=_("Yes") if self.links[4].is_mandatory else _("No")
        )
        self.assertEqual(prerequisite_item_line_2, expected_prerequisite_item_line2)

        prerequisite_item_line_3 = content[7]
        expected_prerequisite_item_line3 = PrerequisiteItemLine(
            text=None,
            operator=_(OR),
            luy_acronym="{})".format(self.luy_children[5].code),
            luy_title=self.luy_children[5].title,
            credits=self.links[5].relative_credits_repr,
            block=str(self.links[5].block) if self.links[5].block else '',
            mandatory=_("Yes") if self.links[5].is_mandatory else _("No")
        )
        self.assertEqual(prerequisite_item_line_3, expected_prerequisite_item_line3)
