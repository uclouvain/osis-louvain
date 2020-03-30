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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################

from django.test import TestCase

from base.models.prerequisite import Prerequisite
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.prerequisite import PrerequisiteFactory
from program_management.forms.prerequisite import LearningUnitPrerequisiteForm


class TestPrerequisiteForm(TestCase):
    def setUp(self):
        self.luy_1 = LearningUnitYearFactory()
        self.luy_2 = LearningUnitYearFactory()
        self.prerequisite = PrerequisiteFactory()
        self.codes_permitted = [self.luy_1.acronym, self.luy_2.acronym]

    def test_prerequisite_form_with_prerequisites(self):
        form = LearningUnitPrerequisiteForm(
            instance=self.prerequisite,
            codes_permitted=self.codes_permitted,
            data={"prerequisite_string": "{} ET {}".format(self.codes_permitted[0], self.codes_permitted[1])}
        )
        self.assertTrue(form.is_valid())
        form.save()
        self.assertTrue(Prerequisite.objects.filter(pk=self.prerequisite.pk))

    def test_prerequisite_form_without_prerequisites(self):
        form = LearningUnitPrerequisiteForm(
            instance=self.prerequisite,
            codes_permitted=self.codes_permitted,
            data={"prerequisite_string": ""}
        )
        self.assertTrue(form.is_valid())
        form.save()
        self.assertFalse(Prerequisite.objects.filter(pk=self.prerequisite.pk))
