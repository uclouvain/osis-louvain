from django.test import TestCase
from django.urls import reverse

from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_type import TrainingEducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from education_group.templatetags.academic_year_display import display_as_academic_year
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from education_group.tests.factories.group_year import GroupYearFactory
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository
from program_management.models.education_group_version import EducationGroupVersion
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.factories.program_tree_version import ProgramTreeVersionIdentityFactory, \
    ProgramTreeVersionFactory

KWARGS = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


class TestCheckVersionName(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)
        cls.year = cls.academic_year.year
        cls.entity_identity = ProgramTreeVersionIdentityFactory(year=cls.year, version_name="VERSION")
        cls.type = TrainingEducationGroupTypeFactory()
        cls.database_offer = EducationGroupYearFactory(
            academic_year=cls.academic_year,
            education_group_type=cls.type,
            acronym=cls.entity_identity.offer_acronym,
        )
        cls.repository = ProgramTreeVersionRepository()
        cls.new_program_tree = ProgramTreeFactory(
            root_node__year=cls.year,
            root_node__start_year=cls.year,
            root_node__end_year=cls.year,
            root_node__node_type=TrainingType[cls.type.name],
        )
        cls.new_program_tree_version = ProgramTreeVersionFactory(
            entity_identity=cls.entity_identity,
            entity_id=cls.entity_identity,
            program_tree_identity=cls.new_program_tree.entity_id,
            tree=cls.new_program_tree,
        )
        GroupYearFactory(
            partial_acronym=cls.new_program_tree_version.program_tree_identity.code,
            academic_year__year=cls.year
        )
        cls.repository.create(cls.new_program_tree_version)
        cls.education_group_version_db_object = EducationGroupVersion.objects.get(
            offer__acronym=cls.new_program_tree_version.entity_id.offer_acronym,
            offer__academic_year__year=cls.new_program_tree_version.entity_id.year,
            version_name=cls.new_program_tree_version.entity_id.version_name,
            is_transition=cls.new_program_tree_version.entity_id.is_transition
        )

    def setUp(self):
        self.central_manager = CentralManagerFactory()
        self.client.force_login(self.central_manager.person.user)

    def test_case_user_not_logged(self):
        self.client.logout()
        self.url = reverse(
            'check_version_name',
            kwargs={
                'year': self.year,
                'acronym': self.education_group_version_db_object.offer.acronym
            }
        )
        get_data = {'version_name': self.education_group_version_db_object.version_name}
        response = self.client.get(self.url, get_data, **KWARGS)
        self.assertTrue('/login/?next=' in response.url)

    def test_existing_version_name(self):
        self.url = reverse(
            'check_version_name',
            kwargs={
                'year': self.year,
                'acronym': self.education_group_version_db_object.root_group.acronym
            }
        )
        get_data = {'version_name': self.education_group_version_db_object.version_name}
        response = self.client.get(self.url, get_data, **KWARGS)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {
                "existed_version_name": False,
                "existing_version_name": True,
                "last_using": None,
                "valid": True,
                "version_name": self.education_group_version_db_object.version_name
            }
        )

    def test_existed_version_name(self):
        self.url = reverse(
            'check_version_name',
            kwargs={
                'year': self.year+1,
                'acronym': self.education_group_version_db_object.root_group.acronym
            }
        )
        get_data = {'version_name': self.education_group_version_db_object.version_name}
        response = self.client.get(self.url, get_data, **KWARGS)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {
                "existed_version_name": True,
                "existing_version_name": False,
                "last_using": display_as_academic_year(self.year),
                "valid": True,
                "version_name": self.education_group_version_db_object.version_name
            }
        )

    def test_invalid_version_name(self):
        invalid_version_names = "[@_!#$%^&*()<>?/|}{~:]".split()
        invalid_version_names.append('0123456')

        self.url = reverse(
            'check_version_name',
            kwargs={
                'year': self.year+1,
                'acronym': self.education_group_version_db_object.root_group.acronym
            }
        )
        for invalid_version_name in invalid_version_names:
            get_data = {'version_name': invalid_version_name}
            response = self.client.get(self.url, get_data, **KWARGS)
            self.assertJSONEqual(
                str(response.content, encoding='utf8'),
                {
                    "existed_version_name": False,
                    "existing_version_name": False,
                    "last_using": None,
                    "valid": False,
                    "version_name": invalid_version_name
                }
            )

    def test_valid_version_name(self):
        self.url = reverse(
            'check_version_name',
            kwargs={
                'year': self.year,
                'acronym': self.education_group_version_db_object.root_group.acronym
            }
        )
        get_data = {'version_name': self.education_group_version_db_object.version_name+"A"}
        response = self.client.get(self.url, get_data, **KWARGS)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {
                "existed_version_name": False,
                "existing_version_name": False,
                "last_using": None,
                "valid": True,
                "version_name": self.education_group_version_db_object.version_name+"A"
            }
        )
