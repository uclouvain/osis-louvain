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
import collections
import json
import pathlib
from itertools import chain

from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django.db.models import Q

from base.models.academic_year import AcademicYear
from base.models.admission_condition import AdmissionCondition, AdmissionConditionLine
from base.models.education_group_year import EducationGroupYear
from cms.models.text_label import TextLabel
from cms.models.translated_text import TranslatedText
from cms.models.translated_text_label import TranslatedTextLabel


def get_text_label(entity, label):
    """
    Essaie de recuperer un label d'une entité ou simplement la crée si celle-ci n'existe pas.
    """
    text_label, created = TextLabel.objects.get_or_create(
        entity=entity,
        label=label,
        published=True
    )
    return text_label


def import_offer_and_items(item, education_group_year, mapping_label_text_label, context):
    for label, value in item['info'].items():
        if not value:
            continue

        translated_text, created = TranslatedText.objects.get_or_create(
            entity=context.entity,
            reference=education_group_year.id,
            text_label=mapping_label_text_label[label],
            language=context.language,
            defaults={
                'text': value
            }
        )

        if not created:
            translated_text.text = value
            translated_text.save()


LABEL_TEXTUALS = [
    (settings.LANGUAGE_CODE_FR, 'comp_acquis', 'Compétences et Acquis'),
    (settings.LANGUAGE_CODE_FR, 'pedagogie', 'Pédagogie'),
    (settings.LANGUAGE_CODE_FR, 'contacts', 'Contacts'),
    (settings.LANGUAGE_CODE_FR, 'mobilite', 'Mobilité'),
    (settings.LANGUAGE_CODE_FR, 'formations_accessibles', 'Formations Accessibles'),
    (settings.LANGUAGE_CODE_FR, 'certificats', 'Certificats'),
    (settings.LANGUAGE_CODE_FR, 'module_complementaire', 'Module Complémentaire'),
    (settings.LANGUAGE_CODE_FR, 'evaluation', 'Évaluation'),
    (settings.LANGUAGE_CODE_FR, 'structure', 'Structure'),
    (settings.LANGUAGE_CODE_FR, 'programme_detaille', 'Programme Détaillé'),
]

MAPPING_LABEL_TEXTUAL = collections.defaultdict(dict)

for language, key, term in LABEL_TEXTUALS:
    MAPPING_LABEL_TEXTUAL[language][key] = term


def find_translated_label(language, label):
    if language in MAPPING_LABEL_TEXTUAL and label in MAPPING_LABEL_TEXTUAL[language]:
        return MAPPING_LABEL_TEXTUAL[language][label]
    else:
        return label.title()


def get_mapping_label_texts(context, labels):
    mapping_label_text_label = {}
    for label in labels:
        text_label = get_text_label(context.entity, label)

        records = TranslatedTextLabel.objects.filter(text_label=text_label, language=context.language)
        if not records.count():
            TranslatedTextLabel.objects.create(
                text_label=text_label,
                language=context.language,
                label=find_translated_label(context.language, label))

        mapping_label_text_label[label] = text_label
    return mapping_label_text_label


def create_offers(context, offers, mapping_label_text_label):
    for offer in offers:
        import_offer(context, offer, mapping_label_text_label)


def import_offer(context, offer, mapping_label_text_label):
    if 'info' not in offer:
        return None

    qs = EducationGroupYear.objects.filter(
        Q(acronym__iexact=offer['acronym']) | Q(partial_acronym__iexact=offer['acronym']),
        academic_year__year=offer['year']
    )

    if not qs.exists():
        return

    egy = qs.first()

    import_offer_and_items(offer, egy, mapping_label_text_label, context)


def check_parameters(filename):
    path = pathlib.Path(filename)
    if not path.exists():
        raise CommandError('The file {} does not exist'.format(filename))

    return path


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('file', type=str)
        parser.add_argument('year', type=int)
        parser.add_argument('--language', type=str, default='fr-be',
                            choices=list(dict(settings.LANGUAGES).keys()))
        parser.add_argument('--conditions', action='store_true', dest='is_conditions',
                            help='Import the condition terms')
        parser.add_argument('--common', action='store_true', dest='is_common',
                            help='Import the common terms for the conditions')

    def handle(self, *args, **options):
        path = check_parameters(options['file'])
        self.stdout.write(self.style.SUCCESS('file: {}'.format(path)))
        self.stdout.write(self.style.SUCCESS('language: {}'.format(options['language'])))
        self.stdout.write(self.style.SUCCESS('year: {}'.format(options['year'])))

        self.iso_language = options['language']
        self.json_content = json.loads(path.read_text())
        self.lang = '' if self.iso_language == 'fr-be' else '_en'

        if options['is_conditions']:
            self.load_admission_conditions()
        elif options['is_common']:
            self.load_admission_conditions_common()
        else:
            self.load_offers()

        self.stdout.write(self.style.SUCCESS('records imported!'))

    def load_offers(self):
        labels = set(chain.from_iterable(o.get('info', {}).keys() for o in self.json_content))

        Context = collections.namedtuple('Context', 'entity language')
        context = Context(entity='offer_year', language=self.iso_language)

        mapping_label_text_label = get_mapping_label_texts(context, labels)

        create_offers(context, self.json_content, mapping_label_text_label)

    def load_admission_conditions(self):
        for item in self.json_content:
            year = item['year']
            acronym = item['acronym']

            if acronym == 'bacs':
                self.load_admission_conditions_for_bachelor(item, year)
            else:
                self.load_admission_conditions_generic(acronym, item, year)

    def load_admission_conditions_generic(self, acronym, item, year):
        filters = (Q(academic_year__year=year),
                   Q(acronym__iexact=acronym) | Q(partial_acronym__iexact=acronym))
        records = EducationGroupYear.objects.filter(*filters)
        if not records:
            self.stderr.write(self.style.WARNING("unknown acronym: {}".format(acronym)))
        else:
            education_group_year = records.first()
            admission_condition, created = AdmissionCondition.objects.get_or_create(
                education_group_year=education_group_year)

            self.save_diplomas(admission_condition, item)
            self.save_text_of_conditions(admission_condition, item)

            admission_condition.save()

    def save_diplomas(self, admission_condition, item):
        lines = item['info'].get('diplomas', []) or []
        for line in lines:
            if line['type'] == 'table':
                self.save_condition_line_of_row(admission_condition, line)
            elif line['type'] == 'text':
                self.set_values_for_text_row_of_condition_admission(admission_condition, line)

    def save_condition_line_of_row(self, admission_condition, line):
        diploma = '\n'.join(map(str.strip, line['diploma'].splitlines()))
        fields = {
            'diploma' + self.lang: diploma,
            'conditions' + self.lang: line['conditions'] or '',
            'access' + self.lang: line['access'],
            'remarks' + self.lang: line['remarks']
        }

        queryset = AdmissionConditionLine.objects.filter(section=line['title'],
                                                         admission_condition=admission_condition,
                                                         external_id=line['external_id'])
        if not queryset.count():
            AdmissionConditionLine.objects.create(
                section=line['title'],
                admission_condition=admission_condition,
                external_id=line['external_id'],
                **fields
            )
        else:
            acl = queryset.first()
            setattr(acl, 'diploma' + self.lang, diploma)
            setattr(acl, 'conditions' + self.lang, line['conditions'] or '')
            setattr(acl, 'access' + self.lang, line['access'])
            setattr(acl, 'remarks' + self.lang, line['remarks'])
            acl.save()

    def save_text_of_conditions(self, admission_condition, item):
        texts = item['info'].get('texts', {}) or {}
        for key, value in texts.items():
            if not value:
                continue
            if key == 'introduction':
                self.set_admission_condition_value(admission_condition, 'standard', value['text'])
            elif key in ('personalized_access', 'admission_enrollment_procedures',
                         'adults_taking_up_university_training'):
                self.set_admission_condition_value(admission_condition, key, value['text'])
            else:
                raise Exception('This case is not handled')

    def set_values_for_text_row_of_condition_admission(self, admission_condition, line):
        section = line['section']
        if section in ('non_university_bachelors', 'holders_non_university_second_degree', 'university_bachelors',
                       'holders_second_university_degree'):
            self.set_admission_condition_value(admission_condition, section, line['text'])
        else:
            raise Exception('This case is not handled')

    def load_admission_conditions_for_bachelor(self, item, year):
        academic_year = AcademicYear.objects.get(year=year)
        education_group_year_common = EducationGroupYear.objects.get(
            academic_year=academic_year,
            acronym='common'
        )
        education_group_year, created = EducationGroupYear.objects.get_or_create(
            academic_year=academic_year,
            acronym='common-bacs',
            education_group=education_group_year_common.education_group
        )
        admission_condition, created = AdmissionCondition.objects.get_or_create(
            education_group_year=education_group_year)
        self.set_admission_condition_value(admission_condition, 'bachelor', item['info']['text'])
        admission_condition.save()

    def load_admission_conditions_common(self):
        year = self.json_content.pop('year')
        education_group_year_common = EducationGroupYear.objects.get(
            academic_year__year=year,
            acronym='common'
        )

        academic_year = AcademicYear.objects.get(year=year)

        for key, value in self.json_content.items():
            offer_type, text_label = key.split('.')

            education_group_year, created = EducationGroupYear.objects.get_or_create(
                academic_year=academic_year,
                acronym='common-{}'.format(offer_type),
                education_group=education_group_year_common.education_group
            )

            admission_condition, created = AdmissionCondition.objects.get_or_create(
                education_group_year=education_group_year)

            if text_label in ('alert_message', 'personalized_access', 'admission_enrollment_procedures',
                              'adults_taking_up_university_training'):
                self.set_admission_condition_value(admission_condition, text_label, value)
            elif text_label == 'introduction':
                self.set_admission_condition_value(admission_condition, 'standard', value)
            else:
                raise Exception('This case is not handled')

            admission_condition.save()

    def set_admission_condition_value(self, admission_condition, field, value):
        setattr(admission_condition, 'text_' + field + self.lang, value)
