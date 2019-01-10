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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import json
from collections import OrderedDict, namedtuple

import requests
from ckeditor.widgets import CKEditorWidget
from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.db.models import F, Case, When
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView
from reversion.models import Version

from base import models as mdl
from base.business.education_group import assert_category_of_education_group_year, can_user_edit_administrative_data
from base.business.education_groups import perms, general_information
from base.business.education_groups.group_element_year_tree import NodeBranchJsTree
from base.business.education_groups.perms import is_eligible_to_edit_general_information, \
    is_eligible_to_edit_admission_condition
from base.business.education_groups.general_information import PublishException, RelevantSectionException
from base.management.commands.import_reddot import COMMON_OFFER
from base.models.admission_condition import AdmissionCondition, AdmissionConditionLine
from base.models.education_group_achievement import EducationGroupAchievement
from base.models.education_group_certificate_aim import EducationGroupCertificateAim
from base.models.education_group_detailed_achievement import EducationGroupDetailedAchievement
from base.models.education_group_organization import EducationGroupOrganization
from base.models.education_group_year import EducationGroupYear
from base.models.education_group_year_domain import EducationGroupYearDomain
from base.models.enums import education_group_categories, academic_calendar_type
from base.models.enums.education_group_categories import TRAINING
from base.models.enums.education_group_types import TrainingType, GroupType, MiniTrainingType
from base.models.person import Person
from base.utils.cache import cache
from base.utils.cache_keys import get_tab_lang_keys
from base.views.common import display_error_messages, display_success_messages
from cms import models as mdl_cms
from cms.enums import entity_name
from cms.models.translated_text import TranslatedText
from cms.models.translated_text_label import TranslatedTextLabel
from webservices.business import CONTACTS_KEY, CONTACT_INTRO_KEY

SECTIONS_WITH_TEXT = (
    'ucl_bachelors',
    'others_bachelors_french',
    'bachelors_dutch',
    'foreign_bachelors',
    'graduates',
    'masters'
)

NUMBER_SESSIONS = 3

COMMON_PARAGRAPH = (
    'agregation',
    'finalites_didactiques',
    'prerequis'
)

INTRO_OFFER = (
    TrainingType.MASTER_MS_120.name,
    TrainingType.MASTER_MS_180_240.name,
    TrainingType.MASTER_MD_120.name,
    TrainingType.MASTER_MD_180_240.name,
    TrainingType.MASTER_MA_120.name,
    TrainingType.MASTER_MA_180_240.name,
    GroupType.COMMON_CORE.name,
    GroupType.SUB_GROUP.name,
    MiniTrainingType.OPTION.name
)


@method_decorator(login_required, name='dispatch')
class EducationGroupGenericDetailView(PermissionRequiredMixin, DetailView):
    # DetailView
    model = EducationGroupYear
    context_object_name = "education_group_year"
    pk_url_kwarg = 'education_group_year_id'

    # PermissionRequiredMixin
    permission_required = 'base.can_access_education_group'
    raise_exception = True

    limited_by_category = None

    with_tree = True

    def get_person(self):
        return get_object_or_404(Person.objects.select_related('user'), user=self.request.user)

    def get_root(self):
        return get_object_or_404(EducationGroupYear, pk=self.kwargs.get("root_id"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # This objects are mandatory for all education group views
        context['person'] = self.get_person()

        self.root = self.get_root()
        # FIXME same param
        context['root'] = self.root
        context['root_id'] = self.root.pk
        context['parent'] = self.root
        context['parent_training'] = self.object.parent_by_training()

        if self.with_tree:
            context['tree'] = json.dumps(NodeBranchJsTree(self.root).to_json())

        context['group_to_parent'] = self.request.GET.get("group_to_parent") or '0'
        context['can_change_education_group'] = perms.is_eligible_to_change_education_group(
            person=self.get_person(),
            education_group=context['object'],
        )
        context['enums'] = mdl.enums.education_group_categories

        self.is_intro_offer = self.object.education_group_type.name in INTRO_OFFER
        context['show_extra_info'] = not self.is_intro_offer

        common_offers = ['common-' + offer.lower() for offer in COMMON_OFFER[:-1]]
        context['show_general_info'] = self.object.acronym not in common_offers

        return context

    def get(self, request, *args, **kwargs):
        if self.limited_by_category:
            assert_category_of_education_group_year(self.get_object(), self.limited_by_category)
        return super().get(request, *args, **kwargs)


class EducationGroupRead(EducationGroupGenericDetailView):
    templates = {
        education_group_categories.TRAINING: "education_group/identification_training_details.html",
        education_group_categories.MINI_TRAINING: "education_group/identification_mini_training_details.html",
        education_group_categories.GROUP: "education_group/identification_group_details.html"
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["education_group_languages"] = self.object.educationgrouplanguage_set.order_by('order').values_list(
            'language__name', flat=True)
        context["hide_for_2M"] = self.hide_for_2m()
        context["versions"] = self.get_related_versions()

        return context

    def get_template_names(self):
        return self.templates.get(self.object.education_group_type.category)

    def hide_for_2m(self):
        """Some informations have to be hidden for 2M.
           Co-organization and administrative data doesn't have sense for 2M (120/180-240) """
        return not (self.object.education_group_type.category == TRAINING and
                    self.object.education_group_type.name not in [TrainingType.PGRM_MASTER_120.name,
                                                                  TrainingType.PGRM_MASTER_180_240.name])

    def get_related_versions(self):
        versions = Version.objects.get_for_object(self.object).select_related('revision__user__person')

        related_models = [
            EducationGroupOrganization,
            EducationGroupAchievement,
            EducationGroupDetailedAchievement,
            EducationGroupYearDomain,
            EducationGroupCertificateAim
        ]

        subversion = Version.objects.none()
        for model in related_models:
            subversion |= Version.objects.get_for_model(model).select_related('revision__user__person')

        versions |= subversion.filter(
            serialized_data__contains="\"education_group_year\": {}".format(self.object.pk)
        )

        return versions.order_by('-revision__date_created').distinct('revision__date_created')

    def get_queryset(self):
        """ Optimization """
        return super().get_queryset().select_related(
            'enrollment_campus', 'education_group_type', 'primary_language',
            'main_teaching_campus', 'administration_entity', 'management_entity',
            'academic_year'
        )


class EducationGroupDiplomas(EducationGroupGenericDetailView):
    template_name = "education_group/tab_diplomas.html"
    limited_by_category = (education_group_categories.TRAINING,)

    def get_queryset(self):
        return super().get_queryset().prefetch_related('certificate_aims')


class EducationGroupGeneralInformation(EducationGroupGenericDetailView):
    template_name = "education_group/tab_general_informations.html"

    def get_queryset(self):
        """ Optimization """
        return super().get_queryset().prefetch_related('educationgrouppublicationcontact_set')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_common_education_group_year = self.object.acronym.startswith('common')
        sections_to_display = self.get_appropriate_sections()
        show_contacts = (not sections_to_display or CONTACTS_KEY in sections_to_display) and not self.is_intro_offer
        context.update({
            'is_common_education_group_year': is_common_education_group_year,
            'sections_with_translated_labels': self.get_sections_with_translated_labels(
                sections_to_display,
                is_common_education_group_year,
            ),
            'contacts': self.get_contacts_section(),
            'show_contacts': show_contacts,
            'can_edit_information': is_eligible_to_edit_general_information(context['person'], context['object'])
        })
        return context

    @cached_property
    def user_language_code(self):
        return mdl.person.get_user_interface_language(self.request.user)

    def get_sections_with_translated_labels(self, sections_to_display, is_common_education_group_year=None):
        # Load the info from the common education group year
        common_education_group_year = None
        if not is_common_education_group_year:
            common_education_group_year = EducationGroupYear.objects.get_common(
                academic_year=self.object.academic_year,
            )

        # Load the labels
        Section = namedtuple('Section', 'title labels')
        sections_with_translated_labels = []
        if self.is_intro_offer:
            sections_list = settings.SECTION_INTRO
        else:
            sections_list = settings.SECTION_LIST
        for section in sections_list:
            translated_labels = self.get_translated_labels_and_content(section,
                                                                       self.user_language_code,
                                                                       common_education_group_year,
                                                                       sections_to_display)

            sections_with_translated_labels.append(Section(section.title, translated_labels))
        return sections_with_translated_labels

    def get_translated_labels_and_content(self, section, user_language, common_education_group_year, sections_list):
        records = []
        for label, selectors in section.labels:
            if not sections_list or any(label in section for section in sections_list):
                records.extend(
                    self.get_selectors(common_education_group_year, label, selectors, user_language)
                )
        return records

    def get_selectors(self, common_education_group_year, label, selectors, user_language):
        records = []

        for selector in selectors.split(','):
            translations = None
            if selector == 'specific':
                translations = self.get_content_translations_for_label(
                    self.object, label, user_language, 'specific')

            elif selector == 'common':
                translations = self._get_common_selector(common_education_group_year, label, user_language)

            if translations:
                records.append(translations)

        return records

    def _get_common_selector(self, common_education_group_year, label, user_language):
        translations = None
        # common_education_group_year is None if education_group_year is common
        # if not common, translation must be non-editable in non common offer
        if common_education_group_year is not None:
            translations = self.get_content_translations_for_label(
                common_education_group_year, label, user_language, 'common')
        # if is common and a label in COMMON_PARAGRAPH, must be editable in common offer
        elif label in COMMON_PARAGRAPH:
            translations = self.get_content_translations_for_label(
                self.object, label, user_language, 'specific')
        return translations

    def get_content_translations_for_label(self, education_group_year, label, user_language, type):
        # fetch the translation for the current user
        translated_label = TranslatedTextLabel.objects.filter(text_label__entity=entity_name.OFFER_YEAR,
                                                              text_label__label=label,
                                                              language=user_language).first()
        # fetch the translations for the both languages
        french, english = 'fr-be', 'en'
        fr_translated_text = TranslatedText.objects.filter(entity=entity_name.OFFER_YEAR,
                                                           text_label__label=label,
                                                           reference=str(education_group_year.id),
                                                           language=french).first()
        en_translated_text = TranslatedText.objects.filter(entity=entity_name.OFFER_YEAR,
                                                           text_label__label=label,
                                                           reference=str(education_group_year.id),
                                                           language=english).first()
        return {
            'label': label,
            'type': type,
            'translation': translated_label.label if translated_label else
            (_('This label %s does not exist') % label),
            french: fr_translated_text.text if fr_translated_text else None,
            english: en_translated_text.text if en_translated_text else None,
        }

    def get_appropriate_sections(self):
        sections = []
        try:
            sections = general_information.get_relevant_sections(self.object)
        except RelevantSectionException as e:
            display_error_messages(self.request, str(e))
        return sections

    def get_contacts_section(self):
        introduction = self.get_content_translations_for_label(
            self.object,
            CONTACT_INTRO_KEY,
            self.user_language_code,
            'specific'
        )
        return {
            'contact_intro': introduction,
            'contacts_grouped': self._get_publication_contacts_group_by_type()
        }

    def _get_publication_contacts_group_by_type(self):
        contacts_by_type = {}
        for publication_contact in self.object.educationgrouppublicationcontact_set.all():
            contacts_by_type.setdefault(publication_contact.type, []).append(publication_contact)
        return contacts_by_type


@login_required
def publish(request, education_group_year_id, root_id):
    education_group_year = get_object_or_404(EducationGroupYear, pk=education_group_year_id)

    try:
        portal_url = general_information.publish(education_group_year)
        message = _("The program are published. Click on the link to display it : ") + \
            "<a href=" + portal_url + ">" + education_group_year.acronym + "</a>"
        display_success_messages(request, message, extra_tags='safe')
    except PublishException as e:
        display_error_messages(request, str(e))

    return redirect(reverse('education_group_general_informations',
                            kwargs={'root_id': root_id, 'education_group_year_id': education_group_year_id}))


class EducationGroupAdministrativeData(EducationGroupGenericDetailView):
    template_name = "education_group/tab_administrative_data.html"
    limited_by_category = (education_group_categories.TRAINING,)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'course_enrollment': get_dates(academic_calendar_type.COURSE_ENROLLMENT, self.object),
            'mandataries': mdl.mandatary.find_by_education_group_year(self.object),
            'pgm_mgrs': mdl.program_manager.find_by_education_group(self.object.education_group),
            'exam_enrollments': get_sessions_dates(academic_calendar_type.EXAM_ENROLLMENTS, self.object),
            'scores_exam_submission': get_sessions_dates(academic_calendar_type.SCORES_EXAM_SUBMISSION, self.object),
            'dissertation_submission': get_sessions_dates(academic_calendar_type.DISSERTATION_SUBMISSION, self.object),
            'deliberation': get_sessions_dates(academic_calendar_type.DELIBERATION, self.object),
            'scores_exam_diffusion': get_sessions_dates(academic_calendar_type.SCORES_EXAM_DIFFUSION, self.object),
            "can_edit_administrative_data": can_user_edit_administrative_data(self.request.user, self.object)
        })

        return context


def get_sessions_dates(an_academic_calendar_type, an_education_group_year):
    date_dict = {}

    for session_number in range(NUMBER_SESSIONS):
        session = mdl.session_exam_calendar.get_by_session_reference_and_academic_year(
            session_number + 1,
            an_academic_calendar_type,
            an_education_group_year.academic_year)
        if session:
            dates = mdl.offer_year_calendar.get_by_education_group_year_and_academic_calendar(session.academic_calendar,
                                                                                              an_education_group_year)
            date_dict['session{}'.format(session_number + 1)] = dates

    return date_dict


def get_dates(an_academic_calendar_type, an_education_group_year):
    ac = mdl.academic_calendar.get_by_reference_and_academic_year(an_academic_calendar_type,
                                                                  an_education_group_year.academic_year)
    if ac:
        dates = mdl.offer_year_calendar.get_by_education_group_year_and_academic_calendar(ac, an_education_group_year)
        return {'dates': dates}
    else:
        return {}


class EducationGroupContent(EducationGroupGenericDetailView):
    template_name = "education_group/tab_content.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["group_element_years"] = self.object.groupelementyear_set.annotate(
                acronym=Case(
                        When(child_leaf__isnull=False, then=F("child_leaf__acronym")),
                        When(child_branch__isnull=False, then=F("child_branch__acronym")),
                     ),
                code=Case(
                    When(child_branch__isnull=False, then=F("child_branch__partial_acronym")),
                    default=None
                ),
                title=Case(
                        When(child_leaf__isnull=False, then=F("child_leaf__specific_title")),
                        When(child_branch__isnull=False, then=F("child_branch__title")),
                     ),
                child_id=Case(
                    When(child_leaf__isnull=False, then=F("child_leaf__id")),
                    When(child_branch__isnull=False, then=F("child_branch__id")),
                ),
            ).order_by('order')

        context['show_minor_major_option_table'] = self._show_minor_major_option_table()
        return context

    def _show_minor_major_option_table(self):
        return self.object.education_group_type.name in GroupType.minor_major_option_list_choice()


class EducationGroupUsing(EducationGroupGenericDetailView):
    template_name = "education_group/tab_utilization.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["group_element_years"] = self.object.child_branch.select_related("parent")
        return context


class EducationGroupYearAdmissionCondition(EducationGroupGenericDetailView):
    template_name = "education_group/tab_admission_conditions.html"
    permission_required = 'base.can_edit_educationgroup_pedagogy'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tab_lang = cache.get(get_tab_lang_keys(self.request.user)) or settings.LANGUAGE_CODE_FR

        acronym = self.object.acronym.lower()
        is_common = acronym.startswith('common-')
        is_specific = not is_common
        is_minor = self.object.is_minor
        is_deepening = self.object.is_deepening

        is_master = acronym.endswith(('2m', '2m1'))
        is_agregation = acronym.endswith('2a')
        is_mc = acronym.endswith('2mc')

        class AdmissionConditionForm(forms.Form):
            text_field = forms.CharField(widget=CKEditorWidget(config_name='minimal'))

        admission_condition_form = AdmissionConditionForm()
        admission_condition, created = AdmissionCondition.objects.get_or_create(education_group_year=self.object)

        record = {}
        for section in SECTIONS_WITH_TEXT:
            record[section] = AdmissionConditionLine.objects.filter(
                admission_condition=admission_condition,
                section=section
            ).annotate_text(tab_lang)

        context.update({
            'admission_condition_form': admission_condition_form,
            'can_edit_information': is_eligible_to_edit_admission_condition(context['person'], context['object']),
            'info': {
                'is_specific': is_specific,
                'is_common': is_common,
                'is_bachelor': is_common and self.object.education_group_type.name == TrainingType.BACHELOR.name,
                'is_master': is_master,
                'show_components_for_agreg': is_common and is_agregation,
                'show_components_for_agreg_and_mc': is_common and is_agregation or is_mc,
                'show_free_text': (is_specific and (is_master or is_agregation or is_mc)) or is_minor or is_deepening,
            },
            'admission_condition': admission_condition,
            'record': record,
            'language': {
                'list': ["fr-be", "en"],
                'tab_lang': tab_lang
            }
        })

        return context
