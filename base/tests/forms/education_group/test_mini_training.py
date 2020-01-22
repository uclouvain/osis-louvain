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
import datetime
from unittest.mock import patch

from base.forms.education_group.mini_training import MiniTrainingYearModelForm
from base.models.education_group_type import EducationGroupType
from base.models.enums import education_group_categories
from base.tests.factories.academic_calendar import AcademicCalendarEducationGroupEditionFactory
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.forms.education_group.test_common import EducationGroupYearModelFormMixin
from rules_management.enums import MINI_TRAINING_DAILY_MANAGEMENT, MINI_TRAINING_PGRM_ENCODING_PERIOD


class TestMiniTrainingModelForm(EducationGroupYearModelFormMixin):
    @classmethod
    def setUpTestData(cls):
        cls.education_group_type = EducationGroupTypeFactory(
            category=education_group_categories.MINI_TRAINING
        )
        cls.form_class = MiniTrainingYearModelForm
        AuthorizedRelationshipFactory(child_type=cls.education_group_type)

        super(TestMiniTrainingModelForm, cls).setUpTestData(education_group_type=cls.education_group_type)

    def test_fields(self):
        fields = (
            "acronym", "partial_acronym", "education_group_type",
            "title", "title_english", "credits", "active",
            "main_teaching_campus", "academic_year", "remark",
            "remark_english", "min_constraint", "max_constraint", "constraint_type",
            "schedule_type", "management_entity", "keywords"
        )
        self._test_fields(self.form_class, fields)

    def test_init_academic_year_field(self):
        self._test_init_and_disable_academic_year_field(self.form_class)

    def test_init_education_group_type_field(self):
        self._test_init_education_group_type_field(self.form_class, education_group_categories.MINI_TRAINING)

    def test_preselect_entity_version_from_entity_value(self):
        self._test_preselect_entity_version_from_entity_value(self.form_class)

    @patch('base.forms.education_group.common.find_authorized_types')
    def test_get_context_for_field_references_case_not_in_editing_pgrm_period(self, mock_authorized_types):
        mock_authorized_types.return_value = EducationGroupType.objects.all()
        context = self.form_class(
            parent=self.parent_education_group_year,
            education_group_type=self.education_group_type,
            user=self.user,
        ).get_context()
        self.assertTrue(context, MINI_TRAINING_DAILY_MANAGEMENT)

    @patch('base.forms.education_group.common.find_authorized_types')
    def test_get_context_for_field_references_case_in_editing_pgrm_period(self, mock_authorized_types):
        mock_authorized_types.return_value = EducationGroupType.objects.all()
        # Create an academic calendar for event EDUCATION_GROUP_EDITION
        AcademicCalendarEducationGroupEditionFactory(
            start_date=datetime.date.today() - datetime.timedelta(days=5),
            end_date=datetime.date.today() + datetime.timedelta(days=30),
        )
        context = self.form_class(
            parent=self.parent_education_group_year,
            education_group_type=self.education_group_type,
            user=self.user,
        ).get_context()
        self.assertTrue(context, MINI_TRAINING_PGRM_ENCODING_PERIOD)

    def test_preselect_management_entity_from_parent(self):
        self._test_preselect_management_entity_from_parent(self.form_class)

    @patch('base.forms.education_group.common.find_authorized_types')
    def test_no_preselect_management_entity_from_training_parent_case_no_parent(self, mock_authorized_types):
        mock_authorized_types.return_value = EducationGroupType.objects.all()
        form = MiniTrainingYearModelForm(
            parent=None,
            education_group_type=self.education_group_type,
            user=self.user
        )
        self.assertIsNone(form.fields["management_entity"].initial)
