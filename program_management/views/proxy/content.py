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
from django.urls import reverse
from django.views.generic import RedirectView

from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.repositories.node import NodeRepository


class ContentRedirectView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        year = self.kwargs['year']
        code = self.kwargs['code']
        root_node = NodeRepository().get(NodeIdentity(code=code, year=year))
        if root_node.is_training():
            url_name = "training_content"
            url_kwargs = {'year': root_node.year, 'code': root_node.code}
        elif root_node.is_mini_training():
            url_name = "mini_training_content"
            url_kwargs = {'year': root_node.year, 'code': root_node.code}
        elif root_node.is_learning_unit():
            url_name = "learning_unit"
            url_kwargs = {'year': root_node.year, 'acronym': root_node.code}
        else:
            url_name = "group_content"
            url_kwargs = {'year': root_node.year, 'code': root_node.code}
        self.url = reverse(
            url_name,
            kwargs=url_kwargs
        )
        return super().get_redirect_url(*args, **kwargs)
