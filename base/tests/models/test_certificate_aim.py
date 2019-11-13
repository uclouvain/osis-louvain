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

from base.tests.factories.certificate_aim import CertificateAimFactory


class TestCertificateAim(TestCase):
    def setUp(self):
        self.certificate_aim = CertificateAimFactory(
            section=9,
            code=987,
            description="Description of the certificate aim"
        )

    def test__str__(self):
        error_msg = "This __str__ representation is used into MultipleSelect (Django-autocomplete-light) " \
                    "into view 'EducationGroupDiplomas.as_view()'"
        self.assertEqual(str(self.certificate_aim), "9 - 987 Description of the certificate aim", error_msg)