# ##################################################################################################
#  OSIS stands for Open Student Information System. It's an application                            #
#  designed to manage the core business of higher education institutions,                          #
#  such as universities, faculties, institutes and professional schools.                           #
#  The core business involves the administration of students, teachers,                            #
#  courses, programs and so on.                                                                    #
#                                                                                                  #
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)              #
#                                                                                                  #
#  This program is free software: you can redistribute it and/or modify                            #
#  it under the terms of the GNU General Public License as published by                            #
#  the Free Software Foundation, either version 3 of the License, or                               #
#  (at your option) any later version.                                                             #
#                                                                                                  #
#  This program is distributed in the hope that it will be useful,                                 #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of                                  #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                                   #
#  GNU General Public License for more details.                                                    #
#                                                                                                  #
#  A copy of this license - GNU General Public License - is available                              #
#  at the root of the source code of this program.  If not,                                        #
#  see http://www.gnu.org/licenses/.                                                               #
# ##################################################################################################
from django.db.models import Exists, OuterRef
from django.utils.translation import gettext as _

from base.business.learning_units.edition import duplicate_learning_unit_year
from base.business.utils.postponement import AutomaticPostponementToN6
from base.models.enums import proposal_type
from base.models.learning_unit import LearningUnit
from base.models.learning_unit_year import LearningUnitYear
from base.utils.send_mail import send_mail_before_annual_procedure_of_automatic_postponement_of_luy, \
    send_mail_after_annual_procedure_of_automatic_postponement_of_luy


class LearningUnitAutomaticPostponementToN6(AutomaticPostponementToN6):
    model = LearningUnit
    annualized_set = "learningunityear"

    send_before = send_mail_before_annual_procedure_of_automatic_postponement_of_luy
    send_after = send_mail_after_annual_procedure_of_automatic_postponement_of_luy
    extend_method = duplicate_learning_unit_year
    msg_result = _("%(number_extended)s learning unit(s) extended and %(number_error)s error(s)")

    def get_queryset(self, queryset=None):
        learning_unit_year_with_containers = LearningUnitYear.objects.filter(
            learning_unit=OuterRef("pk"),
            learning_container_year__isnull=False,
            academic_year__year__gte=self.current_year.year
        )
        external_learning_unit_year_that_are_not_mobility = LearningUnitYear.objects.filter(
            learning_unit=OuterRef("pk"),
            externallearningunityear__mobility=True,
            academic_year__year__gte=self.current_year.year
        )
        creation_proposal = LearningUnitYear.objects.filter(
            learning_unit=OuterRef("pk"),
            proposallearningunit__type=proposal_type.ProposalType.CREATION.name
        )
        return super().get_queryset(queryset).annotate(
            has_container=Exists(learning_unit_year_with_containers),
            is_mobility=Exists(external_learning_unit_year_that_are_not_mobility),
            is_a_creation_proposal=Exists(creation_proposal),
        ).filter(
            has_container=True,
            is_mobility=False,
            is_a_creation_proposal=False,
        )

    def get_object_to_copy(self, object_to_duplicate):
        return getattr(
            object_to_duplicate,
            self.annualized_set + "_set"
        ).filter(
            proposallearningunit__isnull=True
        ).latest(
            'academic_year__year'
        )
