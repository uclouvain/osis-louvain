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
from django.utils.translation import ugettext_lazy as _
from django.test import TestCase, RequestFactory, Client
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.units import mm
from base.models.entity import find_versions_from_entites
from base.models.entity_version import get_last_version

from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from assistant.models import tutoring_learning_unit_year
from assistant.models.review import find_by_mandate
from assistant.utils import export_utils_pdf
from assistant.tests.factories.academic_assistant import AcademicAssistantFactory
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.manager import ManagerFactory
from assistant.tests.factories.mandate_entity import MandateEntityFactory
from assistant.tests.factories.reviewer import ReviewerFactory
from assistant.tests.factories.review import ReviewFactory
from assistant.tests.factories.settings import SettingsFactory
from assistant.tests.factories.tutoring_learning_unit_year import TutoringLearningUnitYearFactory
from assistant.models.enums import assistant_type, assistant_mandate_renewal, review_status

COLS_WIDTH_FOR_REVIEWS = [35*mm, 20*mm, 70*mm, 30*mm, 30*mm]
COLS_WIDTH_FOR_TUTORING = [40*mm, 15*mm, 15*mm, 15*mm, 15*mm, 15*mm, 15*mm, 15*mm, 40*mm]
HTTP_OK = 200


class ExportPdfTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.settings = SettingsFactory()
        self.manager = ManagerFactory()
        self.factory = RequestFactory()
        self.supervisor = PersonFactory()
        self.assistant = AcademicAssistantFactory(
            phd_inscription_date=datetime.date(2015, 10, 2),
            thesis_title='Data fitting on manifolds',
            confirmation_test_date=datetime.date(2017, 9, 25),
            remark="Deux co-promoteurs (l'application ne m'autorise à n'en renseigner qu'un)",
            supervisor=self.supervisor
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
        self.tutoring_learning_unit_year = TutoringLearningUnitYearFactory(mandate=self.mandate)
        self.review3 = ReviewFactory(
            mandate=self.mandate,
            reviewer=None
        )
        self.entity_version = EntityVersionFactory()
        self.mandate_entity = MandateEntityFactory(
            assistant_mandate=self.mandate,
            entity=self.entity_version.entity
        )
        self.entity_version2 = EntityVersionFactory()
        self.mandate_entity2 = MandateEntityFactory(
            assistant_mandate=self.mandate,
            entity=self.entity_version2.entity
        )
        self.reviewer = ReviewerFactory(
            entity=self.mandate_entity.entity
        )

        self.reviewer2 = ReviewerFactory(
            entity=self.mandate_entity2.entity
        )
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(
            name='Tiny',
            fontSize=6,
            font='Helvetica',
            leading=8,
            leftIndent=0,
            rightIndent=0,
            firstLineIndent=0,
            alignment=TA_LEFT,
            spaceBefore=0,
            spaceAfter=0,
            splitLongWords=1,
        ))
        self.review1 = ReviewFactory(
            mandate=self.mandate,
            reviewer=self.reviewer
        )
        self.review2 = ReviewFactory(
            mandate=self.mandate,
            reviewer=self.reviewer2,
            status=review_status.IN_PROGRESS
        )
        self.review3 = ReviewFactory(
            mandate=self.mandate,
            reviewer=None
        )

    def test_export_mandate(self):
        self.client.force_login(self.assistant.person.user)
        response = self.client.post('/assistants/assistant/export_pdf/', {'mandate_id': self.mandate.id})
        self.assertEqual(HTTP_OK, response.status_code)

    def test_export_mandates(self):
        self.client.force_login(self.manager.person.user)
        response = self.client.post('/assistants/manager/mandates/export_pdf/')
        self.assertEqual(HTTP_OK, response.status_code)

    def test_format_data(self):
        data = 'good example of data.'
        title = 'formations'
        self.assertEqual("<strong>%s :</strong> %s<br />" % (_(title), data), export_utils_pdf.format_data(data, title))

    def test_create_paragraph(self):
        data = 'good example of data.'
        title = 'formations'
        subtitle = 'my subtitle'
        style = self.styles['BodyText']
        paragraph = Paragraph("<font size=14><strong>" + title + "</strong></font>" +
                              subtitle + "<br />" + data, style)
        self.assertEqual(str(export_utils_pdf.create_paragraph(title, data, style, subtitle)), str(paragraph))

    def test_get_administrative_data(self):
        assistant_type = export_utils_pdf.format_data(_(self.mandate.assistant_type), 'assistant_type')
        matricule = export_utils_pdf.format_data(self.mandate.sap_id, 'matricule_number')
        entry_date = export_utils_pdf.format_data(self.mandate.entry_date, 'entry_date_contract')
        end_date = export_utils_pdf.format_data(self.mandate.end_date, 'end_date_contract')
        contract_duration = export_utils_pdf.format_data(self.mandate.contract_duration, 'contract_duration')
        contract_duration_fte = export_utils_pdf.format_data(
            self.mandate.contract_duration_fte,
            'contract_duration_fte'
        )
        fulltime_equivalent = export_utils_pdf.format_data(int(self.mandate.fulltime_equivalent * 100),
                                                           'fulltime_equivalent_percentage')
        other_status = export_utils_pdf.format_data(self.mandate.other_status, 'other_status')
        renewal_type = export_utils_pdf.format_data(_(self.mandate.renewal_type), 'renewal_type')
        justification = export_utils_pdf.format_data(self.mandate.justification, 'exceptional_justification')
        external_contract = export_utils_pdf.format_data(self.mandate.external_contract, 'external_post')
        external_functions = export_utils_pdf.format_data(
            self.mandate.external_functions,
            'function_outside_university'
        )
        self.assertEqual(
            assistant_type + matricule + entry_date + end_date + contract_duration + contract_duration_fte
            + fulltime_equivalent + other_status + renewal_type + justification + external_contract +
            external_functions,
            export_utils_pdf.get_administrative_data(self.mandate)
        )

    def test_get_entities(self):
        entities_id = self.mandate.mandateentity_set.all().order_by('id').values_list('entity', flat=True)
        entities = find_versions_from_entites(entities_id, self.mandate.academic_year.start_date)
        entities_data = ""
        for entity in entities:
            entities_data += "<strong>{} : </strong>{}<br />".format(_(entity.entity_type), entity.acronym)
        self.assertEqual(entities_data, export_utils_pdf.get_entities(self.mandate))

    def test_get_absences(self):
        self.assertEqual(self.mandate.absences if self.mandate.absences else "",
                         export_utils_pdf.get_absences(self.mandate))

    def test_get_comment(self):
        self.assertEqual(self.mandate.comment if self.mandate.comment else "",
                         export_utils_pdf.get_comment(self.mandate))

    def test_get_phd_data(self):
        thesis_title = export_utils_pdf.format_data(self.assistant.thesis_title, 'thesis_title')
        phd_inscription_date = export_utils_pdf.format_data(self.assistant.phd_inscription_date, 'phd_inscription_date')
        confirmation_test_date = export_utils_pdf.format_data(self.assistant.confirmation_test_date,
                                                              'confirmatory_test_date')
        thesis_date = export_utils_pdf.format_data(self.assistant.thesis_date, 'thesis_defence_date')
        expected_phd_date = export_utils_pdf.format_data(self.assistant.expected_phd_date, 'expected_registering_date')
        inscription = export_utils_pdf.format_data(_(self.assistant.inscription)
                                                   if self.assistant.inscription else None, 'registered_phd')
        remark = export_utils_pdf.format_data(self.assistant.remark, 'remark')
        self.assertEqual(inscription + phd_inscription_date + expected_phd_date + confirmation_test_date
                         + thesis_title + thesis_date + remark, export_utils_pdf.get_phd_data(self.assistant))

    def test_get_research_data(self):
        internships = export_utils_pdf.format_data(self.mandate.internships, 'scientific_internships')
        conferences = export_utils_pdf.format_data(self.mandate.conferences, 'conferences_contributor')
        publications = export_utils_pdf.format_data(self.mandate.publications, 'publications_in_progress')
        awards = export_utils_pdf.format_data(self.mandate.awards, 'awards')
        framing = export_utils_pdf.format_data(self.mandate.framing, 'framing_participation')
        remark = export_utils_pdf.format_data(self.mandate.remark, 'remark')
        self.assertEqual(internships + conferences + publications + awards + framing + remark,
                         export_utils_pdf.get_research_data(self.mandate))

    def test_get_representation_activities(self):
        faculty_representation = export_utils_pdf.format_data(
            str(self.mandate.faculty_representation),
            'faculty_representation'
        )
        institute_representation = export_utils_pdf.format_data(
            str(self.mandate.institute_representation),
            'institute_representation'
        )
        sector_representation = export_utils_pdf.format_data(
            str(self.mandate.sector_representation),
            'sector_representation'
        )
        governing_body_representation = export_utils_pdf.format_data(
            str(self.mandate.governing_body_representation),
            'governing_body_representation'
        )
        corsci_representation = export_utils_pdf.format_data(str(self.mandate.corsci_representation),
                                                             'corsci_representation')
        self.assertEqual(faculty_representation + institute_representation + sector_representation +
                         governing_body_representation + corsci_representation,
                         export_utils_pdf.get_representation_activities(self.mandate))

    def test_get_summary(self):
        report_remark = export_utils_pdf.format_data(self.mandate.activities_report_remark, 'activities_report_remark')
        self.assertEqual(report_remark, export_utils_pdf.get_summary(self.mandate))

    def test_get_service_activities(self):
        students_service = export_utils_pdf.format_data(
            str(self.mandate.students_service),
            'students_service'
        )
        infrastructure_mgmt_service = export_utils_pdf.format_data(
            str(self.mandate.infrastructure_mgmt_service),
            'infrastructure_mgmt_service'
        )
        events_organisation_service = export_utils_pdf.format_data(
            str(self.mandate.events_organisation_service),
            'events_organisation_service'
        )
        publishing_field_service = export_utils_pdf.format_data(
            str(self.mandate.publishing_field_service),
            'publishing_field_service'
        )
        scientific_jury_service = export_utils_pdf.format_data(
            str(self.mandate.scientific_jury_service),
            'scientific_jury_service'
        )
        self.assertEqual(students_service + infrastructure_mgmt_service + events_organisation_service +
                         publishing_field_service + scientific_jury_service,
                         export_utils_pdf.get_service_activities(self.mandate))

    def test_get_formation_activities(self):
        formations = export_utils_pdf.format_data(self.mandate.formations, 'formations')
        self.assertEqual(formations, export_utils_pdf.get_formation_activities(self.mandate))

    def test_generate_headers(self):
        style = self.styles['BodyText']
        data = []
        titles = [
            'tutoring_learning_units', 'academic_year', 'sessions_number', 'sessions_duration', 'series_number',
            'face_to_face_duration', 'attendees', 'exams_supervision_duration', 'others_delivery'
        ]
        for title in titles:
            data.append(Paragraph("%s" % _(title), style))
        self.assertEqual(str([data]), str(export_utils_pdf.generate_headers(titles, style)))

    def test_get_tutoring_learning_unit_year(self):
        style = self.styles['Tiny']
        data = export_utils_pdf.generate_headers([
            'tutoring_learning_units', 'academic_year', 'sessions_number', 'sessions_duration', 'series_number',
            'face_to_face_duration', 'attendees', 'exams_supervision_duration', 'others_delivery'
        ], style)
        tutoring_learning_units_year = tutoring_learning_unit_year.find_by_mandate(self.mandate)
        for this_tutoring_learning_unit_year in tutoring_learning_units_year:
            academic_year = str(this_tutoring_learning_unit_year.learning_unit_year.academic_year)
            data.append([Paragraph(this_tutoring_learning_unit_year.learning_unit_year.complete_title + " (" +
                                   this_tutoring_learning_unit_year.learning_unit_year.acronym + ")", style),
                         Paragraph(academic_year, style),
                         Paragraph(str(this_tutoring_learning_unit_year.sessions_number), style),
                         Paragraph(str(this_tutoring_learning_unit_year.sessions_duration), style),
                         Paragraph(str(this_tutoring_learning_unit_year.series_number), style),
                         Paragraph(str(this_tutoring_learning_unit_year.face_to_face_duration), style),
                         Paragraph(str(this_tutoring_learning_unit_year.attendees), style),
                         Paragraph(str(this_tutoring_learning_unit_year.exams_supervision_duration), style),
                         Paragraph(this_tutoring_learning_unit_year.others_delivery or '', style)
                         ])
        self.assertEqual(str(data), str(export_utils_pdf.get_tutoring_learning_unit_year(self.mandate, style)))

    def test_get_reviews_for_mandate(self):
        style = self.styles['BodyText']
        data = export_utils_pdf.generate_headers(['reviewer', 'review', 'remark', 'justification', 'confidential'],
                                                 style)
        reviews = find_by_mandate(self.mandate.id)
        for rev in reviews:
            if rev.status == review_status.IN_PROGRESS:
                break
            if rev.reviewer is None:
                person = "{} {}<br/>({})".format(
                    self.mandate.assistant.supervisor.first_name,
                    self.mandate.assistant.supervisor.last_name,
                    str(_('supervisor'))
                )
            else:
                person = "{} {}<br/>({})".format(
                    rev.reviewer.person.first_name,
                    rev.reviewer.person.last_name,
                    get_last_version(rev.reviewer.entity).acronym
                )
            data.append([Paragraph(person, style),
                         Paragraph(_(rev.advice), style),
                         Paragraph(rev.remark or '', style),
                         Paragraph(rev.justification or '', style),
                         Paragraph(rev.confidential or '', style)])
        self.assertEqual(str(data), str(export_utils_pdf.get_reviews_for_mandate(self.mandate, style)))
