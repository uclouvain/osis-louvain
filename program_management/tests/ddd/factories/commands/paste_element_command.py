# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
import factory.fuzzy

from program_management.ddd import command


class PasteElementCommandFactory(factory.Factory):
    class Meta:
        model = command.PasteElementCommand
        abstract = False

    node_to_paste_code = "LSINF2547"
    node_to_paste_year = factory.Faker("random_int")
    path_where_to_paste = factory.LazyFunction(lambda: str(factory.Faker("random_int")))
    access_condition = None
    is_mandatory = None
    block = None
    link_type = None
    comment = ""
    comment_english = ""
    relative_credits = None
    path_where_to_detach = None
