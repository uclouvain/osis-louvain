############################################################################
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
############################################################################
import collections

from factory.faker import Faker
from faker.providers import BaseProvider

Language = collections.namedtuple("Language", "code, name")

_LANGUAGES = (
    ("LN", "Lingala"), ("NO", "Norvégien"), ("PL", "Polonais"), ("QU", "Quechua"), ("RO", "Roumain"), ("RU", "Russe"),
    ("SL", "Slovène"), ("SR", "Serbe"), ("SV", "Suédois"), ("SW", "Swahéli"), ("TR", "Turc"), ("UK", "Ukrainien"),
    ("ZH", "Chinois"), ("??", "Langue des signes de Belgique fr."), ("FI", "Finnois"), ("XX", "Indéterminé"),
    ("FR", "Français"), ("EN", "Anglais"), ("ES", "Espagnol"), ("DE", "Allemand"), ("NL", "Néerlandais"),
    ("IT", "Italien"), ("PT", "Portugais"), ("AR", "Arabe"), ("CA", "Catalan"), ("CS", "Tchèque"), ("DA", "Danois"),
    ("EL", "Grec"), ("GA", "Irlandais"), ("GL", "Galicien"), ("HE", "Hébreu"), ("HI", "Hindi"), ("HR", "Croate"),
    ("HU", "Hongrois"), ("HY", "Arménien"), ("JP", "Japonais"), ("KA", "Géorgien"), ("KO", "Coréen"), ("LA", "Latin")
)

LANGUAGES = tuple(Language(lang[0], lang[1]) for lang in _LANGUAGES)


class OsisProvider(BaseProvider):
    def language(self) -> Language:
        """
        Returns a random language
        :return: a random Language
        """
        return self.generator.random.choice(LANGUAGES)


Faker.add_provider(OsisProvider)
