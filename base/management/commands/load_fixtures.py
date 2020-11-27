#!/usr/bin/env python
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def _load_osis_data(self):

        list_json_data = [
            'group',
            'user',
            'academic_year',
            'academic_calendar',
            'currency',
            'continent',
            'country',
            'decree',
            'language',
            'person',
            'person_address',
            'organization',
            'campus',
            'education_group',
            'offer_type',
            'education_group_type',
            'education_group_year',
            'entity',
            'entity_version',
            'learning_container',
            'learning_container_year',
            'learning_component_year',
            'entity_container_year',
            'entity_component_year',
            'structure',
            'structure_address',
            'entity_manager',
            'learning_unit',
            'learning_unit_year',
            'student',
            'offer',
            'offer_year',
            'offer_year_calendar',
            'offer_year_entity',
            'grade_type',
            'offer_enrollment',
            'learning_unit_enrollment',
            'group_element_year',
            'learning_class_year',
            'learning_unit_component',
            'learning_unit_component_class',
            'session_exam',
            'exam_enrollment',
            'domain',
            'external_offer',
            'offer_year_domain',
            'tutor',
            'attribution',
            'attribution_charge',
            'program_manager',
            'session_exam_calendar',
            'session_exam_deadline',
            'message_template',
            'text_label',
            'translated_text',
            'translated_text_label'
        ]

        for json_file in list_json_data:
            call_command('loaddata', "{}.json".format(json_file))

    def handle(self, *args, **options):
        self._load_osis_data()


