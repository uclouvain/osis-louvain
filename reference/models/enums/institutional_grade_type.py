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

from django.utils.translation import gettext_lazy as _

BACHELOR = "BACHELOR"
MASTER_60 = "MASTER_60"
MASTER_120 = "MASTER_120"
MASTER_180_OR_240 = "MASTER_180_OR_240"
ADVANCED_MASTER = "ADVANCED_MASTER"
TRAINING_CERTIFICATE = "TRAINING_CERTIFICATE"
CERTIFICATE = "CERTIFICATE"
DOCTORATE = "DOCTORATE"
CAPAES = "CAPAES"

INSTITUTIONAL_GRADE_CHOICES = (
    ('BACHELOR', BACHELOR),
    ('MASTER_60', MASTER_60),
    ('MASTER_120', MASTER_120),
    ('MASTER_180_OR_240', MASTER_180_OR_240),
    ('ADVANCED_MASTER', ADVANCED_MASTER),
    ('TRAINING_CERTIFICATE', TRAINING_CERTIFICATE),
    ('CERTIFICATE', CERTIFICATE),
    ('DOCTORATE', DOCTORATE),
    ('CAPAES',CAPAES))


def translate_by_key(key_to_trans):
    for key, value in INSTITUTIONAL_GRADE_CHOICES:
        if key_to_trans == key:
            return _(value)
    return None
