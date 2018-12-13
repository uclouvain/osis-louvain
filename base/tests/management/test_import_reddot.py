import collections
import datetime
from unittest import mock

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned
from django.test import TestCase

from base.management.commands import import_reddot
from base.management.commands.import_reddot import _import_skills_and_achievements, \
    _get_field_achievement_according_to_language, _get_role_field_publication_contact_according_to_language, \
    _import_contacts, _import_contact_entity, CONTACTS_ENTITY_KEY, import_offer_and_items
from base.models.enums import organization_type
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from cms.models.text_label import TextLabel
from cms.models.translated_text_label import TranslatedTextLabel
from base.models.education_group_publication_contact import EducationGroupPublicationContact
from base.models.enums.publication_contact_type import PublicationContactType
from webservices.business import SKILLS_AND_ACHIEVEMENTS_CMS_DATA
from base.models.admission_condition import AdmissionCondition, AdmissionConditionLine, CONDITION_ADMISSION_ACCESSES
from base.models.education_group import EducationGroup
from base.models.education_group_achievement import EducationGroupAchievement
from base.models.education_group_detailed_achievement import EducationGroupDetailedAchievement
from base.models.education_group_type import EducationGroupType
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_categories import TRAINING
from base.models.enums.education_group_types import TrainingType
from base.models.enums.organization_type import MAIN
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group import EducationGroupFactory
from base.tests.factories.education_group_year import (
    EducationGroupYearFactory,
    EducationGroupYearCommonMasterFactory,
    EducationGroupYearCommonBachelorFactory,
    EducationGroupYearMasterFactory)
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from cms.enums import entity_name
from cms.models.translated_text import TranslatedText

OFFERS = [
    {'name': TrainingType.BACHELOR.name, 'category': TRAINING, 'code': '1BA'},
    {'name': TrainingType.PGRM_MASTER_120.name, 'category': TRAINING, 'code': '2M'},
    {'name': TrainingType.MASTER_M1.name, 'category': TRAINING, 'code': '2M1'},
]


class ImportReddotTestCase(TestCase):
    def setUp(self):
        self.command = import_reddot.Command()
        lang = 'fr-be'
        self.command.suffix_language = '' if lang == 'fr-be' else '_en'
        self.command.iso_language = 'fr-be'

    @mock.patch('base.management.commands.import_reddot.get_mapping_label_texts')
    def test_load_offers_call_get_mapping(self, mock_get_mapping):
        item = [
                {
                    "type": "common",
                    "acronym": "common",
                    "year": 2018,
                    "info": {
                        "caap": "TEST",
                        "evaluation": "TESTBIS"
                    }
                },
            ]

        self.command.json_content = item
        self.command.load_offers()
        labels = {'evaluation', 'caap'}
        Context = collections.namedtuple('Context', 'entity language')
        context = Context(entity='offer_year', language=self.command.iso_language)
        mock_get_mapping.assert_called_with(context, labels)

    def test_get_mapping_text_labels(self):
        labels = {'evaluation'}
        Context = collections.namedtuple('Context', 'entity language')
        context = Context(entity='offer_year', language=self.command.iso_language)
        from base.management.commands.import_reddot import get_mapping_label_texts
        result = get_mapping_label_texts(context, labels)
        text_label = TextLabel.objects.filter(
            entity='offer_year',
            label='evaluation',
            published=True
        )
        self.assertTrue(text_label.exists())

        self.assertEqual(result['evaluation'], text_label.first())

    def test_load_admission_conditions_for_bachelor(self):
        education_group_year_common = EducationGroupYearCommonBachelorFactory()
        item = {
            'year': education_group_year_common.academic_year.year,
            'acronym': '1ba',
            'info': {
                'alert_message': {'text-common': 'Alert Message'},
                'ca_bacs_cond_generales': {'text-common': 'General Conditions'},
                'ca_bacs_cond_particulieres': {'text-common': 'Specific Conditions'},
                'ca_bacs_examen_langue': {'text-common': 'Language Exam'},
                'ca_bacs_cond_speciales': {'text-common': 'Special Conditions'},
            }
        }

        self.command.load_admission_conditions_for_bachelor(
            item,
            education_group_year_common.academic_year.year
        )

        common_bacs = EducationGroupYear.objects.filter(
            academic_year=education_group_year_common.academic_year,
            acronym='common-1ba'
        ).first()

        admission_condition = AdmissionCondition.objects.get(education_group_year=common_bacs)
        info = item['info']
        self.assertEqual(admission_condition.text_alert_message,
                         info['alert_message']['text-common'])
        self.assertEqual(admission_condition.text_ca_bacs_cond_generales,
                         info['ca_bacs_cond_generales']['text-common'])
        self.assertEqual(admission_condition.text_ca_bacs_cond_particulieres,
                         info['ca_bacs_cond_particulieres']['text-common'])
        self.assertEqual(admission_condition.text_ca_bacs_examen_langue,
                         info['ca_bacs_examen_langue']['text-common'])
        self.assertEqual(admission_condition.text_ca_bacs_cond_speciales,
                         info['ca_bacs_cond_speciales']['text-common'])

    def test_load_admission_conditions_generic(self):
        item = {
            "acronym": "sged2mc",
            "year": 2018,
            "type": "offer",
            "info": {
                "diplomas": [
                    {
                        "external_id": "id",
                        "section": "university_bachelors",
                        "title": "ucl_bachelors",
                        "type": "table",
                        "diploma": "Bachelier en théologie ou en sciences religieuses",
                        "conditions": "COND",
                        "access": "direct_access",
                        "remarks": "REM"
                    }
                ],
                "texts": {
                    "alert_message": {},
                    "introduction": {
                        "text": "TestText"
                    },
                    "ca_cond_generales": {}
                }
            }
        }
        education_group_year = EducationGroupYearFactory()
        self.command.load_admission_conditions_generic(
            education_group_year.acronym,
            item,
            education_group_year.academic_year.year
        )

        edy = EducationGroupYear.objects.filter(
            academic_year=education_group_year.academic_year,
            acronym=education_group_year.acronym
        ).first()

        admission_condition = AdmissionCondition.objects.get(education_group_year=edy)
        info = item['info']
        line = AdmissionConditionLine.objects.get(admission_condition=admission_condition)
        self.assertEqual(admission_condition.text_free,
                         info['texts']['introduction']['text'])
        self.assertEqual(line.section,
                         info['diplomas'][0]['title'])
        self.assertEqual(line.external_id,
                         info['diplomas'][0]['external_id'])
        self.assertEqual(line.access,
                         info['diplomas'][0]['access'])
        self.assertEqual(line.diploma,
                         info['diplomas'][0]['diploma'])
        self.assertEqual(line.conditions,
                         info['diplomas'][0]['conditions'])
        self.assertEqual(line.remarks,
                         info['diplomas'][0]['remarks'])

    def test_load_admission_conditions_common(self):
        item = {
            "year": 2018,
            "2m.alert_message": "Test",
            "2m.introduction": "IntroTest"
        }
        self.command.json_content = item
        academic_year = AcademicYearFactory(year=2018)
        education_group_year_common = EducationGroupYearFactory(
            academic_year=academic_year,
            acronym='common-2m'
        )
        self.command.load_admission_conditions_common()

        common = EducationGroupYear.objects.filter(
            academic_year=education_group_year_common.academic_year,
            acronym='common-2m'
        ).first()

        admission_condition = AdmissionCondition.objects.get(education_group_year=common)
        self.assertEqual(admission_condition.text_alert_message,
                         item['2m.alert_message'])

    def test_load_admission_conditions_common_label_not_handled(self):
        item = {
            "year": 2018,
            "2m.coucou": "Test"
        }
        self.command.json_content = item
        academic_year = AcademicYearFactory(year=2018)
        education_group_year_common = EducationGroupYearFactory(
            academic_year=academic_year,
            acronym='common-2m'
        )

        with self.assertRaises(Exception):
            self.command.load_admission_conditions_common()

    def test_save_condition_line_of_row_with_no_admission_condition_line(self):
        education_group_year = EducationGroupYearFactory()

        admission_condition = AdmissionCondition.objects.create(education_group_year=education_group_year)

        self.assertEqual(AdmissionConditionLine.objects.filter(admission_condition=admission_condition).count(), 0)

        line = {
            'type': 'table',
            'title': 'ucl_bachelors',
            'diploma': 'Diploma',
            'conditions': 'Conditions',
            'access': CONDITION_ADMISSION_ACCESSES[2][0],
            'remarks': 'Remarks',
            'external_id': '1234567890'
        }
        self.command.save_condition_line_of_row(admission_condition, line)

        queryset = AdmissionConditionLine.objects.filter(admission_condition=admission_condition)
        self.assertEqual(queryset.count(), 1)

        admission_condition_line = queryset.first()

        self.assertEqual(admission_condition_line.diploma, line['diploma'])
        self.assertEqual(admission_condition_line.conditions, line['conditions'])
        self.assertEqual(admission_condition_line.access, line['access'])
        self.assertEqual(admission_condition_line.remarks, line['remarks'])

    def test_save_condition_line_of_row_with_admission_condition_line(self):
        education_group_year = EducationGroupYearFactory()

        line = {
            'type': 'table',
            'title': 'ucl_bachelors',
            'diploma': 'Diploma',
            'conditions': 'Conditions',
            'access': CONDITION_ADMISSION_ACCESSES[2][0],
            'remarks': 'Remarks',
            'external_id': '1234567890'
        }

        admission_condition = AdmissionCondition.objects.create(education_group_year=education_group_year)

        queryset = AdmissionConditionLine.objects.filter(admission_condition=admission_condition)
        self.assertEqual(queryset.count(), 0)

        acl = AdmissionConditionLine.objects.create(admission_condition=admission_condition,
                                                    section=line['title'],
                                                    external_id=line['external_id'])
        self.assertEqual(queryset.count(), 1)

        self.command.save_condition_line_of_row(admission_condition, line)

        queryset = AdmissionConditionLine.objects.filter(admission_condition=admission_condition)
        self.assertEqual(queryset.count(), 1)

        admission_condition_line = queryset.first()

        self.assertEqual(admission_condition_line.diploma, line['diploma'])
        self.assertEqual(admission_condition_line.conditions, line['conditions'])
        self.assertEqual(admission_condition_line.access, line['access'])
        self.assertEqual(admission_condition_line.remarks, line['remarks'])

    @mock.patch('base.management.commands.import_reddot.Command.load_admission_conditions_for_bachelor')
    @mock.patch('base.management.commands.import_reddot.Command.load_admission_conditions_generic')
    def test_load_admission_conditions(self, mock_generic, mock_bachelor):
        self.command.json_content = [{'year': 2018, 'acronym': 'bacs'}, {'year': 2018, 'acronym': 'actu2m'}]
        self.command.load_admission_conditions()

        mock_bachelor.assert_called_with({'year': 2018, 'acronym': 'bacs'}, 2018)
        mock_generic.assert_called_with('actu2m', {'year': 2018, 'acronym': 'actu2m'}, 2018)

    def test_set_values_for_text_row_of_condition_admission_raise_exception(self):
        with self.assertRaises(Exception):
            line = {'section': 'demo'}
            self.command.set_values_for_text_row_of_condition_admission(None, line)

    def test_set_values_for_text_row_of_condition_admission(self):
        line = {'section': 'non_university_bachelors', 'text': 'Text'}
        with mock.patch('base.management.commands.import_reddot.Command.set_admission_condition_value'):
            self.command.set_values_for_text_row_of_condition_admission(None, line)

    @mock.patch('base.management.commands.import_reddot.Command.set_admission_condition_value')
    def test_save_text_of_conditions(self, mock_set_admission):
        item = {
            'info': {
                'texts': {
                    'introduction': {'text': 'Introduction'},
                }
            }
        }
        education_group_year = EducationGroupYearFactory()
        admission_condition = AdmissionCondition.objects.create(education_group_year=education_group_year)
        self.command.save_text_of_conditions(admission_condition, item)

        mock_set_admission.assert_called_with(admission_condition, 'free', 'Introduction')

    @mock.patch('base.management.commands.import_reddot.Command.set_admission_condition_value')
    def test_save_text_of_conditions_personalized_access(self, mock_set_admission):
        item = {
            'info': {
                'texts': {
                    'personalized_access': {'text': 'Personalized Access'}
                }
            }
        }
        education_group_year = EducationGroupYearFactory()
        admission_condition = AdmissionCondition.objects.create(education_group_year=education_group_year)
        self.command.save_text_of_conditions(admission_condition, item)

        mock_set_admission.assert_called_with(admission_condition, 'personalized_access', 'Personalized Access')

    @mock.patch('base.management.commands.import_reddot.Command.set_admission_condition_value')
    def test_save_text_of_conditions_not_called(self, mock_set_admission):
        item = {
            'info': {
                'texts': {
                    'test': None,
                }
            }
        }
        education_group_year = EducationGroupYearFactory()
        admission_condition = AdmissionCondition.objects.create(education_group_year=education_group_year)
        self.command.save_text_of_conditions(admission_condition, item)

        mock_set_admission.assert_not_called()

    @mock.patch('base.management.commands.import_reddot.Command.set_admission_condition_value')
    def test_save_text_of_conditions_raise_exception(self, mock_set_admission):
        item = {
            'info': {
                'texts': {
                    'test': 'something',
                }
            }
        }
        education_group_year = EducationGroupYearFactory()
        admission_condition = AdmissionCondition.objects.create(education_group_year=education_group_year)
        with self.assertRaises(Exception):
            self.command.save_text_of_conditions(admission_condition, item)

    @mock.patch('base.management.commands.import_reddot.Command.save_condition_line_of_row')
    @mock.patch('base.management.commands.import_reddot.Command.set_values_for_text_row_of_condition_admission')
    def test_save_diplomas(self, mock_set_values, mock_save_condition):
        item = {'info': {'diplomas': [{'type': 'table'}, {'type': 'text'}]}}
        self.command.save_diplomas(None, item)
        mock_save_condition.assert_called_with(None, {'type': 'table'})
        mock_set_values.assert_called_with(None, {'type': 'text'})

    @mock.patch('base.management.commands.import_reddot.import_offer_and_items')
    def test_import_common_offer(self, mocker):
        education_group_year_list = [EducationGroupYearCommonMasterFactory()]
        from base.management.commands.import_reddot import import_common_offer
        context = None
        offer = {'year': education_group_year_list[0].academic_year.year}
        import_common_offer(context, offer, None)
        mocker.assert_called_with(offer, education_group_year_list[0], None, context)

    @mock.patch('base.management.commands.import_reddot.import_offer_and_items')
    def test_import_offer(self, mocker):
        education_group_year_list = [EducationGroupYearFactory()]
        from base.management.commands.import_reddot import import_offer
        context = None
        offer = {
            'year': education_group_year_list[0].academic_year.year,
            'info': "",
            'acronym': education_group_year_list[0].acronym
        }
        import_offer(context, offer, None)
        mocker.assert_called_with(offer, education_group_year_list[0], None, context)


@mock.patch('base.management.commands.import_reddot.OFFERS', OFFERS)
class CreateCommonOfferForAcademicYearTest(TestCase):
    def test_with_existing_education_group_year(self):
        academic_year = AcademicYearFactory()
        self.assertEqual(EducationGroup.objects.count(), 0)

        entity = EntityFactory(organization__type=MAIN)
        entity_version = EntityVersionFactory(acronym='UCL', entity=entity)
        from base.management.commands.import_reddot import OFFERS
        for offer in OFFERS:
            EducationGroupType.objects.create(name=offer['name'], category=offer['category'])

        from base.management.commands.import_reddot import create_common_offer_for_academic_year
        self.assertEqual(EducationGroupYear.objects.count(), 0)
        create_common_offer_for_academic_year(academic_year.year)
        self.assertEqual(EducationGroupYear.objects.count(), 2)

    def test_without_education_group_year(self):
        academic_year = AcademicYearFactory()
        self.assertEqual(EducationGroup.objects.count(), 0)

        entity = EntityFactory(organization__type=MAIN)
        entity_version = EntityVersionFactory(acronym='UCL', entity=entity)
        from base.management.commands.import_reddot import OFFERS
        for offer in OFFERS:
            EducationGroupType.objects.create(name=offer['name'], category=offer['category'])

        from base.management.commands.import_reddot import create_common_offer_for_academic_year
        education_group = EducationGroupFactory(start_year=academic_year.year, end_year=academic_year.year + 1)
        self.assertEqual(EducationGroupYear.objects.count(), 0)
        EducationGroupYearCommonMasterFactory(academic_year=academic_year)
        self.assertEqual(EducationGroupYear.objects.count(), 1)
        create_common_offer_for_academic_year(academic_year.year)
        self.assertEqual(EducationGroupYear.objects.count(), 2)

    def test_with_common_to_remove(self):
        academic_year = AcademicYearFactory()
        self.assertEqual(EducationGroup.objects.count(), 0)
        self.assertEqual(EducationGroupYear.objects.count(), 0)
        type_m1 = EducationGroupTypeFactory(
            name=TrainingType.MASTER_M1
        )
        EducationGroupYearMasterFactory(
            acronym='common-2m1',
            academic_year=academic_year,
            education_group_type=type_m1,
            partial_acronym='common-2m1'
        )
        entity = EntityFactory(organization__type=MAIN)
        entity_version = EntityVersionFactory(acronym='UCL', entity=entity)
        from base.management.commands.import_reddot import OFFERS
        for offer in OFFERS:
            EducationGroupType.objects.create(name=offer['name'], category=offer['category'])

        from base.management.commands.import_reddot import create_common_offer_for_academic_year
        self.assertEqual(EducationGroupYear.objects.count(), 1)
        create_common_offer_for_academic_year(academic_year.year)
        self.assertEqual(EducationGroupYear.objects.count(), 2)


class CreateOffersTest(TestCase):
    @mock.patch('base.management.commands.import_reddot.import_common_offer')
    def test_import_common_offer(self, mock_import_offer):
        context, offers = None, [{'type': 'common'}]
        from base.management.commands.import_reddot import create_offers
        create_offers(context, offers, None)
        mock_import_offer.assert_called_with(None, offers[0], None)

    @mock.patch('base.management.commands.import_reddot.import_offer')
    def test_import_offer(self, mock_import_offer):
        context, offers = None, [{'type': 'not-common'}]
        from base.management.commands.import_reddot import create_offers
        create_offers(context, offers, None)
        mock_import_offer.assert_called_with(None, offers[0], None)


class ImportSkillsAndAchievementsTest(TestCase):
    def setUp(self):
        self.achivements_json = {
            "skills_and_achievements_introduction": 'Text skills_and_achievements_introduction',
            "achievements": [
                {
                    "code_name": 1,
                    "text": 'General Education Group Achievement',
                    "detailed": [
                        {"code_name": 1, "text": 'Detailed Education Group Achievement n°1'},
                        {"code_name": 2, "text": 'Detailed Education Group Achievement n°2'},
                    ]
                }
            ],
            "skills_and_achievements_additional_text": "Text skills_and_achievements_additional_text",
        }
        self.education_group_year = EducationGroupYearFactory()

        Context = collections.namedtuple('Context', 'entity language')
        self.context = Context(entity='offer_year', language='en')

    def test_import_skills_and_achievements(self):
        _import_skills_and_achievements(self.achivements_json, self.education_group_year, self.context)

        # Ensure that data is correctly imported [CMS]
        for label_name in SKILLS_AND_ACHIEVEMENTS_CMS_DATA:
            self.assertTrue(
                TranslatedText.objects.filter(
                    text_label__label=label_name,
                    entity=entity_name.OFFER_YEAR,
                    reference=self.education_group_year.pk,
                    text=self.achivements_json[label_name],
                    language=self.context.language
                ).exists()
            )

        # AA Education group year
        qs_achievements = EducationGroupAchievement.objects.filter(education_group_year=self.education_group_year)
        self.assertEqual(qs_achievements.count(), 1)
        achievement = qs_achievements.first()
        self.assertEqual(achievement.english_text, self.achivements_json["achievements"][0]['text'])
        self.assertIsNone(achievement.french_text)

        self.assertEqual(
            EducationGroupDetailedAchievement.objects.filter(education_group_achievement=achievement).count(),
            2
        )

    def test_get_field_achievement_according_to_language(self):
        self.assertEqual(_get_field_achievement_according_to_language(settings.LANGUAGE_CODE_FR), 'french_text')
        self.assertEqual(_get_field_achievement_according_to_language(settings.LANGUAGE_CODE_EN), 'english_text')

        # Language not supported
        with self.assertRaises(AttributeError):
            _get_field_achievement_according_to_language('es')


class ImportContactsTest(TestCase):
    def setUp(self):
        self.contacts_json = {
            "ACADEMIC_RESPONSIBLE": [
                {"email": "academic-responsible-1@osis.com", "description": ""},
                {"email": "academic-responsible-2@osis.com", "description": ""},
                {"email": "academic-responsible-3@osis.com", "description": ""},
            ],
            "JURY_MEMBER": [
                {"title": "Président de jury", "email": "president@osis.com", "description": ""},
                {"title": "Secrétaire", "email": "secretaire@osis.com"},
            ],
            "OTHER_CONTACT": [
                {"title": "Personne de contact de la 1re année de bachelier", "email": "contact-1@osis.com"},
                {"title": "Personne de contact des 2e et 3e années de bachelier", "email": "contact-2@osis.com"},
            ],
            "OTHER_ACADEMIC_RESPONSIBLE": []
        }
        self.education_group_year = EducationGroupYearFactory()

        Context = collections.namedtuple('Context', 'entity language')
        self.context = Context(entity='offer_year', language='fr-be')

    def test_import_contacts_case_academic_responsibles(self):
        _import_contacts(self.contacts_json, self.education_group_year, self.context)

        for idx, academic_responsible in enumerate(self.contacts_json["ACADEMIC_RESPONSIBLE"]):
            self.assertTrue(
                EducationGroupPublicationContact.objects.filter(
                    education_group_year=self.education_group_year,
                    type=PublicationContactType.ACADEMIC_RESPONSIBLE.name,
                    order=idx,
                    role_fr='',
                    role_en='',
                    email=academic_responsible['email'],
                    description=academic_responsible['description']
                ).exists()
            )

    def test_import_contacts_case_jury_members(self):
        _import_contacts(self.contacts_json, self.education_group_year, self.context)

        for idx, jury_member in enumerate(self.contacts_json["JURY_MEMBER"]):
            self.assertTrue(
                EducationGroupPublicationContact.objects.filter(
                    education_group_year=self.education_group_year,
                    type=PublicationContactType.JURY_MEMBER.name,
                    order=idx,
                    role_fr=jury_member['title'],
                    role_en='',
                    email=jury_member['email'],
                    description=jury_member.get('description', '')
                ).exists()
            )

    def test_get_role_field_achievement_according_to_language(self):
        self.assertEqual(
            _get_role_field_publication_contact_according_to_language(settings.LANGUAGE_CODE_FR),
            'role_fr',
        )
        self.assertEqual(
            _get_role_field_publication_contact_according_to_language(settings.LANGUAGE_CODE_EN),
            'role_en',
        )

        # Language not supported
        with self.assertRaises(AttributeError):
            _get_role_field_publication_contact_according_to_language('es')


class ImportOfferAndItems(TestCase):
    def setUp(self):
        self.education_group_year = EducationGroupYearFactory()
        Context = collections.namedtuple('Context', 'entity language')
        self.context = Context(entity='offer_year', language='fr-be')

    @mock.patch('base.management.commands.import_reddot._import_contact_entity')
    def test_import_offer_and_items_case_import_contacts_entity(self, mock_import_contact_entity):
        json_data = {'info': {CONTACTS_ENTITY_KEY: 'AGRO'}}

        import_offer_and_items(json_data, self.education_group_year, {}, self.context)
        self.assertTrue(mock_import_contact_entity.called)


class ImportContactsEntityTest(TestCase):
    def setUp(self):
        self.entity = EntityFactory(organization__type=organization_type.MAIN)
        today = datetime.date.today()
        self.entity_version = EntityVersionFactory(
            start_date=today.replace(year=1900),
            end_date=None,
            entity=self.entity,
        )
        self.education_group_year = EducationGroupYearFactory(
            publication_contact_entity=None
        )

    def test_import_contacts_entity_case_acronym_found(self):
        _import_contact_entity(self.entity_version.acronym, self.education_group_year)

        self.education_group_year.refresh_from_db()
        self.assertEqual(self.education_group_year.publication_contact_entity, self.entity)

    def test_import_contacts_entity_case_acronym_not_found(self):
        _import_contact_entity('DUMMY-ACRONYM', self.education_group_year)

        self.education_group_year.refresh_from_db()
        self.assertIsNone(self.education_group_year.publication_contact_entity)

    def test_import_contacts_entity_case_muliple_acronym_found(self):
        # Create a duplicate entity version [same acronym]
        today = datetime.date.today()
        EntityVersionFactory(
            start_date=today.replace(year=1900),
            end_date=None,
            entity=EntityFactory(organization__type=organization_type.MAIN),
            acronym=self.entity_version.acronym
        )

        with self.assertRaises(MultipleObjectsReturned):
            _import_contact_entity(self.entity_version.acronym, self.education_group_year)

        self.education_group_year.refresh_from_db()
        self.assertIsNone(self.education_group_year.publication_contact_entity)
