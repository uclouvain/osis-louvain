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

from base.models.utils.utils import ChoiceEnum


# FIXME Get decree category title in english
class DecreeCategories(ChoiceEnum):
    FCONT = "Formation continue (non académique)"
    BAC = "Bachelier"
    MA1 = "Master en 60 crédits"
    MA2X = "Master en 120 crédits"
    MA2D = "Master en 120 crédits à finalité didactique"
    MA2S = "Master en 120 crédits à finalité spécialisée"
    MA2A = "Master en 120 crédits à finalité approfondie"
    MA2M = "Master en 180 ou 240 crédits"
    MACO = "Master complémentaire"
    AESSB = "Agrégation de l'enseignement secondaire supérieur (AESS)"
    CAPS = "Certificat d'aptitude pédagogique approprié à l'enseignement supérieur (CAPAES)"
    FODO = "Formations doctorales (Certificat de formation à la recherche)"
    DOCB = "Docteur"
    CEMC = "Certificats de médecine clinique / Certificats interuniversitaires de formation médicale spécialisée"

    @classmethod
    def choices(cls):
        return tuple((x.name, "{name} - {value}".format(name=x.name, value=x.value)) for x in cls)
