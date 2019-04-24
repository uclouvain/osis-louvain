##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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

from base.models import academic_calendar
from base.models import academic_year
from base.models import admission_condition
from base.models import authorized_relationship
from base.models import campus
from base.models import certificate_aim
from base.models import education_group
from base.models import education_group_certificate_aim
from base.models import education_group_language
from base.models import education_group_organization
from base.models import education_group_type
from base.models import education_group_year
from base.models import education_group_year_domain
from base.models import education_group_publication_contact
from base.models import entity
from base.models import entity_calendar
from base.models import entity_component_year
from base.models import entity_container_year
from base.models import entity_manager
from base.models import entity_version
from base.models import exam_enrollment
from base.models import external_learning_unit_year
from base.models import external_learning_unit_year
from base.models import external_offer
from base.models import group_element_year
from base.models import hops
from base.models import learning_achievement
from base.models import learning_class_year
from base.models import learning_component_year
from base.models import learning_container
from base.models import learning_container_year
from base.models import learning_unit
from base.models import learning_unit_enrollment
from base.models import learning_unit_year
from base.models import mandatary
from base.models import mandate
from base.models import offer
from base.models import offer_enrollment
from base.models import offer_type
from base.models import offer_year
from base.models import offer_year_calendar
from base.models import offer_year_domain
from base.models import offer_year_entity
from base.models import organization
from base.models import organization_address
from base.models import person
from base.models import person_address
from base.models import person_entity
from base.models import prerequisite
from base.models import prerequisite_item
from base.models import program_manager
from base.models import proposal_learning_unit
from base.models import session_exam
from base.models import session_exam_calendar
from base.models import session_exam_deadline
from base.models import structure
from base.models import structure_address
from base.models import student
from base.models import synchronization
from base.models import teaching_material
from base.models import tutor
