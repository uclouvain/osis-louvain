from base.tests.factories.academic_year import AcademicYearFactory


class AcademicYearGenerator:
    def __init__(self):
        self.academic_years = AcademicYearFactory.produce(number_past=10, number_future=10)
        self.current_academic_year = self.academic_years[10]
