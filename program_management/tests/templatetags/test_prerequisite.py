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
from decimal import Decimal

from django.test import SimpleTestCase
from django.utils.translation import gettext as _

from base.models.enums import prerequisite_operator
from program_management.templatetags import prerequisite as prerequisite_tags
from program_management.ddd.domain import prerequisite as prerequisite_domain
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeLearningUnitYearFactory


class TestPrerequisiteHtmlDisplay(SimpleTestCase):
    def setUp(self):
        self.links = [
            LinkFactory(
                child=NodeLearningUnitYearFactory(code="OSIS1452", title="OSIS", year=2019, credits=Decimal(5)),
                relative_credits=3
            ),
            LinkFactory(
                child=NodeLearningUnitYearFactory(code="OSIS1358", title="DEV", year=2019, credits=Decimal(7)),
                relative_credits=1
            ),
            LinkFactory(
                child=NodeLearningUnitYearFactory(code="MERC1469", title="What", year=2019, credits=Decimal(8)),
                relative_credits=None
            ),
        ]

    def test_should_return_hyphen_when_no_prerequisite(self):
        result = prerequisite_tags.prerequisite_as_html(None, self.links)
        self.assertEqual(
            result,
            '-'
        )

    def test_when_one_prerequisite_should_return_it_as_href(self):
        prerequisite_items_group_obj = prerequisite_domain.PrerequisiteItemGroup(
            prerequisite_operator.OR,
            [prerequisite_domain.PrerequisiteItem("OSIS1452", 2019)]
        )
        prerequisite_obj = prerequisite_domain.Prerequisite(
            prerequisite_operator.AND,
            [prerequisite_items_group_obj]

        )

        result = prerequisite_tags.prerequisite_as_html(prerequisite_obj, self.links)
        self.assertEqual(
            result,
            "<a href='/learning_units/OSIS1452/2019' title='OSIS\n{cred_label} : 3 / 5'>OSIS1452</a>".format(
                cred_label=_('Cred. rel./abs.')
            )
        )

    def test_should_convert_all_prerequisite_items_as_href(self):
        prerequisite_items_group_obj_1 = prerequisite_domain.PrerequisiteItemGroup(
            prerequisite_operator.OR,
            [prerequisite_domain.PrerequisiteItem("OSIS1452", 2019)]
        )
        prerequisite_items_group_obj_2 = prerequisite_domain.PrerequisiteItemGroup(
            prerequisite_operator.OR,
            [prerequisite_domain.PrerequisiteItem("OSIS1358", 2019),
             prerequisite_domain.PrerequisiteItem("MERC1469", 2019)]
        )
        prerequisite_obj = prerequisite_domain.Prerequisite(
            prerequisite_operator.AND,
            [prerequisite_items_group_obj_1, prerequisite_items_group_obj_2]

        )

        result = prerequisite_tags.prerequisite_as_html(prerequisite_obj, self.links)
        self.assertEqual(
            result,
            "<a href='/learning_units/OSIS1452/2019' title='OSIS\n{cred_label} : 3 / 5'>OSIS1452</a> "
            "{main_operator} "
            "(<a href='/learning_units/OSIS1358/2019' title='DEV\n{cred_label} : 1 / 7'>OSIS1358</a> "
            "{secondary_operator} "
            "<a href='/learning_units/MERC1469/2019' title='What\n{cred_label} : - / 8'>MERC1469</a>)".format(
                main_operator=_(prerequisite_obj.main_operator),
                secondary_operator=_(prerequisite_items_group_obj_1.operator),
                cred_label=_('Cred. rel./abs.')
            )
        )

    def test_should_not_have_title_value_when_no_links_have_prerequisite_value_as_children(self):
        prerequisite_items_group_obj = prerequisite_domain.PrerequisiteItemGroup(
            prerequisite_operator.OR,
            [prerequisite_domain.PrerequisiteItem("OSIS5452", 2019)]
        )
        prerequisite_obj = prerequisite_domain.Prerequisite(
            prerequisite_operator.AND,
            [prerequisite_items_group_obj]

        )

        result = prerequisite_tags.prerequisite_as_html(prerequisite_obj, self.links)
        self.assertEqual(
            result,
            "<a href='/learning_units/OSIS5452/2019' title=''>OSIS5452</a>"
        )


class TestIsPrerequisiteAsHtml(SimpleTestCase):
    def setUp(self) -> None:
        self.links = [
            LinkFactory(
                child=NodeLearningUnitYearFactory(
                    code="OSIS1452", title="OSIS", year=2019, credits=Decimal(5), node_id=1
                ),
                relative_credits=3
            ),
            LinkFactory(
                child=NodeLearningUnitYearFactory(
                    code="OSIS1358", title="DEV", year=2019, credits=Decimal(7), node_id=2
                ),
                relative_credits=1
            ),
            LinkFactory(
                child=NodeLearningUnitYearFactory(
                    code="MERC1469", title="What", year=2019, credits=Decimal(8), node_id=3
                ),
                relative_credits=None
            ),
        ]

    def test_should_return_empty_rows_value_when_is_prerequisite_list_is_empty(self):
        result = prerequisite_tags.is_prerequisite_as_html([], [])
        self.assertEqual(
            result,
            {"is_prerequisite_rows": []}
        )

    def test_when_is_prerequisite_of_one_luy_should_return_a_table_row(self):
        is_prerequisite_list = [
            NodeLearningUnitYearFactory(code="OSIS1452", title="OSIS", year=2019, credits=Decimal(5), node_id=1)
        ]
        result = prerequisite_tags.is_prerequisite_as_html(is_prerequisite_list, self.links)
        rows = [
            ("OSIS1452", "2019", "OSIS", "3", "5")
        ]
        self.assertEqual(
            result,
            {"is_prerequisite_rows": rows}
        )

    def test_should_return_as_many_rows_as_there_is_element_in_is_prerequisite_list_sorted_by_code(self):
        is_prerequisite_list = [
            NodeLearningUnitYearFactory(code="OSIS1452", title="OSIS", year=2019, credits=Decimal(5), node_id=1),
            NodeLearningUnitYearFactory(code="OSIS1358", title="DEV", year=2019, credits=Decimal(7), node_id=2),
            NodeLearningUnitYearFactory(code="MERC1469", title="What", year=2019, credits=Decimal(8), node_id=3)
        ]
        result = prerequisite_tags.is_prerequisite_as_html(is_prerequisite_list, self.links)
        rows = [
            prerequisite_tags.IsPrerequisiteRow("OSIS1452", "2019", "OSIS", "3", "5"),
            prerequisite_tags.IsPrerequisiteRow("OSIS1358", "2019", "DEV", "1", "7"),
            prerequisite_tags.IsPrerequisiteRow("MERC1469", "2019", "What", "-", "8"),

        ]
        self.assertEqual(
            result,
            {"is_prerequisite_rows": rows}
        )
