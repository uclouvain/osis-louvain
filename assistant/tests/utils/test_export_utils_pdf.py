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
from django.test import TestCase, RequestFactory
from reportlab.lib.styles import getSampleStyleSheet
from base.models.entity import find_versions_from_entites
from assistant.utils import export_utils_pdf
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

    def test_get_administrative_data(self):
        assistant_type = "<strong>%s :</strong> %s<br />" % (_('assistant_type'), _(self.mandate.assistant_type))
        matricule = "<strong>%s :</strong> %s<br />" % (_('matricule_number'), self.mandate.sap_id)
        entry_date = "<strong>%s :</strong> %s<br />" % (
        _('entry_date_contract'), self.mandate.entry_date.strftime("%d-%m-%Y"))
        end_date = "<strong>%s :</strong> %s<br />" % (_('end_date_contract'),
                                                       self.mandate.end_date.strftime("%d-%m-%Y"))
        contract_duration = "<strong>%s :</strong> %s<br />" % (_('contract_duration'), self.mandate.contract_duration)
        contract_duration_fte = "<strong>%s :</strong> %s<br />" % (_('contract_duration_fte'),
                                                                    self.mandate.contract_duration_fte)
        fulltime_equivalent = "<strong>%s :</strong> %s" % (_('fulltime_equivalent_percentage'),
                                                            int(self.mandate.fulltime_equivalent * 100)) + "%<br />"
        other_status = "<strong>%s :</strong> %s<br />" % (_('other_status'), self.mandate.other_status) \
            if self.mandate.other_status else "<strong>%s :</strong><br />" % (_('other_status'))
        renewal_type = "<strong>%s :</strong> %s<br />" % (_('renewal_type'), _(self.mandate.renewal_type))
        justification = "<strong>%s :</strong> %s<br />" % (_('exceptional_justification'), self.mandate.justification) \
            if self.mandate.justification else "<strong>%s :</strong><br />" % (_('exceptional_justification'))
        external_contract = "<strong>%s :</strong> %s<br />" % (_('external_post'), self.mandate.external_contract) \
            if self.mandate.external_contract else "<strong>%s :</strong><br />" % (_('external_post'))
        external_functions = "<strong>%s :</strong> %s<br />" % (_('function_outside_university'),
                                                                 self.mandate.external_functions) \
            if self.mandate.external_functions else "<strong>%s :</strong><br />" % (_('function_outside_university'))
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
        thesis_title = "<strong>%s :</strong> %s<br />" % (_('thesis_title'), _(self.assistant.thesis_title)) \
            if self.assistant.thesis_title else "<strong>%s :</strong><br />" % (_('thesis_title'))
        phd_inscription_date = "<strong>%s :</strong> %s<br />" % (_('phd_inscription_date'),
                                                                   self.assistant.phd_inscription_date.strftime(
                                                                       "%d-%m-%Y")) \
            if self.assistant.phd_inscription_date else "<strong>%s :</strong><br />" % (_('phd_inscription_date'))
        confirmation_test_date = "<strong>%s :</strong> %s<br />" % (_('confirmatory_test_date'),
                                                                     self.assistant.confirmation_test_date.strftime(
                                                                         "%d-%m-%Y")) \
            if self.assistant.confirmation_test_date else "<strong>%s :</strong><br />" % (_('confirmatory_test_date'))
        thesis_date = "<strong>%s :</strong> %s<br />" % (_('thesis_defence_date'),
                                                          self.assistant.thesis_date.strftime("%d-%m-%Y")) \
            if self.assistant.thesis_date else "<strong>%s :</strong><br />" % (_('thesis_defence_date'))
        expected_phd_date = "<strong>%s :</strong> %s<br />" % (_('expected_registering_date'),
                                                                self.assistant.expected_phd_date.strftime("%d-%m-%Y")) \
            if self.assistant.expected_phd_date else "<strong>%s :</strong><br />" % (_('expected_registering_date'))
        inscription = "<strong>%s :</strong> %s<br />" % (_('registered_phd'), _(self.assistant.inscription)) \
            if self.assistant.inscription else "<strong>%s :</strong><br />" % (_('registered_phd'))
        remark = "<strong>%s :</strong> %s<br />" % (_('remark'), _(self.assistant.remark)) \
            if self.assistant.remark else "<strong>%s :</strong><br />" % (_('remark'))
        self.assertEqual(inscription + phd_inscription_date + expected_phd_date + confirmation_test_date + thesis_title \
               + thesis_date + remark, export_utils_pdf.get_phd_data(self.assistant))


    def test_get_research_data(self):
        internships = "<strong>%s :</strong> %s<br />" % (_('scientific_internships'), _(self.mandate.internships)) \
            if self.mandate.internships else "<strong>%s :</strong><br />" % (_('scientific_internships'))
        conferences = "<strong>%s :</strong> %s<br />" % (_('conferences_contributor'), _(self.mandate.conferences)) \
            if self.mandate.conferences else "<strong>%s :</strong><br />" % (_('conferences_contributor'))
        publications = "<strong>%s :</strong> %s<br />" % (_('publications_in_progress'), _(self.mandate.publications)) \
            if self.mandate.publications else "<strong>%s :</strong><br />" % (_('publications_in_progress'))
        awards = "<strong>%s :</strong> %s<br />" % (_('awards'), _(self.mandate.awards)) \
            if self.mandate.awards else "<strong>%s :</strong><br />" % (_('awards'))
        framing = "<strong>%s :</strong> %s<br />" % (_('framing_participation'), _(self.mandate.framing)) \
            if self.mandate.framing else "<strong>%s :</strong><br />" % (_('framing_participation'))
        remark = "<strong>%s :</strong> %s<br />" % (_('remark'), _(self.mandate.remark)) \
            if self.mandate.remark else "<strong>%s :</strong><br />" % (_('remark'))
        self.assertEqual(internships + conferences + publications + awards + framing + remark,
                         export_utils_pdf.get_research_data(self.mandate))


    def test_get_representation_activities(self):
        faculty_representation = "<strong>%s :</strong> %s<br />" % (_('faculty_representation'),
                                                                     str(self.mandate.faculty_representation))
        institute_representation = "<strong>%s :</strong> %s<br />" % (_('institute_representation'),
                                                                       str(self.mandate.institute_representation))
        sector_representation = "<strong>%s :</strong> %s<br />" % (_('sector_representation'),
                                                                    str(self.mandate.sector_representation))
        governing_body_representation = "<strong>%s :</strong> %s<br />" \
                                        % (_('governing_body_representation'),
                                           str(self.mandate.governing_body_representation))
        corsci_representation = "<strong>%s :</strong> %s<br />" % (_('corsci_representation'),
                                                                    str(self.mandate.corsci_representation))
        self.assertEqual(faculty_representation + institute_representation + sector_representation +
                         governing_body_representation + corsci_representation,
                         export_utils_pdf.get_representation_activities(self.mandate))


    def test_get_summary(self):
        report_remark = "<strong>%s :</strong> %s<br />" % (
        _('activities_report_remark'), self.mandate.activities_report_remark) \
            if self.mandate.activities_report_remark != 'None' and self.mandate.activities_report_remark else ''
        self.assertEqual(report_remark, export_utils_pdf.get_summary(self.mandate))


    def test_get_service_activities(self):
        students_service = "<strong>%s :</strong> %s<br />" % (_('students_service'), str(self.mandate.students_service))
        infrastructure_mgmt_service = "<strong>%s :</strong> %s<br />" % (_('infrastructure_mgmt_service'),
                                                                          str(self.mandate.infrastructure_mgmt_service))
        events_organisation_service = "<strong>%s :</strong> %s<br />" % (_('events_organisation_service'),
                                                                          str(self.mandate.events_organisation_service))
        publishing_field_service = "<strong>%s :</strong> %s<br />" % (_('publishing_field_service'),
                                                                       str(self.mandate.publishing_field_service))
        scientific_jury_service = "<strong>%s :</strong> %s<br />" % (_('scientific_jury_service'),
                                                                      str(self.mandate.scientific_jury_service))
        self.assertEqual(students_service + infrastructure_mgmt_service + events_organisation_service +
                         publishing_field_service + scientific_jury_service,
                         export_utils_pdf.get_service_activities(self.mandate))


    def test_get_formation_activities(self):
        formations = "<strong>%s :</strong> %s<br />" % (_('formations'), self.mandate.formations)
        self.assertEqual(formations, export_utils_pdf.get_formation_activities(self.mandate))


