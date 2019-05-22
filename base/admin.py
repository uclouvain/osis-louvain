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
from django.contrib import admin

from base.models import *
from base.models import validation_rule, education_group_achievement, education_group_detailed_achievement

admin.site.register(academic_calendar.AcademicCalendar,
                    academic_calendar.AcademicCalendarAdmin)

admin.site.register(academic_year.AcademicYear,
                    academic_year.AcademicYearAdmin)

admin.site.register(admission_condition.AdmissionCondition,
                    admission_condition.AdmissionConditionAdmin)

admin.site.register(admission_condition.AdmissionConditionLine,
                    admission_condition.AdmissionConditionLineAdmin)

admin.site.register(campus.Campus,
                    campus.CampusAdmin)

admin.site.register(certificate_aim.CertificateAim,
                    certificate_aim.CertificateAimAdmin)

admin.site.register(education_group.EducationGroup,
                    education_group.EducationGroupAdmin)

admin.site.register(education_group_certificate_aim.EducationGroupCertificateAim,
                    education_group_certificate_aim.EducationGroupCertificateAimAdmin)

admin.site.register(education_group_language.EducationGroupLanguage,
                    education_group_language.EducationGroupLanguageAdmin)

admin.site.register(education_group_organization.EducationGroupOrganization,
                    education_group_organization.EducationGroupOrganizationAdmin)

admin.site.register(education_group_type.EducationGroupType,
                    education_group_type.EducationGroupTypeAdmin)

admin.site.register(education_group_year.EducationGroupYear,
                    education_group_year.EducationGroupYearAdmin)

admin.site.register(education_group_year_domain.EducationGroupYearDomain,
                    education_group_year_domain.EducationGroupYearDomainAdmin)

admin.site.register(entity.Entity,
                    entity.EntityAdmin)

admin.site.register(entity_calendar.EntityCalendar,
                    entity_calendar.EntityCalendarAdmin)

admin.site.register(entity_container_year.EntityContainerYear,
                    entity_container_year.EntityContainerYearAdmin)

admin.site.register(entity_manager.EntityManager,
                    entity_manager.EntityManagerAdmin)

admin.site.register(entity_version.EntityVersion,
                    entity_version.EntityVersionAdmin)

admin.site.register(exam_enrollment.ExamEnrollment,
                    exam_enrollment.ExamEnrollmentAdmin)

admin.site.register(exam_enrollment.ExamEnrollmentHistory,
                    exam_enrollment.ExamEnrollmentHistoryAdmin)

admin.site.register(external_learning_unit_year.ExternalLearningUnitYear,
                    external_learning_unit_year.ExternalLearningUnitYearAdmin)

admin.site.register(external_offer.ExternalOffer,
                    external_offer.ExternalOfferAdmin)

admin.site.register(hops.Hops,
                    hops.HopsAdmin)

admin.site.register(group_element_year.GroupElementYear,
                    group_element_year.GroupElementYearAdmin)

admin.site.register(learning_achievement.LearningAchievement,
                    learning_achievement.LearningAchievementAdmin)

admin.site.register(learning_class_year.LearningClassYear,
                    learning_class_year.LearningClassYearAdmin)

admin.site.register(learning_component_year.LearningComponentYear,
                    learning_component_year.LearningComponentYearAdmin)

admin.site.register(learning_container.LearningContainer,
                    learning_container.LearningContainerAdmin)

admin.site.register(learning_container_year.LearningContainerYear,
                    learning_container_year.LearningContainerYearAdmin)

admin.site.register(learning_unit.LearningUnit,
                    learning_unit.LearningUnitAdmin)

admin.site.register(learning_unit_enrollment.LearningUnitEnrollment,
                    learning_unit_enrollment.LearningUnitEnrollmentAdmin)

admin.site.register(learning_unit_year.LearningUnitYear,
                    learning_unit_year.LearningUnitYearAdmin)

admin.site.register(mandatary.Mandatary,
                    mandatary.MandataryAdmin)

admin.site.register(mandate.Mandate,
                    mandate.MandateAdmin)

admin.site.register(offer_enrollment.OfferEnrollment,
                    offer_enrollment.OfferEnrollmentAdmin)

admin.site.register(offer.Offer,
                    offer.OfferAdmin)

admin.site.register(offer_type.OfferType,
                    offer_type.OfferTypeAdmin)

admin.site.register(offer_year.OfferYear,
                    offer_year.OfferYearAdmin)

admin.site.register(offer_year_calendar.OfferYearCalendar,
                    offer_year_calendar.OfferYearCalendarAdmin)

admin.site.register(offer_year_domain.OfferYearDomain,
                    offer_year_domain.OfferYearDomainAdmin)

admin.site.register(offer_year_entity.OfferYearEntity,
                    offer_year_entity.OfferYearEntityAdmin)

admin.site.register(organization.Organization,
                    organization.OrganizationAdmin)

admin.site.register(organization_address.OrganizationAddress,
                    organization_address.OrganizationAddressAdmin)

admin.site.register(person.Person,
                    person.PersonAdmin)

admin.site.register(person_address.PersonAddress,
                    person_address.PersonAddressAdmin)

admin.site.register(person_entity.PersonEntity,
                    person_entity.PersonEntityAdmin)

admin.site.register(prerequisite.Prerequisite,
                    prerequisite.PrerequisiteAdmin)

admin.site.register(prerequisite_item.PrerequisiteItem,
                    prerequisite_item.PrerequisiteItemAdmin)

admin.site.register(program_manager.ProgramManager,
                    program_manager.ProgramManagerAdmin)

admin.site.register(proposal_learning_unit.ProposalLearningUnit,
                    proposal_learning_unit.ProposalLearningUnitAdmin)

admin.site.register(session_exam.SessionExam,
                    session_exam.SessionExamAdmin)

admin.site.register(session_exam_calendar.SessionExamCalendar,
                    session_exam_calendar.SessionExamCalendarAdmin)

admin.site.register(session_exam_deadline.SessionExamDeadline,
                    session_exam_deadline.SessionExamDeadlineAdmin)

admin.site.register(structure_address.StructureAddress,
                    structure_address.StructureAddressAdmin)

admin.site.register(structure.Structure,
                    structure.StructureAdmin)

admin.site.register(student.Student,
                    student.StudentAdmin)

admin.site.register(synchronization.Synchronization,
                    synchronization.SynchronizationAdmin)

admin.site.register(teaching_material.TeachingMaterial,
                    teaching_material.TeachingMaterialAdmin)

admin.site.register(tutor.Tutor,
                    tutor.TutorAdmin)

admin.site.register(authorized_relationship.AuthorizedRelationship,
                    authorized_relationship.AuthorizedRelationshipAdmin)

admin.site.register(validation_rule.ValidationRule,
                    validation_rule.ValidationRuleAdmin)

admin.site.register(education_group_achievement.EducationGroupAchievement,
                    education_group_achievement.EducationGroupAchievementAdmin)

admin.site.register(education_group_detailed_achievement.EducationGroupDetailedAchievement,
                    education_group_detailed_achievement.EducationGroupDetailedAchievementAdmin)

admin.site.register(education_group_publication_contact.EducationGroupPublicationContact,
                    education_group_publication_contact.EducationGroupPublicationContactAdmin)
