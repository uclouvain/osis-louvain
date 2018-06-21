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
from django.test import TestCase
from base.forms.education_group.create import CreateEducationGroupYearForm, CreateOfferYearEntityForm
from base.models.enums import offer_year_entity_type, education_group_categories, organization_type
from base.models.group_element_year import GroupElementYear
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.campus import CampusFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity_version import MainEntityVersionFactory


class TestCreateEducationGroupYearForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.education_group_type = EducationGroupTypeFactory(category=education_group_categories.GROUP)
        cls.campus = CampusFactory(organization__type=organization_type.MAIN)
        cls.academic_year = AcademicYearFactory()
        cls.form_data = {
            "acronym": "ACRO4569",
            "partial_acronym": "PACR8974",
            "education_group_type": cls.education_group_type.id,
            "title": "Test data",
            "main_teaching_campus": cls.campus.id,
            "academic_year": cls.academic_year.id,
            "remark": "This is a test!!"
        }

        cls.parent_education_group_year = EducationGroupYearFactory()

    def test_fields(self):
        fields = ("acronym", "partial_acronym", "education_group_type", "title", "title_english", "credits",
                  "main_teaching_campus", "academic_year", "remark", "remark_english", "min_credits", "max_credits")

        form = CreateEducationGroupYearForm()
        self.assertCountEqual(tuple(form.fields.keys()), fields)

    def test_save(self):
        form = CreateEducationGroupYearForm(data=self.form_data)

        self.assertTrue(form.is_valid(), form.errors)

        education_group_year = form.save()

        self.assertEqual(education_group_year.education_group.start_year, self.academic_year.year)
        self.assertIsNone(education_group_year.education_group.end_year)

    def test_save_with_parent(self):
        form = CreateEducationGroupYearForm(data=self.form_data)

        self.assertTrue(form.is_valid(), form.errors)

        education_group_year = form.save(self.parent_education_group_year)

        self.assertTrue(GroupElementYear.objects.get(child_branch=education_group_year,
                                                     parent=self.parent_education_group_year))


class TestCreateOfferYearEntityForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.entity_version = MainEntityVersionFactory()
        cls.education_group_year = EducationGroupYearFactory()
        cls.form_data = {
            "entity": cls.entity_version.id
        }

    def test_fields(self):
        fields = ("entity", )

        form = CreateOfferYearEntityForm()
        self.assertCountEqual(tuple(form.fields.keys()), fields)

    def test_save(self):
        form = CreateOfferYearEntityForm(data=self.form_data)
        self.assertTrue(form.is_valid(), form.errors)

        offer_year_entity = form.save(self.education_group_year)

        self.assertEqual(offer_year_entity.education_group_year, self.education_group_year)
        self.assertEqual(offer_year_entity.type, offer_year_entity_type.ENTITY_ADMINISTRATION)
        self.assertIsNone(offer_year_entity.offer_year)
