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
from django.conf import settings
from django.db.models import Case, When, F, CharField
from rest_framework import serializers

from base.models.education_group_publication_contact import EducationGroupPublicationContact
from base.models.education_group_year import EducationGroupYear
from base.models.enums.publication_contact_type import PublicationContactType
from webservices.business import get_contacts_intro_text


class ContactSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='translated_role', read_only=True)
    description = serializers.CharField(source='description_or_none', read_only=True)

    class Meta:
        model = EducationGroupPublicationContact

        fields = (
            'description',
            'email',
            'role'
        )


class ContactsSerializer(serializers.ModelSerializer):
    contacts = serializers.SerializerMethodField()
    text = serializers.SerializerMethodField()
    entity = serializers.CharField(source='publication_contact_entity_version.acronym', read_only=True)
    management_entity = serializers.CharField(source='management_entity_version.acronym', read_only=True)

    class Meta:
        model = EducationGroupYear

        fields = (
            'contacts',
            'text',
            'entity',
            'management_entity'
        )

    def get_text(self, obj):
        text = get_contacts_intro_text(obj, self.context.get('lang'))
        return text if text else None

    def get_contacts(self, obj):
        contact_types = [
            (PublicationContactType.ACADEMIC_RESPONSIBLE.name, 'academic_responsibles'),
            (PublicationContactType.OTHER_ACADEMIC_RESPONSIBLE.name, 'other_academic_responsibles'),
            (PublicationContactType.JURY_MEMBER.name, 'jury_members'),
            (PublicationContactType.OTHER_CONTACT.name, 'other_contacts')
        ]
        lookup_field = 'role_fr' if self.context.get('lang') == settings.LANGUAGE_CODE_FR else 'role_en'
        lookup_expr = '__'.join([lookup_field, 'exact'])
        datas = {
            contact_type: ContactSerializer(
                obj.educationgrouppublicationcontact_set.filter(type=type_name).annotate(
                    description_or_none=Case(
                        When(description__exact='', then=None),
                        default=F('description'),
                        output_field=CharField()
                    ),
                    translated_role=Case(
                        When(**{lookup_expr: ''}, then=None),
                        default=lookup_field,
                        output_field=CharField()
                    ),
                ),
                many=True,
                read_only=True
            ).data
            for type_name, contact_type in contact_types
        }
        return self._remove_empty_contact_type(datas)

    @staticmethod
    def _remove_empty_contact_type(datas):
        for contact_type, contact in datas.copy().items():
            if not contact:
                datas.pop(contact_type)
        return datas
