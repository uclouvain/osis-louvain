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
from typing import Any, List

import mock

from osis_common.ddd import interface


class MockFormValid(mock.Mock):

    errors = []
    changed_data = ['dummy_field']

    def is_valid(self):
        return True

    @property
    def cleaned_data(self):
        return mock.MagicMock()

    def add_error(self, field, error):
        self.errors.append('error')


class FakeRepository:
    root_entities = list()  # type: List['interface.RootEntity']
    not_found_exception_class = None

    @classmethod
    def create(cls, domain_obj: interface.RootEntity, **_) -> interface.EntityIdentity:
        cls.root_entities.append(domain_obj)
        return domain_obj.entity_id

    @classmethod
    def update(cls, domain_obj: interface.RootEntity, **_) -> interface.EntityIdentity:
        idx = -1
        for idx, entity in enumerate(cls.root_entities):
            if entity.entity_id == domain_obj.entity_id:
                break
        if idx >= 0:
            cls.root_entities[idx] = domain_obj
        else:
            raise cls.not_found_exception_class()

        return domain_obj.entity_id

    @classmethod
    def get(cls, entity_id: interface.EntityIdentity) -> interface.RootEntity:
        try:
            return next((root_entity for root_entity in cls.root_entities if root_entity.entity_id == entity_id))
        except StopIteration:
            raise cls.not_found_exception_class()

    @classmethod
    def delete(cls, entity_id: interface.EntityIdentity, **_) -> None:
        idx = -1
        for idx, entity in enumerate(cls.root_entities):
            if entity.entity_id == entity_id:
                break
        if idx >= 0:
            cls.root_entities.pop(idx)


class MockPatcherMixin:
    def mock_service(self, service_path: str, return_value: Any = None) -> mock.Mock:
        service_patcher = mock.patch(service_path, return_value=return_value)
        self.addCleanup(service_patcher.stop)

        return service_patcher.start()

    def mock_repo(self, repository_path: 'str', fake_repo: 'Any') -> mock.Mock:
        repository_patcher = mock.patch(repository_path, new=fake_repo)
        self.addCleanup(repository_patcher.stop)

        return repository_patcher.start()
