##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test import TestCase

from base.models.certificate_aim import CertificateAim
from base.models.education_group import EducationGroup
from base.models.education_group_certificate_aim import EducationGroupCertificateAim
from base.models.education_group_year import EducationGroupYear as EducationGroupYearModelDb, EducationGroupYear
from base.models.education_group_year_domain import EducationGroupYearDomain
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.campus import CampusFactory as CampusModelDbFactory
from base.tests.factories.certificate_aim import CertificateAimFactory as CertificateAimModelDbFactory
from base.tests.factories.education_group_type import TrainingEducationGroupTypeFactory
from base.tests.factories.education_group_year import TrainingFactory as TrainingDBFactory
from base.tests.factories.entity_version import EntityVersionFactory as EntityVersionModelDbFactory
from education_group.ddd.domain.training import TrainingIdentity
from education_group.ddd.repository.training import TrainingRepository
from education_group.tests.ddd.factories.campus import CampusIdentityFactory
from education_group.tests.ddd.factories.diploma import DiplomaAimFactory, DiplomaAimIdentityFactory
from education_group.tests.ddd.factories.isced_domain import IscedDomainIdentityFactory
from education_group.tests.ddd.factories.study_domain import StudyDomainIdentityFactory, StudyDomainFactory
from education_group.tests.ddd.factories.training import TrainingFactory, TrainingIdentityFactory
from reference.models.domain import Domain
from reference.tests.factories.domain import DomainFactory as DomainModelDbFactory
from reference.tests.factories.domain_isced import DomainIscedFactory as DomainIscedFactoryModelDb
from reference.tests.factories.language import LanguageFactory as LanguageModelDbFactory


class TestTrainingRepositoryCreateMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.year = AcademicYearFactory(current=True).year

        cls.repository = TrainingRepository()

        cls.education_group_type = TrainingEducationGroupTypeFactory()
        cls.language = LanguageModelDbFactory()
        cls.study_domain = DomainModelDbFactory()
        cls.secondary_study_domain = DomainModelDbFactory()
        cls.isced_domain = DomainIscedFactoryModelDb()
        cls.entity_version = EntityVersionModelDbFactory()
        cls.campus = CampusModelDbFactory()
        cls.certificate_aim = CertificateAimModelDbFactory()

        study_domain_identity = StudyDomainIdentityFactory(decree_name=cls.study_domain.decree.name, code=cls.study_domain.code)
        diploma_aim_identity = DiplomaAimIdentityFactory(code=cls.certificate_aim.code, section=cls.certificate_aim.section)
        campus_identity = CampusIdentityFactory(name=cls.campus.name, university_name=cls.campus.organization.name)
        training_identity = TrainingIdentityFactory(year=cls.year)
        cls.training = TrainingFactory(
            entity_id=training_identity,
            entity_identity=training_identity,
            start_year=cls.year,
            end_year=cls.year,
            type=TrainingType[cls.education_group_type.name],
            main_language__name=cls.language.name,
            main_domain__entity_id=study_domain_identity,
            isced_domain__entity_id=IscedDomainIdentityFactory(code=cls.isced_domain.code),
            management_entity__acronym=cls.entity_version.acronym,
            administration_entity__acronym=cls.entity_version.acronym,
            teaching_campus=campus_identity,
            enrollment_campus=campus_identity,
            secondary_domains=[
                StudyDomainFactory(entity_id=study_domain_identity)
            ],
            diploma__aims=[
                DiplomaAimFactory(entity_id=diploma_aim_identity)
            ]
        )

    def test_fields_mapping(self):
        entity_id = self.repository.create(self.training)

        # EducationGroup
        education_group = EducationGroup.objects.get(
            educationgroupyear__acronym=self.training.entity_id.acronym,
            educationgroupyear__academic_year__year=self.training.entity_id.year,
        )
        self.assertEqual(education_group.start_year.year, self.training.start_year)
        self.assertEqual(education_group.end_year.year, self.training.end_year)

        # EducationGroupYear
        education_group_year = EducationGroupYearModelDb.objects.get(
            acronym=entity_id.acronym,
            academic_year__year=entity_id.year,
        )
        self.assertEqual(education_group_year.education_group, education_group)
        self.assertEqual(education_group_year.acronym, self.training.entity_id.acronym)
        self.assertEqual(education_group_year.academic_year.year, self.training.entity_id.year)
        self.assertEqual(education_group_year.education_group_type.name, self.training.type.name)
        self.assertEqual(education_group_year.credits, int(self.training.credits))
        self.assertEqual(education_group_year.schedule_type, self.training.schedule_type.name)
        self.assertEqual(education_group_year.duration, self.training.duration)
        self.assertEqual(education_group_year.title, self.training.titles.title_fr)
        self.assertEqual(education_group_year.title_english, self.training.titles.title_en)
        self.assertEqual(education_group_year.partial_title, self.training.titles.partial_title_fr)
        self.assertEqual(education_group_year.partial_title_english, self.training.titles.partial_title_en)
        self.assertEqual(education_group_year.keywords, self.training.keywords)
        self.assertEqual(education_group_year.internship, self.training.internship_presence.name)
        self.assertEqual(education_group_year.enrollment_enabled, self.training.is_enrollment_enabled)
        self.assertEqual(education_group_year.web_re_registration, self.training.has_online_re_registration)
        self.assertEqual(education_group_year.partial_deliberation, self.training.has_partial_deliberation)
        self.assertEqual(education_group_year.admission_exam, self.training.has_admission_exam)
        self.assertEqual(education_group_year.dissertation, self.training.has_dissertation)
        self.assertEqual(education_group_year.university_certificate, self.training.produce_university_certificate)
        self.assertEqual(education_group_year.decree_category, self.training.decree_category.name)
        self.assertEqual(education_group_year.rate_code, self.training.rate_code.name)
        self.assertEqual(education_group_year.primary_language.name, self.training.main_language.name)
        self.assertEqual(education_group_year.english_activities, self.training.english_activities.name)
        self.assertEqual(education_group_year.other_language_activities, self.training.other_language_activities.name)
        self.assertEqual(education_group_year.internal_comment, self.training.internal_comment)
        self.assertEqual(education_group_year.main_domain.code, self.training.main_domain.entity_id.code)
        self.assertEqual(education_group_year.isced_domain.code, self.training.isced_domain.entity_id.code)
        self.assertEqual(education_group_year.management_entity_id, self.entity_version.entity_id)
        self.assertEqual(education_group_year.administration_entity_id, self.entity_version.entity_id)
        self.assertEqual(education_group_year.main_teaching_campus.name, self.campus.name)
        self.assertEqual(education_group_year.enrollment_campus.name, self.campus.name)
        self.assertEqual(education_group_year.other_campus_activities, self.training.other_campus_activities.name)
        self.assertEqual(education_group_year.funding, self.training.funding.can_be_funded)
        self.assertEqual(education_group_year.funding_direction, self.training.funding.funding_orientation.name)
        self.assertEqual(education_group_year.funding_cud, self.training.funding.can_be_international_funded)
        self.assertEqual(education_group_year.funding_direction_cud, self.training.funding.international_funding_orientation.name)
        self.assertEqual(education_group_year.hops.ares_study, self.training.hops.ares_code)
        self.assertEqual(education_group_year.hops.ares_graca, self.training.hops.ares_graca)
        self.assertEqual(education_group_year.hops.ares_ability, self.training.hops.ares_authorization)
        self.assertEqual(education_group_year.co_graduation, self.training.co_graduation.code_inter_cfb)
        self.assertEqual(education_group_year.co_graduation_coefficient, self.training.co_graduation.coefficient)
        self.assertEqual(education_group_year.academic_type, self.training.academic_type.name)
        self.assertEqual(education_group_year.duration_unit, self.training.duration_unit.name)
        self.assertEqual(education_group_year.professional_title, self.training.diploma.professional_title)
        self.assertEqual(education_group_year.joint_diploma, self.training.diploma.leads_to_diploma)
        self.assertEqual(education_group_year.diploma_printing_title, self.training.diploma.printing_title)
        self.assertEqual(education_group_year.active, self.training.status.name)

        # Secondary domains
        qs = EducationGroupYearDomain.objects.filter(education_group_year=education_group_year)
        self.assertEqual(1, qs.count())
        educ_group_year_domain = qs.get()
        self.assertEqual(
            educ_group_year_domain.domain,
            Domain.objects.get(
                code=self.training.secondary_domains[0].entity_id.code,
                decree__name=self.training.secondary_domains[0].entity_id.decree_name
            )
        )

        # Certificate aims
        qs_aims = EducationGroupCertificateAim.objects.filter(education_group_year=education_group_year)
        self.assertEqual(1, qs_aims.count())
        educ_group_certificate_aim = qs_aims.get()
        self.assertEqual(educ_group_certificate_aim.certificate_aim, CertificateAim.objects.get(code=self.training.diploma.aims[0].entity_id.code))


class TestTrainingRepositoryDeleteMethod(TestCase):
    def setUp(self) -> None:
        self.training_db = TrainingDBFactory()

    def test_assert_delete_in_database(self):
        training_id = TrainingIdentity(acronym=self.training_db.acronym, year=self.training_db.academic_year.year)
        TrainingRepository.delete(training_id)

        with self.assertRaises(EducationGroupYear.DoesNotExist):
            EducationGroupYear.objects.get(acronym=training_id.acronym, academic_year__year=training_id.year)
