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

from base.models.enums.constraint_type import ConstraintTypeEnum
from education_group.ddd.domain._content_constraint import ContentConstraint
from education_group.ddd.domain.exception import ContentConstraintTypeMissing, ContentConstraintMinimumMaximumMissing, \
    ContentConstraintMaximumShouldBeGreaterOrEqualsThanMinimum, ContentConstraintMinimumInvalid, \
    ContentConstraintMaximumInvalid
from education_group.ddd.validators._content_constraint import ContentConstraintValidator
from education_group.ddd.validators._content_constraint import MIN_CONSTRAINT_VALUE, MAX_CONSTRAINT_VALUE


class TestContentConstraintValidator(SimpleTestCase):
    def test_assert_type_missing_exception_when_type_is_not_defined_but_min_and_max_set(self):
        content_constraint = ContentConstraint(
            type=None,
            minimum=1,
            maximum=10
        )
        validator = ContentConstraintValidator(content_constraint)
        with self.assertRaises(ContentConstraintTypeMissing):
            validator.is_valid()

    def test_assert_min_max_missing_exception_when_type_is_defined_but_not_min_and_max(self):
        content_constraint = ContentConstraint(
            type=ConstraintTypeEnum.CREDITS,
            minimum=None,
            maximum=None
        )
        validator = ContentConstraintValidator(content_constraint)
        with self.assertRaises(ContentConstraintMinimumMaximumMissing):
            validator.is_valid()

    def test_assert_maximum_should_be_equals_or_greater_than_minimum(self):
        content_constraint = ContentConstraint(
            type=ConstraintTypeEnum.CREDITS,
            minimum=10,
            maximum=9
        )
        validator = ContentConstraintValidator(content_constraint)
        with self.assertRaises(ContentConstraintMaximumShouldBeGreaterOrEqualsThanMinimum):
            validator.is_valid()

    def test_when_min_is_set_but_not_max(self):
        content_constraint = ContentConstraint(
            type=ConstraintTypeEnum.CREDITS,
            minimum=10,
            maximum=None
        )
        validator = ContentConstraintValidator(content_constraint)
        self.assertTrue(validator.is_valid())

    def test_when_max_is_set_but_not_min(self):
        content_constraint = ContentConstraint(
            type=ConstraintTypeEnum.CREDITS,
            minimum=None,
            maximum=10
        )
        validator = ContentConstraintValidator(content_constraint)
        self.assertTrue(validator.is_valid())

    def test_content_type_valid(self):
        content_constraint = ContentConstraint(
            type=ConstraintTypeEnum.CREDITS,
            minimum=1,
            maximum=10
        )
        validator = ContentConstraintValidator(content_constraint)
        self.assertTrue(validator.is_valid())

    def test_when_min_is_set_but_invalid(self):
        content_constraint = ContentConstraint(
            type=ConstraintTypeEnum.CREDITS,
            minimum=MIN_CONSTRAINT_VALUE - 9,
            maximum=None
        )
        validator = ContentConstraintValidator(content_constraint)
        with self.assertRaises(ContentConstraintMinimumInvalid):
            validator.is_valid()

    def test_when_max_is_set_but_invalid(self):
        content_constraint = ContentConstraint(
            type=ConstraintTypeEnum.CREDITS,
            minimum=None,
            maximum=MAX_CONSTRAINT_VALUE + 1
        )
        validator = ContentConstraintValidator(content_constraint)
        with self.assertRaises(ContentConstraintMaximumInvalid):
            validator.is_valid()
