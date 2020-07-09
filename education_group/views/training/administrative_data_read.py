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
from django.db.models import F
from django.shortcuts import redirect
from django.urls import reverse

from base.models.education_group_year import EducationGroupYear
from base.models.enums import academic_calendar_type
from base.models.enums.mandate_type import MandateTypes
from base.models.mandatary import Mandatary
from base.models.offer_year_calendar import OfferYearCalendar
from base.models.program_manager import ProgramManager
from education_group.views.serializers import training_administrative_dates as serializer
from education_group.views.training.common_read import TrainingRead, Tab


class TrainingReadAdministrativeData(TrainingRead):
    template_name = "education_group_app/training/administrative_data.html"
    active_tab = Tab.ADMINISTRATIVE_DATA

    def get(self, request, *args, **kwargs):
        if not self.have_administrative_data_tab():
            return redirect(reverse('training_identification', kwargs=self.kwargs))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        offer_acronym = self.get_object().title
        year = self.get_object().year
        return {
            **super().get_context_data(**kwargs),
            "children": self.get_object().children,
            "learning_unit_enrollment_dates": self.__get_learning_unit_enrollment_date(),
            "administrative_dates": serializer.get_session_dates(offer_acronym, year),
            "additional_informations": self.__get_complementary_informations(),
            "mandataries": self.__get_mandataries(),
            "program_managers": self.__get_program_managers()
        }

    def __get_learning_unit_enrollment_date(self) -> OfferYearCalendar:
        return OfferYearCalendar.objects.filter(
            education_group_year__acronym=self.get_object().title,
            education_group_year__academic_year__year=self.get_object().year,
            academic_calendar__reference=academic_calendar_type.COURSE_ENROLLMENT,
        ).first()

    def __get_complementary_informations(self):
        qs = EducationGroupYear.objects.filter(
            acronym=self.training_identity.acronym, academic_year__year=self.training_identity.year
        ).values('weighting', 'default_learning_unit_enrollment')
        return {
            'weighting': qs[0]['weighting'],
            'has_learning_unit_default_enrollment': qs[0]['default_learning_unit_enrollment'],
        }

    def __get_mandataries(self):
        qs = Mandatary.objects.filter(
            mandate__education_group__educationgroupyear__acronym=self.get_object().title,
            mandate__education_group__educationgroupyear__academic_year__year=self.get_object().year,
            start_date__lte=F('mandate__education_group__educationgroupyear__academic_year__end_date'),
            end_date__gte=F('mandate__education_group__educationgroupyear__academic_year__start_date')
        ).order_by(
            'mandate__function',
            'person__last_name',
            'person__first_name'
        ).annotate(
            function=F('mandate__function'),
            qualification=F('mandate__qualification'),
            first_name=F('person__first_name'),
            middle_name=F('person__middle_name'),
            last_name=F('person__last_name'),
            # function=Value(MandateTypes[F('mandate__function')])
        ).values(
            'function',
            'qualification',
            'first_name',
            'middle_name',
            'last_name',
        )
        for values in qs:
            values['function'] = MandateTypes[values['function']]
        return qs

    def __get_program_managers(self):
        return ProgramManager.objects.filter(
            education_group__educationgroupyear__acronym=self.get_object().title,
            education_group__educationgroupyear__academic_year__year=self.get_object().year,
        ).order_by("person__last_name", "person__first_name")
