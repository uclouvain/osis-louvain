##############################################################################
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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from unittest import mock

from django.test import TestCase, SimpleTestCase
from django.test.utils import override_settings
from django.utils.translation import gettext_lazy as _

from base.models.enums import education_group_types
from base.models.enums.constraint_type import ConstraintTypeEnum
from base.models.enums.education_group_types import TrainingType, MiniTrainingType, GroupType
from base.models.enums.publication_contact_type import PublicationContactType
from base.tests.factories.academic_year import get_current_year, AcademicYearFactory
from base.tests.factories.education_group_publication_contact import EducationGroupPublicationContactFactory
from base.tests.factories.education_group_type import MiniTrainingEducationGroupTypeFactory
from education_group.ddd.domain.group import GroupIdentity
from education_group.ddd.domain.mini_training import MiniTrainingIdentity
from education_group.tests.ddd.factories.academic_partner import AcademicPartnerFactory
from education_group.tests.ddd.factories.address import AddressFactory
from education_group.tests.ddd.factories.co_graduation import CoGraduationFactory
from education_group.tests.ddd.factories.co_organization import CoorganizationFactory
from education_group.tests.ddd.factories.content_constraint import ContentConstraintFactory
from education_group.tests.ddd.factories.diploma import DiplomaFactory, DiplomaAimFactory
from education_group.tests.ddd.factories.funding import FundingFactory
from education_group.tests.ddd.factories.group import GroupFactory
from education_group.tests.ddd.factories.remark import RemarkFactory
from education_group.tests.ddd.factories.study_domain import StudyDomainFactory
from education_group.tests.ddd.factories.titles import TitlesFactory
from education_group.tests.ddd.factories.training import TrainingFactory
from education_group.tests.factories.mini_training import MiniTrainingFactory
from program_management.business.xls_customized import _build_headers, TRAINING_LIST_CUSTOMIZABLE_PARAMETERS, \
    WITH_ACTIVITIES, WITH_ORGANIZATION, WITH_ARES_CODE, WITH_CO_GRADUATION_AND_PARTNERSHIP, \
    _build_additional_info_data, _build_validity_data, _get_start_year, _get_end_year, _get_titles_en, \
    _build_organization_data, _get_responsibles_and_contacts, _build_aims_data, _build_keywords_data, \
    _get_co_organizations, _build_duration_data, _build_common_ares_code_data, _title_yes_no_empty, \
    _build_funding_data, _build_diploma_certificat_data, _build_enrollment_data, \
    _build_other_legal_information_data, _build_title_fr, _build_secondary_domains
from program_management.tests.ddd.factories.node import NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.factories.program_tree_version import ProgramTreeVersionFactory
from program_management.tests.ddd.factories.program_tree_version import StandardProgramTreeVersionFactory, \
    SpecificProgramTreeVersionFactory
from program_management.tests.factories.education_group_version import StandardEducationGroupVersionFactory
from program_management.tests.factories.element import ElementGroupYearFactory

FIRST_CUSTOMIZABLE_COL = 7

UNSPECIFIED_FR = "Indéterminé"


DEFAULT_FR_HEADERS = ['Anac.', 'Sigle/Int. abr.', 'Intitulé', 'Catégorie', 'Type', 'Crédits', 'Code']
VALIDITY_HEADERS = ["Statut", "Début", "Dernière année d'org."]
PARTIAL_ENGLISH_TITLES = ["Intitulé en anglais", "Intitulé partiel en français", "Intitulé partiel en anglais", ]
EDUCATION_FIELDS_HEADERS = ["Domaine principal", "Domaines secondaires", "Domaine ISCED/CITE"]
ACTIVITIES_HEADERS = [
    "Activités sur d'autres sites", "Stage", "Mémoire", "Langue principale", "Activités en anglais",
    "Activités dans d'autres langues"
]
ORGANIZATION_HEADERS = [
    "Type horaire", "Ent. gestion", "Ent. adm.", "Lieu d'enseignement", "Durée"
] + ACTIVITIES_HEADERS


ARES_HEADERS_ONLY = ["Code étude ARES", "ARES-GRACA", "Habilitation ARES"]

CO_GRADUATION_AND_PARTNERSHIP_COMMON_WITH_ARES_HEADERS = [
    "Code co-diplômation intra CfB", "Coefficient total de co-diplômation"
]

CO_GRADUATION_AND_PARTNERSHIP_HEADERS = CO_GRADUATION_AND_PARTNERSHIP_COMMON_WITH_ARES_HEADERS +\
                                        ["Programme co-organisés avec d'autres institutions"]


ARES_HEADERS = CO_GRADUATION_AND_PARTNERSHIP_COMMON_WITH_ARES_HEADERS + ARES_HEADERS_ONLY

DIPLOMA_CERTIFICAT_HEADERS = [
    "Mène à diplôme/certificat", "Intitulé du diplôme/du certificat", "Titre professionnel", "Attendus du diplôme"
    ]
ENROLLMENT_HEADERS = [
    "Lieu d'inscription", "Inscriptible", "Ré-inscription par internet", "Sous-épreuve", "Concours", "Code tarif"
]

FUNDING_HEADERS = [
    "Finançable", "Orientation de financement", "Financement coopération internationale CCD/CUD",
    "Orientation coopération internationale CCD/CUD"
]
OTHER_LEGAL_INFORMATION_HEADERS = ["Nature", "Certificat universitaire", "Catégorie décret"]
ADDITIONAL_INFO_HEADERS = [
    "Type de contrainte", "Contrainte minimum", "Contrainte maximum", "Commentaire (interne)", "Remarque",
    "Remarque en anglais"
]


@override_settings(LANGUAGES=[('fr-be', 'Français'), ], LANGUAGE_CODE='fr-be')
class XlsCustomizedHeadersTestCase(SimpleTestCase):

    def test_headers_without_selected_parameters(self):
        expected = DEFAULT_FR_HEADERS
        self.assertListEqual(_build_headers([]), expected)

    def test_headers_with_all_parameters_selected(self):
        headers = _build_headers(TRAINING_LIST_CUSTOMIZABLE_PARAMETERS)
        self.assertListEqual(headers[0:FIRST_CUSTOMIZABLE_COL], DEFAULT_FR_HEADERS)
        self.assertListEqual(headers[FIRST_CUSTOMIZABLE_COL:10], VALIDITY_HEADERS)
        self.assertListEqual(headers[10:13], PARTIAL_ENGLISH_TITLES)
        self.assertListEqual(headers[13:16], EDUCATION_FIELDS_HEADERS)
        self.assertListEqual(headers[16:27], ORGANIZATION_HEADERS)
        self.assertListEqual(headers[27:28], ["Infos générales - contacts"])
        self.assertListEqual(headers[28:32], DIPLOMA_CERTIFICAT_HEADERS)
        self.assertListEqual(headers[32:35], CO_GRADUATION_AND_PARTNERSHIP_HEADERS)
        self.assertListEqual(headers[35:41], ENROLLMENT_HEADERS)
        self.assertListEqual(headers[41:45], FUNDING_HEADERS)
        self.assertListEqual(headers[45:48], ARES_HEADERS_ONLY)
        self.assertListEqual(headers[48:51], OTHER_LEGAL_INFORMATION_HEADERS)
        self.assertListEqual(headers[51:57], ADDITIONAL_INFO_HEADERS)
        self.assertListEqual(headers[57:58], ["Mots clés"])

    def test_no_duplicate_headers_when_organization_and_activities(self):
        headers = _build_headers([WITH_ORGANIZATION, WITH_ACTIVITIES])
        self.assertListEqual(headers[0:FIRST_CUSTOMIZABLE_COL], DEFAULT_FR_HEADERS)
        self.assertListEqual(headers[FIRST_CUSTOMIZABLE_COL:], ORGANIZATION_HEADERS)

    def test_no_duplicate_headers_when_organization_and_without_activities(self):
        headers = _build_headers([WITH_ORGANIZATION])
        self.assertListEqual(headers[0:FIRST_CUSTOMIZABLE_COL], DEFAULT_FR_HEADERS)
        self.assertListEqual(headers[FIRST_CUSTOMIZABLE_COL:], ORGANIZATION_HEADERS)

    def test_no_duplicate_headers_without_organization_and_with_activities(self):
        headers = _build_headers([WITH_ACTIVITIES])
        self.assertListEqual(headers[0:FIRST_CUSTOMIZABLE_COL], DEFAULT_FR_HEADERS)
        self.assertListEqual(headers[FIRST_CUSTOMIZABLE_COL:], ACTIVITIES_HEADERS)

    def test_no_duplicate_headers_with_co_graduation_and_partnership_and_ares_code(self):
        headers = _build_headers([WITH_CO_GRADUATION_AND_PARTNERSHIP, WITH_ARES_CODE])
        self.assertListEqual(headers[0:FIRST_CUSTOMIZABLE_COL], DEFAULT_FR_HEADERS)
        self.assertListEqual(headers[FIRST_CUSTOMIZABLE_COL:], CO_GRADUATION_AND_PARTNERSHIP_HEADERS + ARES_HEADERS_ONLY)

    def test_headers_without_co_graduation_and_partnership_and_with_ares_code(self):
        headers = _build_headers([WITH_ARES_CODE])
        self.assertListEqual(headers[0:FIRST_CUSTOMIZABLE_COL], DEFAULT_FR_HEADERS)
        self.assertListEqual(headers[FIRST_CUSTOMIZABLE_COL:], ARES_HEADERS)

    def test_headers_with_co_graduation_and_partnership_and_without_ares_code(self):
        headers = _build_headers([WITH_CO_GRADUATION_AND_PARTNERSHIP])
        self.assertListEqual(headers[0:FIRST_CUSTOMIZABLE_COL], DEFAULT_FR_HEADERS)
        self.assertListEqual(headers[FIRST_CUSTOMIZABLE_COL:], CO_GRADUATION_AND_PARTNERSHIP_HEADERS)


class XlsCustomizedContentTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        remark = RemarkFactory(text_fr="<p>Remarque voir <a href='https://www.google.com/'>Google</a></p>",
                               text_en="Remarque fr")
        cls.current_year = get_current_year()
        cls.training_version = StandardEducationGroupVersionFactory(
            offer__acronym="DROI2M",
            offer__partial_acronym="LDROI200M",
            offer__academic_year__year=cls.current_year,
            offer__education_group_type__name=TrainingType.PGRM_MASTER_120.name,
            root_group__acronym="DROI2M",
            root_group__partial_acronym="LDROI200M",
            root_group__academic_year__year=cls.current_year,
            root_group__education_group_type__name=TrainingType.PGRM_MASTER_120.name,
        )
        cls.root_group_element = ElementGroupYearFactory(group_year=cls.training_version.root_group)

        cls.constraint = ContentConstraintFactory(type=ConstraintTypeEnum.CREDITS,
                                                  minimum=1,
                                                  maximum=15)

        cls.group_training = GroupFactory(entity_identity__code=cls.training_version.root_group.partial_acronym,
                                          entity_identity__year=cls.current_year,
                                          content_constraint=cls.constraint,
                                          remark=remark
                                          )
        cls.training = TrainingFactory(entity_identity__acronym=cls.training_version.root_group.partial_acronym,
                                       entity_identity__year=cls.current_year,
                                       internal_comment='Internal comment',
                                       start_year=cls.current_year,
                                       end_year=cls.current_year+6)

        root_node_training = NodeGroupYearFactory(node_type=TrainingType.PGRM_MASTER_120,
                                                  offer_partial_title_fr='LDROI200M',
                                                  start_year=cls.current_year,
                                                  end_year=cls.current_year+3,)
        cls.current_training_tree_version = StandardProgramTreeVersionFactory(
            tree=ProgramTreeFactory(root_node=root_node_training)
        )

        cls.mini_training_version = StandardEducationGroupVersionFactory(
            offer__acronym="APPDRT",
            offer__partial_acronym="LDRT100P",
            offer__academic_year__year=cls.current_year,
            offer__education_group_type__name=MiniTrainingType.DEEPENING.name,
            root_group__acronym="APPDRT",
            root_group__partial_acronym="LDRT100P",
            root_group__academic_year__year=cls.current_year,
            root_group__education_group_type__name=MiniTrainingType.DEEPENING.name,
        )

        cls.education_group_type = MiniTrainingEducationGroupTypeFactory()
        cls.mini_training = MiniTrainingFactory(
            entity_identity=MiniTrainingIdentity(acronym="APPDRT", year=cls.current_year),
            start_year=cls.current_year,
            type=education_group_types.MiniTrainingType[cls.education_group_type.name],
        )
        root_node_mini_training = NodeGroupYearFactory(node_type=cls.mini_training.type,
                                                       offer_partial_title_fr='LDRT100P')
        cls.current_mini_training_tree_version = StandardProgramTreeVersionFactory(
            tree=ProgramTreeFactory(root_node=root_node_mini_training)
        )

        cls.group_mini_training = GroupFactory(
            entity_identity__code=cls.mini_training_version.root_group.partial_acronym,
            entity_identity__year=cls.current_year,
            content_constraint=cls.constraint,
            remark=remark
        )

        cls.group = GroupFactory(
            entity_identity=GroupIdentity(code="LOIS58", year=cls.current_year),
            start_year=cls.current_year,
            type=GroupType.COMMON_CORE.name,
            content_constraint=cls.constraint,
            remark=remark
        )

    def test_build_validity_for_training(self):
        expected = [
            'Actif',
            "{}-{}".format(str(self.training.start_year), str(self.training.start_year + 1)[-2:]),
            "{}-{}".format(str(self.training.end_year), str(self.training.end_year + 1)[-2:])
        ]
        data = _build_validity_data(self.training, self.group_training, self.current_training_tree_version)
        self.assertListEqual(data, expected)

    def test_build_validity_no_data(self):
        data = _build_validity_data(None, self.group_training, self.current_training_tree_version)
        self.assertListEqual(data, _build_array_with_empty_string(3))

    def test_get_start_year(self):
        standard_current_version = StandardProgramTreeVersionFactory()
        particular_current_version = SpecificProgramTreeVersionFactory()
        training = TrainingFactory(start_year=2020,
                                   end_year=2021)
        mini_training = MiniTrainingFactory(start_year=2022,
                                            end_year=2023)
        group = GroupFactory(start_year=2018,
                             end_year=2019)
        self.assertEqual(_get_start_year(standard_current_version, training, group),
                         "{}-{}".format(str(training.start_year), str(training.start_year + 1)[-2:]))
        self.assertEqual(_get_start_year(particular_current_version, training, group),
                         "{}-{}".format(str(group.start_year), str(group.start_year + 1)[-2:]))
        self.assertEqual(_get_start_year(standard_current_version, mini_training, group),
                         "{}-{}".format(str(standard_current_version.start_year),
                                        str(standard_current_version.start_year + 1)[-2:]))
        self.assertEqual(_get_start_year(particular_current_version, mini_training, group),
                         "{}-{}".format(str(particular_current_version.start_year),
                                        str(particular_current_version.start_year + 1)[-2:]))
        self.assertEqual(_get_start_year(particular_current_version, None, group),
                         '')

    def test_build_additional_info_for_training(self):
        expected = [self.group_training.content_constraint.type.value.title(),
                    self.group_training.content_constraint.minimum,
                    self.group_training.content_constraint.maximum, self.training.internal_comment,
                    "Remarque voir Google", self.group_training.remark.text_en]
        data = _build_additional_info_data(self.training, self.group_training)
        self.assertListEqual(data, expected)

    def test_build_additional_info_for_mini_training(self):
        expected = [self.group_mini_training.content_constraint.type.value.title(),
                    self.group_mini_training.content_constraint.minimum,
                    self.group_mini_training.content_constraint.maximum, '',
                    "Remarque voir Google", self.group_mini_training.remark.text_en]
        data = _build_additional_info_data(self.mini_training, self.group_mini_training)
        self.assertListEqual(data, expected)

    def test_build_additional_info_for_group(self):
        expected = [self.group.content_constraint.type.value.title(),
                    self.group.content_constraint.minimum,
                    self.group.content_constraint.maximum, '',
                    "Remarque voir Google", self.group.remark.text_en]
        data = _build_additional_info_data(None, self.group)
        self.assertListEqual(data, expected)

    def test_build_additional_info_no_data(self):
        data = _build_additional_info_data(None, None)
        self.assertListEqual(data, _build_array_with_empty_string(6))

    def test_end_year(self):
        standard_current_version = StandardProgramTreeVersionFactory()
        particular_current_version = SpecificProgramTreeVersionFactory()
        training = TrainingFactory(start_year=2020,
                                   end_year=2021)
        training_without_end_year = TrainingFactory(start_year=2020, end_year=None)
        mini_training = MiniTrainingFactory(start_year=2022,
                                            end_year=2023)
        group = GroupFactory(start_year=2018,
                             end_year=2019)
        self.assertEqual(_get_end_year(standard_current_version, training, group),
                         "{}-{}".format(str(training.end_year), str(training.end_year + 1)[-2:]))
        self.assertEqual(_get_end_year(particular_current_version, training, group),
                         "{}-{}".format(str(group.end_year), str(group.end_year + 1)[-2:]))
        self.assertEqual(_get_end_year(standard_current_version, training_without_end_year, group),
                         UNSPECIFIED_FR)

        standard_current_version = ProgramTreeVersionFactory(end_year_of_existence=2021)
        standard_current_version_without_end_year = ProgramTreeVersionFactory(end_year_of_existence=None)
        self.assertEqual(_get_end_year(standard_current_version, mini_training, group),
                         "{}-{}".format(str(standard_current_version.end_year_of_existence),
                                        str(standard_current_version.end_year_of_existence + 1)[-2:]))
        self.assertEqual(_get_end_year(standard_current_version_without_end_year, mini_training, group),
                         UNSPECIFIED_FR)


class XlsCustomizedContentTitlesPartialAndEnTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory()
        cls.standard_current_version = StandardProgramTreeVersionFactory()
        cls.particular_current_version = SpecificProgramTreeVersionFactory(title_en='Title en', title_fr='Title fr')

        titles = TitlesFactory()
        cls.aims1 = DiplomaAimFactory(entity_id__section=1, entity_id__code=191, description="description 1")
        cls.aims2 = DiplomaAimFactory(entity_id__section=2, entity_id__code=192, description="description 2")
        diplomas_factory = DiplomaFactory(aims=[
            cls.aims1,
            cls.aims2,
        ])
        cls.training = TrainingFactory(titles=titles, diploma=diplomas_factory,
                                       type=TrainingType.BACHELOR, entity_identity__year=cls.academic_year.year)
        cls.training_finality = TrainingFactory(titles=titles,
                                                type=TrainingType.MASTER_MA_120)

        cls.mini_training = MiniTrainingFactory(titles=titles, entity_identity__year=cls.academic_year.year)
        cls.group = GroupFactory(titles=titles, entity_identity__year=cls.academic_year.year)

    def test_get_titles_en_for_training_standard_version_not_finality(self):
        self.assertListEqual(_get_titles_en(self.standard_current_version, self.training, self.group),
                             [self.training.titles.title_en, '', ''])

    def test_get_titles_en_for_training_standard_version_finality(self):
        self.assertListEqual(_get_titles_en(self.standard_current_version, self.training_finality, self.group),
                             [
                                 self.training.titles.title_en,
                                 self.training.titles.partial_title_fr,
                                 self.training.titles.partial_title_en
                             ]
                             )

    def test_get_titles_en_for_training_particular_version_not_finality(self):
        self.assertListEqual(_get_titles_en(self.particular_current_version, self.training, self.group),
                             ["{}[{}]".format(self.training.titles.title_en,
                                              self.particular_current_version.title_en),
                              '', '']
                             )

    def test_get_titles_en_for_training_particular_version_finality(self):
        self.assertListEqual(_get_titles_en(self.particular_current_version, self.training_finality, self.group),
                             [
                                 "{}[{}]".format(self.training.titles.title_en,
                                                 self.particular_current_version.title_en),
                                 self.training.titles.partial_title_fr,
                                 self.training.titles.partial_title_en
                             ]
                             )

    def test_get_titles_en_for_group(self):
        self.assertListEqual(_get_titles_en(None, None, self.group),
                             [self.group.titles.title_en, '', ''])

    @mock.patch('base.models.entity_version.EntityVersion.is_entity_active', return_value=True)
    def test_build_organization_data_for_training(self, mock_is_entity_active):
        result = _build_organization_data(self.standard_current_version, self.training, None, self.group)
        expected = [
            self.training.schedule_type.value,
            self.training.management_entity.acronym,
            self.training.administration_entity.acronym,
            "{} - {}".format(self.group.teaching_campus.name,
                             self.group.teaching_campus.university_name),
            "{} {}".format(self.training.duration, self.training.duration_unit.value),
            self.training.other_campus_activities.value.title() if self.training.other_campus_activities else '',
            self.training.internship_presence.value.title() if self.training.internship_presence else '',
            str(_('Yes')) if self.training.has_dissertation else str(_('No')),
            self.training.main_language.name if self.training.main_language else '',
            self.training.english_activities.value.title() if self.training.english_activities else '',
            self.training.other_language_activities.value.title() if self.training.other_language_activities else ''
        ]
        self.assertListEqual(
            result,
            expected)

    @mock.patch('base.models.entity_version.EntityVersion.is_entity_active', return_value=True)
    def test_build_organization_data_for_mini_training(self, mock_is_entity_active):
        result = _build_organization_data(None, None, self.mini_training, self.group)
        expected = [
            self.mini_training.schedule_type.value,
            self.group.management_entity.acronym,
            "",
            "{} - {}".format(self.group.teaching_campus.name,
                             self.group.teaching_campus.university_name),
            "",
            "",
            "",
            "",
            "",
            "",
            ""
        ]
        self.assertListEqual(
            result,
            expected)

    @mock.patch('base.models.entity_version.EntityVersion.is_entity_active', return_value=True)
    def test_build_organization_data_for_group(self, mock_is_entity_active):
        result = _build_organization_data(None, None, None, self.group)
        expected = [
            "",
            self.group.management_entity.acronym,
            "",
            "{} - {}".format(self.group.teaching_campus.name,
                             self.group.teaching_campus.university_name),
            "",
            "",
            "",
            "",
            "",
            "",
            ""
        ]
        self.assertListEqual(
            result,
            expected)

    def test_get_responsibles_and_contacts(self):
        education_group_version = StandardEducationGroupVersionFactory()

        g = GroupFactory(entity_identity=GroupIdentity(code=education_group_version.offer.partial_acronym,
                                                       year=education_group_version.offer.academic_year.year))
        academic_responsible_contact = EducationGroupPublicationContactFactory(
            type=PublicationContactType.ACADEMIC_RESPONSIBLE.name,
            role_fr='dummy role in french',
            role_en='dummy role in english',
            education_group_year=education_group_version.offer
        )
        academic_responsible_contact_2 = EducationGroupPublicationContactFactory(
            type=PublicationContactType.ACADEMIC_RESPONSIBLE.name,
            role_fr='dummy role2 in french',
            role_en='dummy role2 in english',
            education_group_year=education_group_version.offer
        )
        other_academic_responsible_contact = EducationGroupPublicationContactFactory(
            type=PublicationContactType.OTHER_ACADEMIC_RESPONSIBLE.name,
            role_fr='dummy role in french',
            role_en='dummy role in english',
            education_group_year=education_group_version.offer
        )
        jury_member = EducationGroupPublicationContactFactory(
            type=PublicationContactType.JURY_MEMBER.name,
            role_fr='dummy role in french',
            role_en='dummy role in english',
            education_group_year=education_group_version.offer
        )
        other_contact = EducationGroupPublicationContactFactory(
            type=PublicationContactType.OTHER_CONTACT.name,
            role_fr='dummy role in french',
            role_en='dummy role in english',
            education_group_year=education_group_version.offer
        )
        contacts = _get_responsibles_and_contacts(g)
        basic_titles = "Responsable académique\n{}\n{}\n\n" \
                       "Autres responsables académiques\n{}\n\n" \
                       "Membres du jury\n{}\n\n" \
                       "Autres contacts\n{}\n\n"
        expected = basic_titles.format(
            _build_person_detail(academic_responsible_contact),
            _build_person_detail(academic_responsible_contact_2),
            _build_person_detail(other_academic_responsible_contact),
            _build_person_detail(
                jury_member),
            _build_person_detail(other_contact)
        )
        self.assertEqual(contacts, expected)

    def test_build_aims_data(self):
        data_aims_1 = "{} - {} - {} ;".format(
            self.aims1.section, self.aims1.code, self.aims1.description
        )
        data_aims_2 = "{} - {} - {} ;".format(self.aims2.section, self.aims2.code, self.aims2.description)
        expected = "{}\n{}".format(data_aims_1, data_aims_2)
        aims_data = _build_aims_data(self.training)
        self.assertEqual(aims_data, expected)

    def test_build_without_aims_data(self):
        training_without_aims = TrainingFactory(diploma=DiplomaFactory(aims=[]))
        self.assertEqual(_build_aims_data(training_without_aims), '')

    def test_build_keywords_data(self):
        self.assertEqual(_build_keywords_data(self.training), self.training.keywords)
        self.assertEqual(_build_keywords_data(self.mini_training), self.mini_training.keywords)
        self.assertEqual(_build_keywords_data(None), '')

    def test_get_co_organizations_no_data(self):
        self.assertEqual(_get_co_organizations([]), '')

    def test_get_co_organizations(self):
        co_organization_1 = CoorganizationFactory(partner=AcademicPartnerFactory(address=AddressFactory()))
        co_organization_2 = CoorganizationFactory()
        expected = '{}\n{}'.format(_get_co_organization_data(co_organization_1),
                                   _get_co_organization_data(co_organization_2)
                                   )

        res = _get_co_organizations([co_organization_1, co_organization_2])
        self.assertEqual(res, expected)

    def test_build_duration_data(self):
        self.assertEqual(_build_duration_data(self.training),
                         "{} {}".format(self.training.duration, self.training.duration_unit.value))
        self.assertEqual(_build_duration_data(TrainingFactory(duration=None)),
                         '')

    def test_build_common_ares_code_data(self):
        co_graduation = CoGraduationFactory(code_inter_cfb='A', coefficient=2.5)
        self.assertListEqual(_build_common_ares_code_data(co_graduation), ['A', '2.5'])

        co_graduation = CoGraduationFactory(code_inter_cfb=None, coefficient=None)
        self.assertListEqual(_build_common_ares_code_data(co_graduation), _build_array_with_empty_string(2))

        self.assertListEqual(_build_common_ares_code_data(None), _build_array_with_empty_string(2))

    def test_title_yes_no_empty(self):
        self.assertEqual(_title_yes_no_empty(True), 'Oui')
        self.assertEqual(_title_yes_no_empty(False), 'Non')

    def test_build_funding_data(self):
        self.assertListEqual(_build_funding_data(None), _build_array_with_empty_string(4))
        funding = FundingFactory()
        self.assertListEqual(_build_funding_data(funding), ['Oui' if funding.can_be_funded else 'Non',
                                                            funding.funding_orientation.value.title(),
                                                            'Oui' if funding.can_be_international_funded else 'Non',
                                                            funding.international_funding_orientation.value.title()])
        funding = FundingFactory(funding_orientation=None, international_funding_orientation=None)
        self.assertListEqual(_build_funding_data(funding), ['Oui' if funding.can_be_funded else 'Non',
                                                            '',
                                                            'Oui' if funding.can_be_international_funded else 'Non',
                                                            ''])

    def test_build_diploma_certicat_data(self):
        diploma = DiplomaFactory(leads_to_diploma=True,
                                 printing_title='Printing title',
                                 professional_title='Professional title',
                                 aims=[])
        training_diploma = TrainingFactory(diploma=diploma)
        self.assertListEqual(_build_diploma_certificat_data(training_diploma),
                             ['Oui', 'Printing title', 'Professional title', ''])
        diploma = DiplomaFactory(leads_to_diploma=False,
                                 printing_title=None,
                                 professional_title=None,
                                 aims=[])

        training_diploma = TrainingFactory(diploma=diploma)
        self.assertListEqual(_build_diploma_certificat_data(training_diploma),
                             ['Non', '', '', ''])
        training_without_diploma = TrainingFactory(diploma=None)
        self.assertListEqual(_build_diploma_certificat_data(training_without_diploma),
                             _build_array_with_empty_string(4))

    def test_build_enrollment_data(self):
        self.assertListEqual(_build_enrollment_data(None), _build_array_with_empty_string(6))
        self.assertListEqual(_build_enrollment_data(self.training),
                             ["{} - {}".format(self.training.enrollment_campus.name,
                                               self.training.enrollment_campus.university_name),
                              "Oui",
                              "Oui",
                              "Oui",
                              "Oui",
                              self.training.rate_code.value])

    def test_build_other_legal_information_data(self):
        self.assertListEqual(_build_other_legal_information_data(None), _build_array_with_empty_string(3))
        self.assertListEqual(_build_other_legal_information_data(self.training),
                             [self.training.academic_type.value,
                              "Oui",
                              "{} - {}".format(self.training.decree_category.name,
                                               self.training.decree_category.value)
                              ]
                             )

    def test_build_title_fr_training(self):
        self.assertEqual(_build_title_fr(self.training, None, None), self.training.titles.title_fr)

    def test_build_title_fr_minitraining(self):
        self.assertEqual(_build_title_fr(self.mini_training, None, None), self.mini_training.titles.title_fr)

    def test_build_title_fr_group(self):
        self.assertEqual(_build_title_fr(None, self.group, None), self.group.titles.title_fr)

    def test_build_title_fr_training_with_version(self):
        self.assertEqual(_build_title_fr(self.training, None, self.particular_current_version),
                         "{}[{}]".format(self.training.titles.title_fr,
                                         self.particular_current_version.title_fr))

    def test_build_secondary_domains_no_data(self):
        self.assertEqual(_build_secondary_domains(None), '')
        self.assertEqual(_build_secondary_domains([]), '')

    def test_build_secondary_domains(self):
        secondary_domain_1 = StudyDomainFactory()
        secondary_domain_2 = StudyDomainFactory()
        self.assertCountEqual(
            _build_secondary_domains([secondary_domain_1, secondary_domain_2]),
            "{}\n{}".format(
                "{} : {} {}".format(secondary_domain_1.decree_name, secondary_domain_1.code, secondary_domain_1.name),
                "{} : {} {}".format(secondary_domain_2.decree_name, secondary_domain_2.code, secondary_domain_2.name)
            )
        )


def _build_array_with_empty_string(nb_of_occurence):
    return ['' for _ in range(0, nb_of_occurence)]


def _get_co_organization_data(co_organization):
    line1 = "{} - {} \n{}\n".format(
        co_organization.partner.address.country_name if co_organization.partner.address else '',
        co_organization.partner.address.city if co_organization.partner.address else '',
        co_organization.partner.name
    )
    line2 = _build_line('For all students', co_organization.is_for_all_students)
    line3 = _build_line('Reference institution', co_organization.is_reference_institution)

    line5 = _build_line('Producing certificat', co_organization.is_producing_certificate)
    line6 = _build_line('Producing annexe', co_organization.is_producing_certificate_annexes)

    line4 = "{} : {}\n".format(
        str(_('UCL Diploma')),
        co_organization.certificate_type.value if co_organization.certificate_type else ''
    )
    return line1 + line2 + line3 + line4 + line5 + line6


def _build_line(title, boolean_value):
    return "{} : {}\n".format(str(_(title)),
                              'Oui' if boolean_value else 'Non')


def _build_person_detail(person):
    return "{}\n(fr) {}\n(en) {}".format(
                person.email,
                person.role_fr,
                person.role_en,
            )

