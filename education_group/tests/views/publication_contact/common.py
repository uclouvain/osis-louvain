#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.db.models import Model

from base.models.education_group_publication_contact import EducationGroupPublicationContact
from base.models.education_group_year import EducationGroupYear
from base.models.enums.publication_contact_type import PublicationContactType
from base.tests.factories.education_group_publication_contact import EducationGroupPublicationContactFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity_version import MainEntityVersionFactory


class TestPublicationContactMixin:
    def generate_publication_contact_data(self):
        self.publication_contact = EducationGroupPublicationContactFactory(
            education_group_year__academic_year__current=True,
            type=PublicationContactType.OTHER_ACADEMIC_RESPONSIBLE.name
        )
        self.education_group_year = self.publication_contact.education_group_year
        self.next_year_education_group_year = EducationGroupYearFactory.next_year_from(self.education_group_year)

        self.other_entity_version = MainEntityVersionFactory()

    def assert_publication_entity_equal(self, obj: 'EducationGroupYear', other_obj: 'EducationGroupYear'):
        obj.refresh_from_db()
        other_obj.refresh_from_db()
        self.assertEqual(obj.publication_contact_entity, other_obj.publication_contact_entity)

    def assert_publication_contacts_equal(self, obj: 'EducationGroupYear', other_obj: 'EducationGroupYear'):
        publication_contacts = EducationGroupPublicationContact.objects.filter(
            education_group_year=obj
        )

        to_compare_publication_contacts = EducationGroupPublicationContact.objects.filter(
            education_group_year=other_obj
        )

        for contact, other_contact in zip(publication_contacts, to_compare_publication_contacts):
            self._assert_model_equal(contact, other_contact)

    def _assert_model_equal(self, obj: 'Model', other_obj: 'Model'):
        fields_not_compare = (
            "external_id",
            "changed",
            "uuid",
            "id",
            "education_group_year_id",
        )
        model_fields = obj._meta.fields
        fields_to_compare = [field.attname for field in model_fields if field.attname not in fields_not_compare]
        for field in fields_to_compare:
            self.assertEqual(getattr(obj, field), getattr(other_obj, field), field)

