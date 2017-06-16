##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from base.models import entity
from base.models import entity_version
from base.serializers import EntitySerializer


@api_view(['POST'])
def post_entities(request):
    existing_entity = entity.get_by_external_id(request.data.get('external_id'))

    if existing_entity is None:
        return create_full_entity(request)

    else:
        return update_existing_entity(existing_entity, request)


def create_full_entity(request):
    entity_data = {
        'organization': request.data.get('organization'),
        'external_id': request.data.get('external_id'),
        'website': request.data.get('website'),
        'entityversion_set': request.data.get('entityversion_set'),
        'location': request.data.get('location'),
        'postal_code': request.data.get('postal_code'),
        'city': request.data.get('city'),
        'country': request.data.get('country')
    }
    entity_serializer = EntitySerializer(data=entity_data)
    if entity_serializer.is_valid():
        try:
            entity_serializer.save()
        except AttributeError:
            return Response(data=entity_serializer.errors, status=status.HTTP_406_NOT_ACCEPTABLE)
        return Response(data=entity_serializer.data, status=status.HTTP_201_CREATED)
    return Response(data=entity_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def update_existing_entity(existing_entity, request):
    new_versions_count = create_versions_of_existing_entity(request, existing_entity)
    entity_serializer = EntitySerializer(existing_entity)
    data = entity_serializer.data
    data['new_versions_count'] = new_versions_count
    return Response(data=data, status=status.HTTP_200_OK)


def create_versions_of_existing_entity(request, same_entity):
    new_versions_count = 0
    entityversion_data = request.data.get('entityversion_set')
    for version in entityversion_data:
        same_versions_count = entity_version.count(entity=same_entity,
                                                   title=version.get('title'),
                                                   acronym=version.get('acronym'),
                                                   entity_type=version.get('entity_type'),
                                                   parent=version.get('parent'),
                                                   start_date=version.get('start_date'),
                                                   end_date=version.get('end_date')
                                                   )
        if not same_versions_count:
            parent = entity.get_by_internal_id(version.pop('parent'))
            if create_version(version, same_entity, parent) is not None:
                new_versions_count += 1

    return new_versions_count


def create_version(version, same_entity, parent):
        try:
            new_version = entity_version.EntityVersion.objects.create(entity=same_entity, parent=parent, **version)
        except AttributeError:
            new_version = None
        return new_version
