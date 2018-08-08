##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest.mock import patch

from django.core.validators import _lazy_re_compile
from django.test import TestCase

from base.forms.education_group.group import GroupModelForm, GroupForm
from base.models.education_group_type import EducationGroupType
from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_categories
from base.models.group_element_year import GroupElementYear
from base.models.validation_rule import ValidationRule
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import GroupFactory
from base.tests.forms.education_group.test_common import EducationGroupYearModelFormMixin, _get_valid_post_data


class TestGroupModelFormModelForm(EducationGroupYearModelFormMixin):

    def setUp(self):
        self.education_group_type = EducationGroupTypeFactory(category=education_group_categories.GROUP)
        self.form_class = GroupModelForm
        super(TestGroupModelFormModelForm, self).setUp(education_group_type=self.education_group_type)

    def test_fields(self):
        fields = ("acronym", "partial_acronym", "education_group_type", "title", "title_english", "credits",
                  "main_teaching_campus", "academic_year", "remark", "remark_english", "min_credits", "max_credits",
                  "management_entity")
        self._test_fields(self.form_class, fields)

    def test_init_academic_year_field(self):
        self._test_init_and_disable_academic_year_field(self.form_class)

    def test_init_education_group_type_field(self):
        self._test_init_education_group_type_field(self.form_class, education_group_categories.GROUP)

    def test_preselect_entity_version_from_entity_value(self):
        self._test_preselect_entity_version_from_entity_value(self.form_class)

    def test_create_with_validation_rule(self):
        ValidationRule.objects.create(
            field_reference=(EducationGroupYear._meta.db_table + ".acronym." + self.education_group_type.name),
            initial_value="yolo",
            required_field=False,
            regex_rule="([A-Z]{2})(.*)"
        )

        form = GroupModelForm(initial={
            "education_group_type": self.education_group_type
        })

        self.assertEqual(form.fields["acronym"].initial, "yolo")
        self.assertEqual(form.fields["acronym"].required, False)
        self.assertEqual(form.fields["acronym"].validators[1].regex, _lazy_re_compile("([A-Z]{2})(.*)"))




class TestGroupForm(TestCase):
    def setUp(self):
        self.category = education_group_categories.GROUP
        self.expected_educ_group_year, self.post_data = _get_valid_post_data(self.category)

    def test_create(self):
        form = GroupForm(data=self.post_data, parent=None)

        self.assertTrue(form.is_valid(), form.errors)

        education_group_year = form.save()

        self.assertEqual(education_group_year.education_group.start_year,
                         self.expected_educ_group_year.academic_year.year)
        self.assertIsNone(education_group_year.education_group.end_year)

    @patch('base.models.education_group_type.find_authorized_types', return_value=EducationGroupType.objects.all())
    def test_create_with_parent(self, mock_find_authorized_types):
        parent = GroupFactory()
        form = GroupForm(data=self.post_data, parent=parent)

        self.assertTrue(form.is_valid(), form.errors)

        education_group_year = form.save()

        self.assertTrue(GroupElementYear.objects.get(child_branch=education_group_year, parent=parent))

