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
import datetime
import json
import pathlib
from itertools import chain

from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django.db.models import Q
from django.db.transaction import atomic

from base.models.academic_year import AcademicYear
from base.models.admission_condition import AdmissionCondition, AdmissionConditionLine
from base.models.education_group import EducationGroup
from base.models.education_group_achievement import EducationGroupAchievement
from base.models.education_group_detailed_achievement import EducationGroupDetailedAchievement
from base.models.education_group_publication_contact import EducationGroupPublicationContact
from base.models.education_group_type import EducationGroupType
from base.models.education_group_year import EducationGroupYear
from base.models.entity import Entity
from base.models.enums.education_group_categories import TRAINING, MINI_TRAINING
from base.models.enums.education_group_types import TrainingType, MiniTrainingType
from base.models.enums.organization_type import MAIN
from cms.models.text_label import TextLabel
from cms.models.translated_text import TranslatedText
from cms.models.translated_text_label import TranslatedTextLabel
from webservices.business import SKILLS_AND_ACHIEVEMENTS_CMS_DATA, SKILLS_AND_ACHIEVEMENTS_KEY, \
    SKILLS_AND_ACHIEVEMENTS_AA_DATA, CONTACTS_KEY

BACHELOR_FIELDS = (
    'alert_message', 'ca_bacs_cond_generales', 'ca_bacs_cond_particulieres', 'ca_bacs_examen_langue',
    'ca_bacs_cond_speciales'
)

COMMON_FIELDS = (
    'alert_message', 'personalized_access', 'admission_enrollment_procedures', 'adults_taking_up_university_training',
    'ca_cond_generales', 'ca_maitrise_fr', 'ca_allegement', 'ca_ouv_adultes'
)

OFFERS = [
    {'name': TrainingType.AGGREGATION.name, 'category': TRAINING, 'code': '2A'},
    {'name': TrainingType.CERTIFICATE_OF_PARTICIPATION.name, 'category': TRAINING, 'code': '8FC'},
    {'name': TrainingType.CERTIFICATE_OF_SUCCESS.name, 'category': TRAINING, 'code': '7FC'},
    {'name': TrainingType.CERTIFICATE_OF_HOLDING_CREDITS.name, 'category': TRAINING, 'code': '9FC'},
    {'name': TrainingType.BACHELOR.name, 'category': TRAINING, 'code': '1BA'},
    {'name': TrainingType.CERTIFICATE.name, 'category': TRAINING, 'code': 'CE'},
    {'name': TrainingType.CAPAES.name, 'category': TRAINING, 'code': '2CE'},
    {'name': TrainingType.RESEARCH_CERTIFICATE.name, 'category': TRAINING, 'code': '3CE'},
    {'name': TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name, 'category': TRAINING, 'code': '1FC'},
    {'name': TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE.name, 'category': TRAINING, 'code': '2FC'},
    {'name': TrainingType.PGRM_MASTER_120.name, 'category': TRAINING, 'code': '2M'},
    {'name': TrainingType.MASTER_M1.name, 'category': TRAINING, 'code': '2M1'},
    {'name': TrainingType.MASTER_MC.name, 'category': TRAINING, 'code': '2MC'},
    {'name': TrainingType.INTERNSHIP.name, 'category': TRAINING, 'code': 'ST'},
    {'name': TrainingType.CERTIFICATE.name, 'category': TRAINING, 'code': '9CE'},
    {'name': MiniTrainingType.DEEPENING.name, 'category': MINI_TRAINING, 'code': ''}
]

COMMON_OFFER = ['1BA', '2A', '2M', '2MC', '']
CONTACTS_ENTITY_KEY = 'contact_entity_code'


def create_common_offer_for_academic_year(year):
    academic_year = AcademicYear.objects.get(year=year)
    for offer in OFFERS:
        code = offer['code'].lower()
        if offer['category'] == TRAINING:
            acronym = 'common-{}'.format(code)
        else:
            acronym = 'common'
        education_group_year = EducationGroupYear.objects.filter(academic_year=academic_year,
                                                                 acronym=acronym)

        if offer['code'] in COMMON_OFFER:
            _update_or_create_common_offer(
                academic_year,
                acronym,
                offer
            )
        else:
            education_group_year.delete()


def _update_or_create_common_offer(academic_year, acronym, offer):
    entity_ucl = Entity.objects.get(entityversion__acronym='UCL', organization__type=MAIN)
    education_group_type = EducationGroupType.objects.get(
        name=offer['name'],
        category=offer['category']
    )

    education_group = EducationGroup.objects.filter(educationgroupyear__acronym=acronym)
    if education_group.count() == 0:
        education_group = EducationGroup.objects.create(
            start_year=2017,
            end_year=None
        )
    else:
        education_group = education_group.first()

    EducationGroupYear.objects.update_or_create(
        academic_year=academic_year,
        education_group=education_group,
        acronym=acronym,
        education_group_type=education_group_type,
        defaults={
            'management_entity': entity_ucl,
            'administration_entity': entity_ucl,
            'title': acronym,
            'title_english': acronym,
            'partial_acronym': acronym
        }
    )


def get_text_label(entity, label):
    """
    Essaie de recuperer un label d'une entité ou simplement la crée si celle-ci n'existe pas.
    """
    if label == 'intro':
        TextLabel.objects.filter(
            entity=entity,
            label=label,
            published=True
        ).delete()
        label = 'welcome_introduction'
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
        if label == SKILLS_AND_ACHIEVEMENTS_KEY:
            _import_skills_and_achievements(value, education_group_year, context)
        elif label == CONTACTS_KEY:
            _import_contacts(value, education_group_year, context)
        elif label == CONTACTS_ENTITY_KEY:
            _import_contact_entity(value, education_group_year)
        else:
            # General CMS data
            TranslatedText.objects.update_or_create(
                entity=context.entity,
                reference=education_group_year.id,
                text_label=mapping_label_text_label[label],
                language=context.language,
                defaults={
                    'text': value
                }
            )


def _import_skills_and_achievements(skills_achievements, education_group_year, context):
    for label, data in skills_achievements.items():
        if label in SKILLS_AND_ACHIEVEMENTS_CMS_DATA:
            text_label = get_text_label(context.entity, label)
            TranslatedText.objects.update_or_create(
                entity=context.entity,
                reference=education_group_year.id,
                text_label=text_label,
                language=context.language,
                defaults={'text': data}
            )
        elif label == SKILLS_AND_ACHIEVEMENTS_AA_DATA:
            _import_general_achievements(
                skills_achievements[SKILLS_AND_ACHIEVEMENTS_AA_DATA],
                education_group_year,
                context,
            )


def _import_general_achievements(achievements, education_group_year, context):
    for idx, achievement in enumerate(achievements):
        field_to_update = _get_field_achievement_according_to_language(context.language)
        education_group_achievement, created = EducationGroupAchievement.objects.update_or_create(
            education_group_year_id=education_group_year.id,
            order=idx,
            defaults={
                'code_name': achievement['code_name'],
                field_to_update: achievement['text']
            }
        )

        if achievement['detailed']:
            _import_detailled_achievements(achievement['detailed'], education_group_achievement, context)


def _import_detailled_achievements(detailled_achievements, education_group_achievement, context):
    for idx, detailled_achievement in enumerate(detailled_achievements):
        field_to_update = _get_field_achievement_according_to_language(context.language)
        EducationGroupDetailedAchievement.objects.update_or_create(
            education_group_achievement=education_group_achievement,
            order=idx,
            defaults={
                'code_name': detailled_achievement['code_name'],
                field_to_update: detailled_achievement['text'],
            }
        )


def _get_field_achievement_according_to_language(language):
    if language == settings.LANGUAGE_CODE_FR:
        return 'french_text'
    elif language == settings.LANGUAGE_CODE_EN:
        return 'english_text'
    raise AttributeError('Language not supported {}'.format(language))


def _import_contacts(contacts_grouped_by_types, education_group_year, context):
    for type, contacts in contacts_grouped_by_types.items():
        _import_single_contacts_type(type, contacts, education_group_year, context.language)


def _import_single_contacts_type(type, contacts, education_group_year, language):
    role_field = _get_role_field_publication_contact_according_to_language(language)
    for idx, contact in enumerate(contacts):
        EducationGroupPublicationContact.objects.update_or_create(
             education_group_year=education_group_year,
             order=idx,
             type=type,
             defaults={
                 role_field: contact.get('title', ''),
                 'email': contact.get('email', ''),
                 'description': contact.get('description', '')
             }
         )


def _get_role_field_publication_contact_according_to_language(language):
    if language == settings.LANGUAGE_CODE_FR:
        return 'role_fr'
    elif language == settings.LANGUAGE_CODE_EN:
        return 'role_en'
    raise AttributeError('Language not supported {}'.format(language))


def _import_contact_entity(entity_acronym, education_group_year):
    try:
        entity = Entity.objects.filter(entityversion__acronym=entity_acronym).distinct().get()
        education_group_year.publication_contact_entity = entity
        education_group_year.save()
    except Entity.DoesNotExist:
        msg = 'Entity {acronym} not found for program: {program}'
        print(msg.format(acronym=entity_acronym, program=education_group_year.acronym))


LABEL_TEXTUALS = [
    (settings.LANGUAGE_CODE_FR, 'pedagogie', 'Pédagogie'),
    (settings.LANGUAGE_CODE_FR, 'mobilite', 'Mobilité'),
    (settings.LANGUAGE_CODE_FR, 'formations_accessibles', 'Formations Accessibles'),
    (settings.LANGUAGE_CODE_FR, 'certificats', 'Certificats'),
    (settings.LANGUAGE_CODE_FR, 'module_complementaire', 'Module Complémentaire'),
    (settings.LANGUAGE_CODE_FR, 'evaluation', 'Évaluation'),
    (settings.LANGUAGE_CODE_FR, 'structure', 'Structure'),
    (settings.LANGUAGE_CODE_FR, 'programme_detaille', 'Programme Détaillé'),
    (settings.LANGUAGE_CODE_FR, 'welcome_introduction', 'Introduction'),
    (settings.LANGUAGE_CODE_FR, 'welcome_job', 'Votre Futur Job'),
    (settings.LANGUAGE_CODE_FR, 'welcome_profil', 'Votre profil'),
    (settings.LANGUAGE_CODE_FR, 'welcome_programme', 'Votre Programme'),
    (settings.LANGUAGE_CODE_FR, 'welcome_parcours', 'Votre Parcours'),
    (settings.LANGUAGE_CODE_FR, 'caap', "Cours et Acquis d'Apprentissage du Programme"),
    (settings.LANGUAGE_CODE_FR, 'acces_professions', 'Accès aux Professions'),
    (settings.LANGUAGE_CODE_FR, 'bacheliers_concernes', 'Bacheliers Concernés'),
    (settings.LANGUAGE_CODE_FR, 'infos_pratiques', 'Informations Pratiques'),
    (settings.LANGUAGE_CODE_FR, 'mineures', 'Mineures'),
    (settings.LANGUAGE_CODE_FR, 'majeures', 'Majeures'),
    (settings.LANGUAGE_CODE_FR, 'finalites', 'Finalités'),
    (settings.LANGUAGE_CODE_FR, 'finalites_didactiques', 'Finalités Didactique'),
    (settings.LANGUAGE_CODE_FR, 'agregation', 'Agrégation'),
    (settings.LANGUAGE_CODE_FR, 'prerequis', 'Prérequis'),
    (settings.LANGUAGE_CODE_FR, 'contact_intro', 'Introduction'),
    (settings.LANGUAGE_CODE_EN, 'pedagogie', 'Pedagogy'),
    (settings.LANGUAGE_CODE_EN, 'mobilite', 'Mobility'),
    (settings.LANGUAGE_CODE_EN, 'formations_accessibles', 'Possible Trainings'),
    (settings.LANGUAGE_CODE_EN, 'certificats', 'Certificates'),
    (settings.LANGUAGE_CODE_EN, 'module_complementaire', 'Supplementary Modules'),
    (settings.LANGUAGE_CODE_EN, 'evaluation', 'Evaluation'),
    (settings.LANGUAGE_CODE_EN, 'structure', 'Structure'),
    (settings.LANGUAGE_CODE_EN, 'programme_detaille', 'Detailed Programme'),
    (settings.LANGUAGE_CODE_EN, 'welcome_introduction', 'Introduction'),
    (settings.LANGUAGE_CODE_EN, 'welcome_job', 'Your Future Job'),
    (settings.LANGUAGE_CODE_EN, 'welcome_profil', 'Your Profile'),
    (settings.LANGUAGE_CODE_EN, 'welcome_programme', 'Your Programme'),
    (settings.LANGUAGE_CODE_EN, 'welcome_parcours', 'Votre Parcours'),
    (settings.LANGUAGE_CODE_EN, 'caap', "The Programme's Courses and Learning Outcomes"),
    (settings.LANGUAGE_CODE_EN, 'acces_professions', 'Accès aux Professions'),
    (settings.LANGUAGE_CODE_EN, 'bacheliers_concernes', 'Concerned Bachelors'),
    (settings.LANGUAGE_CODE_EN, 'infos_pratiques', 'Informations Pratiques'),
    (settings.LANGUAGE_CODE_EN, 'mineures', 'Minors'),
    (settings.LANGUAGE_CODE_EN, 'majeures', 'Majors'),
    (settings.LANGUAGE_CODE_EN, 'finalites', 'Focuses'),
    (settings.LANGUAGE_CODE_EN, 'finalites_didactiques', 'Teaching Focuses'),
    (settings.LANGUAGE_CODE_EN, 'agregation', 'Agregation'),
    (settings.LANGUAGE_CODE_EN, 'prerequis', 'Prerequis'),
    (settings.LANGUAGE_CODE_EN, 'contact_intro', 'Introduction'),
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
        TranslatedTextLabel.objects.update_or_create(
            text_label=text_label,
            language=context.language,
            defaults={'label': find_translated_label(context.language, label)}
        )

        mapping_label_text_label[label] = text_label
    return mapping_label_text_label


def import_common_offer(context, offer, mapping_label_text_label):
    """
    Comme nous recevons une seule offre 'common', nous dispatchons les textes aux offres specifiques communes
    * common-1ba
    * common-2mc
    * ...
    """
    qs = EducationGroupYear.objects.look_for_common(academic_year__year=offer['year'])
    for record in qs:
        import_offer_and_items(offer, record, mapping_label_text_label, context)


def create_offers(context, offers, mapping_label_text_label):
    for offer in offers:
        if offer['type'] == 'common':
            import_common_offer(context, offer, mapping_label_text_label)
        else:
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

    @atomic
    def handle(self, *args, **options):
        path = check_parameters(options['file'])
        self.stdout.write(self.style.SUCCESS('file: {}'.format(path)))
        self.stdout.write(self.style.SUCCESS('language: {}'.format(options['language'])))
        self.stdout.write(self.style.SUCCESS('year: {}'.format(options['year'])))

        self.iso_language = options['language']
        self.json_content = json.loads(path.read_text())
        self.suffix_language = '' if self.iso_language == 'fr-be' else '_en'

        this_year = datetime.date.today().year - 1
        for year in range(this_year, this_year + 6):
            create_common_offer_for_academic_year(year)

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
            'diploma' + self.suffix_language: diploma,
            'conditions' + self.suffix_language: line['conditions'] or '',
            'access': line['access'],
            'remarks' + self.suffix_language: line['remarks']
        }

        queryset = AdmissionConditionLine.objects.filter(section=line['title'],
                                                         admission_condition=admission_condition,
                                                         external_id=line['external_id'])
        if not queryset.count():
            acl = AdmissionConditionLine(
                section=line['title'],
                admission_condition=admission_condition,
                external_id=line['external_id'],
                **fields
            )
            acl.save()
        else:
            acl = queryset.first()
            setattr(acl, 'access', line['access'])
            setattr(acl, 'diploma' + self.suffix_language, diploma)
            setattr(acl, 'conditions' + self.suffix_language, line['conditions'] or '')
            setattr(acl, 'remarks' + self.suffix_language, line['remarks'])
            acl.save()

    def save_text_of_conditions(self, admission_condition, item):
        texts = item['info'].get('texts', {}) or {}
        for key, value in texts.items():
            if not value:
                continue
            if key == 'introduction':
                self.set_admission_condition_value(admission_condition, 'free', value['text'])
            elif key in ('personalized_access', 'admission_enrollment_procedures',
                         'adults_taking_up_university_training'):
                self.set_admission_condition_value(admission_condition, key, value['text'])
            else:
                raise Exception('This case is not handled %s' % key)

    def set_values_for_text_row_of_condition_admission(self, admission_condition, line):
        section = line['section']
        if section in ('non_university_bachelors', 'holders_non_university_second_degree', 'university_bachelors',
                       'holders_second_university_degree'):
            self.set_admission_condition_value(admission_condition, section, line['text'])
        else:
            raise Exception('This case is not handled %s' % section)

    def load_admission_conditions_for_bachelor(self, item, year):
        academic_year = AcademicYear.objects.get(year=year)

        education_group_year = EducationGroupYear.objects.get(
            academic_year=academic_year,
            acronym='common-1ba'
        )

        admission_condition, created = AdmissionCondition.objects.get_or_create(
            education_group_year=education_group_year)

        for text_label in BACHELOR_FIELDS:
            if text_label in item['info']:
                self.set_admission_condition_value(admission_condition, text_label,
                                                   item['info'][text_label]['text-common'])
        admission_condition.save()

    def load_admission_conditions_common(self):
        year = self.json_content.pop('year')

        academic_year = AcademicYear.objects.get(year=year)

        for key, value in self.json_content.items():
            offer_type, text_label = key.split('.')

            if offer_type.upper() in COMMON_OFFER:
                education_group_year = EducationGroupYear.objects.get(
                    academic_year=academic_year,
                    acronym='common-{}'.format(offer_type)
                )

                admission_condition, created = AdmissionCondition.objects.get_or_create(
                    education_group_year=education_group_year)

                if text_label in COMMON_FIELDS:
                    self.set_admission_condition_value(admission_condition, text_label, value)
                elif text_label == 'introduction':
                    self.set_admission_condition_value(admission_condition, 'standard', value)
                else:
                    raise Exception('This case is not handled %s' % text_label)

                admission_condition.save()

    def set_admission_condition_value(self, admission_condition, field, value):
        setattr(admission_condition, 'text_' + field + self.suffix_language, value)
