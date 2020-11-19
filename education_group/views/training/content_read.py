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
import functools
from typing import List

from base.utils.urls import reverse_with_get
from education_group.views.training.common_read import TrainingRead, Tab
from program_management.ddd.repositories import load_tree


class TrainingReadContent(TrainingRead):
    template_name = "education_group_app/training/content_read.html"
    active_tab = Tab.CONTENT

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "children": self.get_children()
        }

    def get_update_training_url(self):
        return reverse_with_get(
            'content_update',
            kwargs={'code': self.kwargs['code'], 'year': self.kwargs['year']},
            get={"path_to": self.path, "tab": self.active_tab.name}
        )

    def get_update_permission_name(self) -> str:
        return "base.change_link_data"

    @functools.lru_cache()
    def get_tree(self):
        return load_tree.load(self.get_root_id())

    def get_children(self) -> List['Node']:
        parent_node = self.get_tree().get_node(self.path)
        return parent_node.children
