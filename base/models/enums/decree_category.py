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


# FIXME Get decree category title in english
class DecreeCategories(ChoiceEnum):
    FCONT = "Formation continue (non académique)"
    BAS1 = "Etudes de base de premier cycle"
    BAS2 = "Etudes de base de deuxième cycle"
    AESS = "A.E.S.S."
    DEC1 = "Etudes complémentaires de premier cycle"
    DEC2 = "Etudes complémentaires de deuxième cycle"
    DES = "Etudes spécialisées de troisième cycle"
    DEA = "Etudes approfondies de troisième cycle"
    AES = "A.E.S."
    AUTRE = "Autre (non académique)"
    BAC = "Bachelier"
    AP2C = "Année préparatoire à un 2ème cycle"
    MA1 = "Master en 60 crédits"
    MA2X = "Master en 120 crédits"
    MA2D = "Master en 120 crédits à finalité didactique"
    MA2S = "Master en 120 crédits à finalité spécialisée"
    MA2A = "Master en 120 crédits à finalité approfondie"
    MA2M = "Master en 180 ou 240 crédits"
    AS2C = "Année supplémentaire à un 2ème cycle"
    MACO = "Master complémentaire"
    AESSB = "Agrégation de l'enseignement secondaire supérieur (AESS)"
    CAPS = "Certificat d'aptitude pédagogique approprié à l'enseignement supérieur (CAPAES)"
    AS3C = "Année supplémentaire à un 3ème cycle"
    FODO = "Formations doctorales (Certificat de formation à la recherche)"
    DOCB = "Docteur"
    CEMC = "Certificats de médecine clinique / Certificats interuniversitaires de formation médicale spécialisée"
    MED = "Médecin"
    VETE = "Médecin vétérinaire"

    @classmethod
    def choices(cls):
        return tuple((x.name, "{name} - {value}".format(name=x.name, value=x.value)) for x in cls)
