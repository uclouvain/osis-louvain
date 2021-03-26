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
import random

from django.test import SimpleTestCase

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from education_group.ddd.domain.exception import HopsFieldsAllOrNone, \
    AresCodeShouldBeGreaterOrEqualsThanZeroAndLessThan9999, AresGracaShouldBeGreaterOrEqualsThanZeroAndLessThan9999, \
    AresAuthorizationShouldBeGreaterOrEqualsThanZeroAndLessThan9999
from education_group.ddd.validators._hops_validator import HopsValuesValidator, HopsFields2OrNoneForFormationPhd
from education_group.tests.ddd.factories.hops import HOPSFactory
from education_group.tests.ddd.factories.training import TrainingFactory
from education_group.tests.factories.mini_training import MiniTrainingFactory
from base.models.enums.education_group_types import TrainingType

MAX_VALUE_FOR_HOPS_FIELD = 9999
MIN_VALUE_FOR_HOPS_FIELD = 1


class TestHopsValidator(SimpleTestCase):

    def test_validation_ok_on_hops_fields_when_not_training(self):
        mini_training = MiniTrainingFactory()
        validator = HopsValuesValidator(training=mini_training)
        self.assertTrue(validator.is_valid())

    def test_validation_all_hops_fields_present(self):
        hops = HOPSFactory(ares_code=random.randint(MIN_VALUE_FOR_HOPS_FIELD, MAX_VALUE_FOR_HOPS_FIELD),
                           ares_graca=random.randint(MIN_VALUE_FOR_HOPS_FIELD, MAX_VALUE_FOR_HOPS_FIELD),
                           ares_authorization=random.randint(MIN_VALUE_FOR_HOPS_FIELD, MAX_VALUE_FOR_HOPS_FIELD))

        training = TrainingFactory(hops=hops)
        validator = HopsValuesValidator(training=training)
        self.assertTrue(validator.is_valid())

    def test_validation_hops_field_ares_code_missing(self):
        hops = HOPSFactory(ares_code=None,
                           ares_graca=random.randint(MIN_VALUE_FOR_HOPS_FIELD, MAX_VALUE_FOR_HOPS_FIELD),
                           ares_authorization=random.randint(MIN_VALUE_FOR_HOPS_FIELD, MAX_VALUE_FOR_HOPS_FIELD))

        training = TrainingFactory(hops=hops, type=TrainingType.BACHELOR)
        validator = HopsValuesValidator(training=training)

        with self.assertRaises(MultipleBusinessExceptions) as e:
            validator.is_valid()

        self.assertIsInstance(
            e.exception.exceptions.pop(),
            HopsFieldsAllOrNone
        )

    def test_validation_hops_field_ares_code_missing_for_phd(self):
        hops = HOPSFactory(ares_code=None,
                           ares_graca=None,
                           ares_authorization=random.randint(MIN_VALUE_FOR_HOPS_FIELD, MAX_VALUE_FOR_HOPS_FIELD))

        training = TrainingFactory(hops=hops, type=TrainingType.FORMATION_PHD)
        validator = HopsValuesValidator(training=training)

        with self.assertRaises(MultipleBusinessExceptions) as e:
            validator.is_valid()

        self.assertIsInstance(
            e.exception.exceptions.pop(),
            HopsFields2OrNoneForFormationPhd
        )

    def test_validation_ares_code_not_valid(self):
        hops = HOPSFactory(ares_code=-1,
                           ares_graca=random.randint(MIN_VALUE_FOR_HOPS_FIELD, MAX_VALUE_FOR_HOPS_FIELD),
                           ares_authorization=random.randint(MIN_VALUE_FOR_HOPS_FIELD, MAX_VALUE_FOR_HOPS_FIELD))

        self.assert_hops_field_valid_value(hops, AresCodeShouldBeGreaterOrEqualsThanZeroAndLessThan9999)

    def test_validation_ares_graca_not_valid(self):
        hops = HOPSFactory(ares_code=random.randint(MIN_VALUE_FOR_HOPS_FIELD, MAX_VALUE_FOR_HOPS_FIELD),
                           ares_graca=-1,
                           ares_authorization=random.randint(MIN_VALUE_FOR_HOPS_FIELD, MAX_VALUE_FOR_HOPS_FIELD))

        self.assert_hops_field_valid_value(hops, AresGracaShouldBeGreaterOrEqualsThanZeroAndLessThan9999)

    def test_validation_ares_authorization_not_valid(self):
        hops = HOPSFactory(ares_code=random.randint(MIN_VALUE_FOR_HOPS_FIELD, MAX_VALUE_FOR_HOPS_FIELD),
                           ares_graca=random.randint(MIN_VALUE_FOR_HOPS_FIELD, MAX_VALUE_FOR_HOPS_FIELD),
                           ares_authorization=-1)

        self.assert_hops_field_valid_value(hops, AresAuthorizationShouldBeGreaterOrEqualsThanZeroAndLessThan9999)

    def assert_hops_field_valid_value(self, hops, exception_raised):
        training = TrainingFactory(hops=hops)
        validator = HopsValuesValidator(training=training)
        with self.assertRaises(MultipleBusinessExceptions) as e:
            validator.is_valid()
        self.assertIsInstance(
            e.exception.exceptions.pop(),
            exception_raised
        )
