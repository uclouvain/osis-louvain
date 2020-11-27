import datetime
import logging

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from backoffice.celery import app as celery_app
from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.entity_version_address import EntityVersionAddress
from base.models.enums import organization_type, entity_type
from base.models.organization import Organization

from reference.models.country import Country

logger = logging.getLogger(settings.DEFAULT_LOGGER)


@celery_app.task
def run() -> dict:
    try:
        raw_entities = __fetch_entities_from_esb()
        raw_root_entity = next(entity for entity in raw_entities if __is_root_entity(entity))
        __upsert_entity(raw_root_entity)
        __save_children_entities(raw_root_entity, raw_entities)
        return {'Entities synchronized': 'OK'}
    except FetchEntitiesException:
        return {'Entities synchronized': 'Unable to fetch data from ESB'}


def __fetch_entities_from_esb():
    if not all([settings.ESB_API_URL, settings.ESB_ENTITIES_HISTORY_ENDPOINT]):
        raise ImproperlyConfigured('ESB_API_URL / ESB_ENTITIES_HISTORY_ENDPOINT must be set in configuration')

    endpoint = settings.ESB_ENTITIES_HISTORY_ENDPOINT
    url = "{esb_api}/{endpoint}".format(esb_api=settings.ESB_API_URL, endpoint=endpoint)
    try:
        entities_wrapped = requests.get(
            url,
            headers={"Authorization": settings.ESB_AUTHORIZATION},
            timeout=settings.REQUESTS_TIMEOUT or 20
        )
        return entities_wrapped.json()['entities']['entity']
    except Exception:
        logger.info("[Synchronize entities] An error occured during fetching entities on ESB")
        raise FetchEntitiesException


def __fetch_address_from_esb(raw_entity):
    if not all([settings.ESB_API_URL, settings.ESB_ENTITY_ADDRESS_ENDPOINT]):
        raise ImproperlyConfigured('ESB_API_URL / ESB_ENTITY_ADDRESS_ENDPOINT must be set in configuration')

    endpoint = settings.ESB_ENTITY_ADDRESS_ENDPOINT.format(entity_id=raw_entity['entity_id'])
    url = "{esb_api}/{endpoint}".format(esb_api=settings.ESB_API_URL, endpoint=endpoint)
    try:
        entity_address_wrapper = requests.get(
            url,
            headers={"Authorization": settings.ESB_AUTHORIZATION},
            timeout=settings.REQUESTS_TIMEOUT or 20
        )
        return entity_address_wrapper.json()['address']
    except Exception:
        logger.info("[Synchronize entities] An error occured during fetching address on ESB "
                    "of entity" + raw_entity['acronym'])
        raise FetchEntitiesException


def __save_children_entities(raw_entity, all_raw_entities):
    for child_entity in filter(lambda entity: entity['parent_entity_id'] == raw_entity['entity_id'], all_raw_entities):
        __upsert_entity(child_entity)
        __save_children_entities(child_entity, all_raw_entities)


def __upsert_entity(raw_entity):
    raw_address = __fetch_address_from_esb(raw_entity)

    entity, _ = Entity.objects.update_or_create(
        external_id=__build_entity_external_id(raw_entity['entity_id']),
        defaults={
            'website': raw_entity['web'] or '',
            'organization': Organization.objects.only('pk').get(type=organization_type.MAIN),
            'fax': raw_address['fax'] or '',
            'phone': raw_address['phone'] or ''
        }
    )

    parent = Entity.objects.only('pk').get(external_id=__build_entity_external_id(raw_entity['parent_entity_id'])) \
        if not __is_root_entity(raw_entity) else None
    try:
        entity_version, _ = EntityVersion.objects.update_or_create(
            entity=entity,
            acronym=raw_entity['acronym'],
            parent=parent,
            title=raw_entity['name_fr'],
            entity_type=__get_entity_type(raw_entity),
            start_date=ESBDate(raw_entity['begin']).to_date(),
            defaults={
                'end_date': ESBDate(raw_entity['end']).to_date()
            }
        )

        EntityVersionAddress.objects.update_or_create(
            entity_version=entity_version,
            is_main=True,
            defaults={
                'city': raw_address['town'] or '',
                'street': raw_address['streetName'] or '',
                'street_number': raw_address['streetNumber'] or '',
                'postal_code': raw_address['postCode'] or '',
                'country': Country.objects.only('pk').get(iso_code='BE'),
            }
        )
    except AttributeError:
        logger.info("[Synchronize entities] Overlapping found for " + raw_entity['acronym'])


def __build_entity_external_id(esb_id) -> str:
    return 'osis.entity_{}'.format(esb_id)


def __is_root_entity(raw_entity) -> bool:
    return raw_entity['parent_entity_id'] == {"@nil": "true"}


def __get_entity_type(raw_entity) -> str:
    return {
        'S': entity_type.SECTOR,
        'F': entity_type.FACULTY,
        'E': entity_type.SCHOOL,
        'I': entity_type.INSTITUTE,
        'P': entity_type.POLE,
        'D': entity_type.DOCTORAL_COMMISSION,
        'T': entity_type.PLATFORM,
        'L': entity_type.LOGISTICS_ENTITY,
        'N': '',
    }.get(raw_entity['departmentType'])


class ESBDate(int):
    """
    The date format comming from ESB data is in format 20100101 which means 01/01/2010
    The undefined value is represented as 99991231
    """
    def to_date(self):
        if self == 99991231:
            return None
        date_str = str(self)
        return datetime.date(year=int(date_str[0:4]), month=int(date_str[4:6]), day=int(date_str[6:8]))


class FetchEntitiesException(Exception):
    def __init__(self, **kwargs):
        self.message = "Unable to fetch entities data"
        super().__init__(**kwargs)
