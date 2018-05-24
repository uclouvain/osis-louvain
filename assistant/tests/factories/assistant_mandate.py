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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import factory
import factory.fuzzy
import datetime
from base.tests.factories.academic_year import AcademicYearFactory
from assistant.models.enums import assistant_type, assistant_mandate_renewal, assistant_mandate_state
from assistant.models.enums import assistant_mandate_appeal
from assistant.tests.factories.academic_assistant import AcademicAssistantFactory


class AssistantMandateFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'assistant.AssistantMandate'

    assistant = factory.SubFactory(AcademicAssistantFactory)
    if datetime.date.today() < datetime.date(datetime.date.today().year, 9, 15):
        academic_year = factory.SubFactory(AcademicYearFactory, year=datetime.date.today().year-1)
    else:
        academic_year = factory.SubFactory(AcademicYearFactory, year=datetime.date.today().year)
    assistant_type = factory.Iterator(assistant_type.ASSISTANT_TYPES, getter=lambda c: c[0])
    fulltime_equivalent = factory.fuzzy.FuzzyChoice([0.25, 0.33, 0.5, 0.75, 1])
    entry_date = datetime.datetime(datetime.date.today().year - 2, 9, 15)
    end_date = datetime.datetime(datetime.date.today().year, 9, 14)
    sap_id = factory.Faker('text', max_nb_chars=7)
    renewal_type = factory.Iterator(assistant_mandate_renewal.ASSISTANT_MANDATE_RENEWAL_TYPES, getter=lambda c: c[0])
    state = factory.Iterator(assistant_mandate_state.ASSISTANT_MANDATE_STATES, getter=lambda c: c[0])
    scale = factory.fuzzy.FuzzyChoice(['021', '502', '020', '023'])
    research_percent = 0
    tutoring_percent = 0
    service_activities_percent = 0
    formation_activities_percent = 0
    faculty_representation = 0
    institute_representation = 0
    sector_representation = 0
    governing_body_representation = 0
    corsci_representation = 0
    students_service = 0
    infrastructure_mgmt_service = 0
    events_organisation_service = 0
    publishing_field_service = 0
    scientific_jury_service = 0
    appeal = assistant_mandate_appeal.NONE
    special = False
    contract_duration = str(int(end_date.year) - int(entry_date.year))
    contract_duration_fte = contract_duration
