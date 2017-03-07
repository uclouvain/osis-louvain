import operator
import datetime

import factory
import factory.fuzzy

from django.conf import settings
from django.utils import timezone

from base.models import person

from base.factories.user import UserFactory

def _get_tzinfo():
    if settings.USE_TZ:
        return timezone.get_current_timezone()
    else:
        return None


def generate_person_email(person, domain=None):
    if domain is None:
        domain = factory.Faker('domain_name').generate({})
    return '{0.first_name}.{0.last_name}@{1}'.format(person, domain).lower()


class PersonFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'base.Person'

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    changed = factory.fuzzy.FuzzyDateTime(datetime.datetime(2016, 1, 1, tzinfo=_get_tzinfo()))
    email = factory.LazyAttribute(generate_person_email)
    phone = factory.Faker('phone_number')
    language = factory.Iterator(settings.LANGUAGES, getter=operator.itemgetter(0))
    gender = factory.Iterator(person.Person.GENDER_CHOICES, getter=operator.itemgetter(0))
    user = factory.SubFactory(UserFactory)
