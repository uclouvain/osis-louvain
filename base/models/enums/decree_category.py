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
from django.utils.translation import ugettext_lazy as _

from base.models.utils.utils import ChoiceEnum

FCONT = "FCONT"
BAS1 = "1BAS"
BAS2 = "2BAS"
AESS = "AESS"
DEC1 = "DEC1"
DEC2 = "DEC2"
DES = "DES"
DEA = "DEA"
DOC = "DOC"
AES = "AES"
AUTRE = "AUTRE"
BAC = "BAC"
AP2C = "AP2C"
MA1 = "MA1"
MA2X = "MA2X"
MA2D = "MA2D"
MA2S = "MA2S"
MA2A = "MA2A"
MA2M = "MA2M"
AS2C = "AS2C"
MACO = "MACO"
AESSB = "AESSB"
CAPS = "CAPS"
AS3C = "AS3C"
FODO = "FODO"
DOCB = "DOCB"
CEMC = "CEMC"
MED = "MED"
VETE = "VETE"

DECREE_CATEGORY = (
    (FCONT, _(FCONT)),
    (BAS1, _(BAS1)),
    (BAS2, _(BAS2)),
    (AESS, _(AESS)),
    (DEC1, _(DEC1)),
    (DEC2, _(DEC2)),
    (DES, _(DES)),
    (DEA, _(DEA)),
    (DOC, _(DOC)),
    (AES, _(AES)),
    (AUTRE, _(AUTRE)),
    (BAC, _(BAC)),
    (AP2C, _(AP2C)),
    (MA1, _(MA1)),
    (MA2X, _(MA2X)),
    (MA2D, _(MA2D)),
    (MA2S, _(MA2S)),
    (MA2A, _(MA2A)),
    (MA2M, _(MA2M)),
    (AS2C, _(AS2C)),
    (MACO, _(MACO)),
    (AESSB, _(AESSB)),
    (CAPS, _(CAPS)),
    (AS3C, _(AS3C)),
    (FODO, _(FODO)),
    (DOCB, _(DOCB)),
    (CEMC, _(CEMC)),
    (MED, _(MED)),
    (VETE, _(VETE))
)


class DecreeCategories(ChoiceEnum):
    FCONT = "FCONT"
    BAS1 = "BAS1"
    BAS2 = "BAS2"
    AESS = "AESS"
    DEC1 = "DEC1"
    DEC2 = "DEC2"
    DES = "DES"
    DEA = "DEA"
    DOC = "DOC"
    AES = "AES"
    AUTRE = "AUTRE"
    BAC = "BAC"
    AP2C = "AP2C"
    MA1 = "MA1"
    MA2X = "MA2X"
    MA2D = "MA2D"
    MA2S = "MA2S"
    MA2A = "MA2A"
    MA2M = "MA2M"
    AS2C = "AS2C"
    MACO = "MACO"
    AESSB = "AESSB"
    CAPS = "CAPS"
    AS3C = "AS3C"
    FODO = "FODO"
    DOCB = "DOCB"
    CEMC = "CEMC"
    MED = "MED"
    VETE = "VETE"
