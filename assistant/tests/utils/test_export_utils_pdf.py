##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime
import mimetypes
from django.utils.translation import ugettext_lazy as _
from django.test import TestCase, RequestFactory
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from base.models.entity import find_versions_from_entites
from assistant.utils import export_utils_pdf
from assistant.utils.export_utils_pdf import format_data
from assistant.tests.factories.academic_assistant import AcademicAssistantFactory
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.review import ReviewFactory
from assistant.models.enums import assistant_type, assistant_mandate_renewal



class ExportPdfTestCase(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.factory = RequestFactory()
        self.assistant = AcademicAssistantFactory(
            phd_inscription_date=datetime.date(2015, 10, 2),
            thesis_title='Data fitting on manifolds',
            confirmation_test_date=datetime.date(2017, 9, 25),
            remark="Deux co-promoteurs (l'application ne m'autorise à n'en renseigner qu'un)"
        )
        self.mandate = AssistantMandateFactory(
            assistant=self.assistant,
            assistant_type=assistant_type.ASSISTANT,
            sap_id='1120019',
            entry_date=datetime.date(2012, 9, 15),
            end_date=datetime.date(2018, 9, 14),
            contract_duration='6 ans',
            contract_duration_fte='6 ans',
            fulltime_equivalent=1,
            other_status=None,
            renewal_type=assistant_mandate_renewal.NORMAL,
            justification=None,
            external_contract='',
            external_functions='',
        )
        self.styles = getSampleStyleSheet()
        self.review1 = ReviewFactory(
            mandate=self.mandate
        )

    def test_format_data(self):
        data = 'good example of data.'
        title = 'formations'
        self.assertEqual("<strong>%s :</strong> %s<br />" % (_(title), data), export_utils_pdf.format_data(data, title))


    def test_get_administrative_data(self):
        assistant_type = format_data(_(self.mandate.assistant_type), 'assistant_type')
        matricule = format_data(self.mandate.sap_id, 'matricule_number')
        entry_date = format_data(self.mandate.entry_date, 'entry_date_contract')
        end_date = format_data(self.mandate.end_date, 'end_date_contract')
        contract_duration = format_data(self.mandate.contract_duration, 'contract_duration')
        contract_duration_fte = format_data(self.mandate.contract_duration_fte, 'contract_duration_fte')
        fulltime_equivalent = format_data(int(self.mandate.fulltime_equivalent * 100), 'fulltime_equivalent_percentage')
        other_status = format_data(self.mandate.other_status, 'other_status')
        renewal_type = format_data(_(self.mandate.renewal_type), 'renewal_type')
        justification = format_data(self.mandate.justification, 'exceptional_justification')
        external_contract = format_data(self.mandate.external_contract, 'external_post')
        external_functions = format_data(self.mandate.external_functions, 'function_outside_university')
        self.assertEqual( assistant_type + matricule + entry_date + end_date + contract_duration + contract_duration_fte \
           + fulltime_equivalent + other_status + renewal_type + justification + external_contract + external_functions,
                          export_utils_pdf.get_administrative_data(self.mandate))


    def test_get_entities(self):
        entities_id = self.mandate.mandateentity_set.all().order_by('id').values_list('entity', flat=True)
        entities = find_versions_from_entites(entities_id, self.mandate.academic_year.start_date)
        entities_data = ""
        for entity in entities:
            type = "%s" % (_(entity.entity_type))
            entities_data += "<strong>" + type + " :</strong> " + entity.acronym + "<br />"
        self.assertEqual(entities_data, export_utils_pdf.get_entities(self.mandate))


    def test_get_absences(self):
        self.assertEqual(self.mandate.absences if self.mandate.absences else "",
                         export_utils_pdf.get_absences(self.mandate))


    def test_get_comment(self):
        self.assertEqual(self.mandate.comment if self.mandate.comment else "",
                         export_utils_pdf.get_comment(self.mandate))


    def test_get_phd_data(self):
        thesis_title = format_data(self.assistant.thesis_title, 'thesis_title')
        phd_inscription_date = format_data(self.assistant.phd_inscription_date, 'phd_inscription_date')
        confirmation_test_date = format_data(self.assistant.confirmation_test_date, 'confirmatory_test_date')
        thesis_date = format_data(self.assistant.thesis_date, 'thesis_defence_date')
        expected_phd_date = format_data(self.assistant.expected_phd_date, 'expected_registering_date')
        inscription = format_data(_(self.assistant.inscription) if self.assistant.inscription else None,
                                  'registered_phd')
        remark = format_data(self.assistant.remark, 'remark')
        self.assertEqual(inscription + phd_inscription_date + expected_phd_date + confirmation_test_date + thesis_title \
               + thesis_date + remark, export_utils_pdf.get_phd_data(self.assistant))


    def test_get_research_data(self):
        internships = format_data(self.mandate.internships, 'scientific_internships')
        conferences = format_data(self.mandate.conferences, 'conferences_contributor')
        publications = format_data(self.mandate.publications, 'publications_in_progress')
        awards = format_data(self.mandate.awards, 'awards')
        framing = format_data(self.mandate.framing, 'framing_participation')
        remark = format_data(self.mandate.remark, 'remark')
        self.assertEqual(internships + conferences + publications + awards + framing + remark,
                         export_utils_pdf.get_research_data(self.mandate))


    def test_get_representation_activities(self):
        faculty_representation = format_data(str(self.mandate.faculty_representation), 'faculty_representation')
        institute_representation = format_data(str(self.mandate.institute_representation), 'institute_representation')
        sector_representation = format_data(str(self.mandate.sector_representation), 'sector_representation')
        governing_body_representation = format_data(str(self.mandate.governing_body_representation),
                                                    'governing_body_representation')
        corsci_representation = format_data(str(self.mandate.corsci_representation), 'corsci_representation')
        self.assertEqual(faculty_representation + institute_representation + sector_representation +
                         governing_body_representation + corsci_representation,
                         export_utils_pdf.get_representation_activities(self.mandate))


    def test_get_summary(self):
        report_remark = format_data(self.mandate.activities_report_remark, 'activities_report_remark')
        self.assertEqual(report_remark, export_utils_pdf.get_summary(self.mandate))


    def test_get_service_activities(self):
        students_service = format_data(str(self.mandate.students_service), 'students_service')
        infrastructure_mgmt_service = format_data(str(self.mandate.infrastructure_mgmt_service),
                                                  'infrastructure_mgmt_service')
        events_organisation_service = format_data(str(self.mandate.events_organisation_service),
                                                  'events_organisation_service')
        publishing_field_service = format_data(str(self.mandate.publishing_field_service), 'publishing_field_service')
        scientific_jury_service = format_data(str(self.mandate.scientific_jury_service), 'scientific_jury_service')
        self.assertEqual(students_service + infrastructure_mgmt_service + events_organisation_service +
                         publishing_field_service + scientific_jury_service,
                         export_utils_pdf.get_service_activities(self.mandate))


    def test_get_formation_activities(self):
        formations = format_data(self.mandate.formations, 'formations')
        self.assertEqual(formations, export_utils_pdf.get_formation_activities(self.mandate))

    def test_export_mandates(self):
        file = export_utils_pdf.export_mandates
        self.assertTrue(file)