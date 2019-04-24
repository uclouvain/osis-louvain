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
from django.utils.translation import ugettext_lazy as _

from assistant.models import tutoring_learning_unit_year
from attribution.models.attribution import Attribution
from attribution.models.attribution_charge_new import AttributionChargeNew
from attribution.models.attribution_new import AttributionNew
from base.business.learning_unit import CMS_LABEL_SPECIFICATIONS, CMS_LABEL_PEDAGOGY, CMS_LABEL_SUMMARY
from base.models import learning_unit_enrollment, learning_class_year, learning_unit_year as learn_unit_year_model
from base.models import proposal_learning_unit
from cms.enums import entity_name
from cms.models import translated_text


def check_learning_unit_deletion(learning_unit, check_proposal=True):
    msg = {}

    for learning_unit_year in learn_unit_year_model.search(learning_unit=learning_unit).order_by('academic_year__year'):
        msg.update(check_learning_unit_year_deletion(learning_unit_year, check_proposal=check_proposal))

    return msg


def check_learning_unit_year_deletion(learning_unit_year, check_proposal=True):
    msg = {}

    if check_proposal:
        msg.update(_check_learning_unit_proposal(learning_unit_year))
    msg.update(check_can_delete_ignoring_proposal_validation(learning_unit_year))
    return msg


def _check_tutoring_learning_unit_year(tutoring):
    msg = {}

    if tutoring.mandate:
        msg[tutoring] = _(
            "%(subtype)s %(acronym)s is assigned to the assistant %(assistant)s for the year %(year)s") % {
                            'subtype': _str_partim_or_full(tutoring.learning_unit_year),
                            'acronym': tutoring.learning_unit_year.acronym,
                            'assistant': tutoring.mandate.assistant,
                            'year': tutoring.learning_unit_year.academic_year}

    return msg


def _check_group_element_year_deletion(group_element_year):
    if not group_element_year.parent:
        return {}

    return {
        group_element_year: _('%(subtype)s %(acronym)s is included in the group %(group)s for the year %(year)s') % {
            'subtype': _str_partim_or_full(group_element_year.child_leaf),
            'acronym': group_element_year.child_leaf.acronym,
            'group': group_element_year.parent.partial_acronym,
            'year': group_element_year.child_leaf.academic_year
        }
        }


def _check_attribution_deletion(learning_unit_year):
    msg = {}
    error_attribution = "%(subtype)s %(acronym)s is assigned to %(tutor)s for the year %(year)s"

    for attribution in Attribution.objects.filter(learning_unit_year=learning_unit_year):
        msg[attribution] = _(error_attribution) % {
            'subtype': _str_partim_or_full(learning_unit_year),
            'acronym': learning_unit_year.acronym,
            'tutor': attribution.tutor,
            'year': learning_unit_year.academic_year}

    for attribution_new in AttributionNew.objects.filter(
            learning_container_year=learning_unit_year.learning_container_year,
            attributionchargenew__learning_component_year__learning_unit_year=learning_unit_year
    ):
        msg[attribution_new] = _(error_attribution) % {
            'subtype': _str_partim_or_full(learning_unit_year),
            'acronym': learning_unit_year.acronym,
            'tutor': attribution_new.tutor,
            'year': learning_unit_year.academic_year}

    return msg


def _check_learning_component_deletion(learning_component_year):
    msg = {}

    for attribution_charge in \
            AttributionChargeNew.objects.filter(learning_component_year=learning_component_year):
        attribution = attribution_charge.attribution
        msg[attribution] = _("%(subtype)s %(acronym)s is assigned to %(tutor)s for the year %(year)s") % {
            'subtype': _str_partim_or_full(learning_component_year.learning_unit_year),
            'acronym': learning_component_year.learning_unit_year.acronym,
            'tutor': attribution.tutor,
            'year': learning_component_year.learning_unit_year.academic_year}

    return msg


def _check_learning_unit_proposal(learning_unit_year):
    msg = {}

    proposal = proposal_learning_unit.find_by_learning_unit_year(learning_unit_year)
    if proposal:
        error_proposal = "%(subtype)s %(acronym)s is in proposal for the year %(year)s"
        msg[proposal] = _(error_proposal) % {'subtype': _str_partim_or_full(proposal.learning_unit_year),
                                             'acronym': proposal.learning_unit_year.acronym,
                                             'year': proposal.learning_unit_year.academic_year}
    return msg


def _check_related_partims_deletion(learning_container_year):
    msg = {}

    for partim in learning_container_year.get_partims_related():
        msg.update(check_learning_unit_year_deletion(partim))

    return msg


def delete_learning_unit(learning_unit):
    msg = []

    first_learning_unit_year_to_delete = learn_unit_year_model.search(learning_unit=learning_unit) \
        .order_by('academic_year__year').first()
    if first_learning_unit_year_to_delete:
        msg.extend(delete_from_given_learning_unit_year(first_learning_unit_year_to_delete))

    learning_unit.delete()

    return msg


def delete_from_given_learning_unit_year(learning_unit_year):
    msg = []

    next_year = learning_unit_year.get_learning_unit_next_year()
    if next_year:
        msg.extend(delete_from_given_learning_unit_year(next_year))

    if learning_unit_year.learning_container_year and learning_unit_year.is_full():
        msg.extend(_delete_learning_container_year(learning_unit_year.learning_container_year))

    for component in learning_unit_year.learningcomponentyear_set.all():
        msg.extend(_delete_learning_component_year(component))

    _delete_cms_data(learning_unit_year)

    _decrement_end_year_learning_unit(learning_unit_year)

    learning_unit_year.delete()

    msg.append(create_learning_unit_year_deletion_message(learning_unit_year))
    return msg


def _decrement_end_year_learning_unit(learning_unit_year):
    learning_unit_to_edit = learning_unit_year.learning_unit

    start_year = learning_unit_to_edit.start_year
    new_end_year = learning_unit_year.academic_year.year - 1
    if new_end_year >= start_year:
        learning_unit_to_edit.end_year = new_end_year
        learning_unit_to_edit.save()


def _delete_learning_container_year(learning_unit_container):
    msg = []

    for partim in learning_unit_container.get_partims_related():
        msg.extend(delete_from_given_learning_unit_year(partim))
    learning_unit_container.delete()

    return msg


def _delete_learning_component_year(learning_component_year):
    msg = []

    for l_class_year in learning_class_year.find_by_learning_component_year(learning_component_year):
        l_class_year.delete()
        msg.append(_("The class %(acronym)s has been deleted for the year %(year)s")
                   % {'acronym': l_class_year,
                      'year': learning_component_year.learning_container_year.academic_year})
    learning_component_year.delete()

    return msg


def _str_partim_or_full(learning_unit_year):
    return _('The partim') if learning_unit_year.is_partim() else _('The learning unit')


def _delete_cms_data(learning_unit_year):
    text_label_names = CMS_LABEL_SPECIFICATIONS + CMS_LABEL_PEDAGOGY + CMS_LABEL_SUMMARY
    for learning_unit_cms_data in translated_text.search(entity=entity_name.LEARNING_UNIT_YEAR,
                                                         reference=learning_unit_year.id,
                                                         text_labels_name=text_label_names):
        learning_unit_cms_data.delete()


def check_can_delete_ignoring_proposal_validation(learning_unit_year):
    msg = {}
    enrollment_count = len(learning_unit_enrollment.find_by_learning_unit_year(learning_unit_year))
    if enrollment_count > 0:
        msg[learning_unit_year] = _("There is %(count)d enrollments in %(subtype)s %(acronym)s for the year %(year)s") \
                                  % {'subtype': _str_partim_or_full(learning_unit_year),
                                     'acronym': learning_unit_year.acronym,
                                     'year': learning_unit_year.academic_year,
                                     'count': enrollment_count}
    if learning_unit_year.is_full() and learning_unit_year.learning_container_year:
        msg.update(_check_related_partims_deletion(learning_unit_year.learning_container_year))
    msg.update(_check_attribution_deletion(learning_unit_year))
    components = learning_unit_year.learningcomponentyear_set.all().select_related('learning_unit_year__academic_year')
    for component in components:
        msg.update(_check_learning_component_deletion(component))
    for group_element_year in learning_unit_year.find_list_group_element_year():
        msg.update(_check_group_element_year_deletion(group_element_year))
    msg.update(check_tutorings_deletion(learning_unit_year))
    next_year = learning_unit_year.get_learning_unit_next_year()
    if next_year:
        msg.update(check_learning_unit_year_deletion(next_year))
    return msg


def check_tutorings_deletion(learning_unit_year):
    msg = {}
    for tutoring in tutoring_learning_unit_year.find_learning_unit_year(learning_unit_year=learning_unit_year):
        msg.update(_check_tutoring_learning_unit_year(tutoring))
    return msg


def create_learning_unit_year_deletion_message(learning_unit_year_deleted):
    return _('Learning unit %(acronym)s (%(academic_year)s) successfuly deleted.') % {
        'acronym': learning_unit_year_deleted.acronym,
        'academic_year': learning_unit_year_deleted.academic_year,
    }
