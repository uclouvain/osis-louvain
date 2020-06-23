from behave.runner import Context
from django.core import management

from features import factories as functional_factories
from features.factories import academic_year, reference, structure, users, score_encoding, learning_unit, \
    education_group, program
from features.factories.attribution import AttributionGenerator
from features.utils import log_execution_time


def setup_data(context: Context):
    context.data = FunctionalTestData()
    return context


class FunctionalTestData:
    def __init__(self):
        self.generate_all_data()

    def _load_fixtures(self):
        fixtures = ("authorized_relationship", "waffle_flags.json", "waffle_switches.json")
        management.call_command(
            'loaddata',
            *fixtures,
            **{'verbosity': 0}
        )
        management.call_command(
            "load_validation_rules",
        )

    @log_execution_time
    def generate_all_data(self):
        self._generate_base_data()
        self._generate_users()
        self._generate_learning_units_data()
        self._generate_attributions()
        self._generate_education_groups()

        self._load_fixtures()

        self._generate_programs()
        self._generate_score_encoding_data()

    @log_execution_time
    def _generate_base_data(self):
        academic_year_generator = functional_factories.academic_year.AcademicYearGenerator()
        reference_data_generator = functional_factories.reference.ReferenceDataGenerator()
        structure_generator = functional_factories.structure.StructureGenerator()

        self.academic_years = academic_year_generator.academic_years
        self.current_academic_year = academic_year_generator.current_academic_year
        self.languages = reference_data_generator.languages
        self.entity_tree = structure_generator.entity_tree
        self.main_campuses = structure_generator.campuses

    @log_execution_time
    def _generate_users(self):
        user_generator = functional_factories.users.UsersGenerator()

        self.superuser = user_generator.superuser
        self.faculty_manager = user_generator.faculty_manager
        self.central_manager = user_generator.central_manager
        self.tutors = user_generator.tutors
        self.students = user_generator.students
        self.program_managers = user_generator.program_managers

    @log_execution_time
    def _generate_learning_units_data(self):
        learning_unit_generator = functional_factories.learning_unit.LearningUnitGenerator()
        self.learning_units = learning_unit_generator.learning_units

    @log_execution_time
    def _generate_attributions(self):
        functional_factories.attribution.AttributionGenerator()

    @log_execution_time
    def _generate_education_groups(self):
        education_group_generator = functional_factories.education_group.EducationGroupsGenerator()
        self.education_groups = education_group_generator.education_groups

    @log_execution_time
    def _generate_score_encoding_data(self):
        functional_factories.score_encoding.ScoreEncodingFactory()

    @log_execution_time
    def _generate_programs(self):
        functional_factories.program.ProgramGenerators()
