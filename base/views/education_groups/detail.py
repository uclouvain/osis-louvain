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
import itertools
import json
from collections import namedtuple, defaultdict

from ckeditor.widgets import CKEditorWidget
from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import F, Case, When, Prefetch
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView
from reversion.models import Version

from base import models as mdl
from base.business.education_group import assert_category_of_education_group_year, can_user_edit_administrative_data
from base.business.education_groups import perms, general_information
from base.business.education_groups.general_information import PublishException
from base.business.education_groups.general_information_sections import SECTION_LIST, \
    MIN_YEAR_TO_DISPLAY_GENERAL_INFO_AND_ADMISSION_CONDITION, SECTIONS_PER_OFFER_TYPE
from base.business.education_groups.group_element_year_tree import EducationGroupHierarchy
from base.models.academic_calendar import AcademicCalendar
from base.models.academic_year import current_academic_year
from base.models.admission_condition import AdmissionCondition, AdmissionConditionLine
from base.models.education_group_achievement import EducationGroupAchievement
from base.models.education_group_certificate_aim import EducationGroupCertificateAim
from base.models.education_group_detailed_achievement import EducationGroupDetailedAchievement
from base.models.education_group_organization import EducationGroupOrganization
from base.models.education_group_year import EducationGroupYear
from base.models.education_group_year_domain import EducationGroupYearDomain
from base.models.enums import education_group_categories, academic_calendar_type
from base.models.enums.education_group_categories import TRAINING
from base.models.enums.education_group_types import TrainingType, MiniTrainingType
from base.models.mandatary import Mandatary
from base.models.offer_year_calendar import OfferYearCalendar
from base.models.person import Person
from base.models.program_manager import ProgramManager
from base.utils.cache import cache
from base.utils.cache_keys import get_tab_lang_keys
from base.views.common import display_error_messages, display_success_messages
from cms.enums import entity_name
from cms.models.translated_text import TranslatedText
from cms.models.translated_text_label import TranslatedTextLabel
from webservices.business import CONTACT_INTRO_KEY

SECTIONS_WITH_TEXT = (
    'ucl_bachelors',
    'others_bachelors_french',
    'bachelors_dutch',
    'foreign_bachelors',
    'graduates',
    'masters'
)

NUMBER_SESSIONS = 3


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
            context['tree'] = json.dumps(EducationGroupHierarchy(self.root).to_json())

        context['group_to_parent'] = self.request.GET.get("group_to_parent") or '0'
        context['can_change_education_group'] = perms.is_eligible_to_change_education_group(
            person=self.get_person(),
            education_group=context['object'],
        )
        context['can_change_coorganization'] = perms.is_eligible_to_change_coorganization(
            person=self.get_person(),
            education_group=context['object'],
        )
        context['enums'] = mdl.enums.education_group_categories

        context["show_identification"] = self.show_identification()
        context["show_diploma"] = self.show_diploma()
        context["show_general_information"] = self.show_general_information()
        context["show_skills_and_achievements"] = self.show_skills_and_achievements()
        context["show_administrative"] = self.show_administrative()
        context["show_content"] = self.show_content()
        context["show_utilization"] = self.show_utilization()
        context["show_admission_conditions"] = self.show_admission_conditions()
        return context

    def get(self, request, *args, **kwargs):
        if self.limited_by_category:
            assert_category_of_education_group_year(self.get_object(), self.limited_by_category)
        return super().get(request, *args, **kwargs)

    def show_identification(self):
        return True

    def show_diploma(self):
        return self.object.education_group_type.category == TRAINING and not self.object.is_common

    def show_general_information(self):
        return not self.object.acronym.startswith('common-') and \
               self.is_general_info_and_condition_admission_in_display_range() and \
               self.object.education_group_type.name in SECTIONS_PER_OFFER_TYPE.keys()

    def show_administrative(self):
        return self.object.education_group_type.category == "TRAINING" and \
               self.object.education_group_type.name not in [TrainingType.PGRM_MASTER_120.name,
                                                             TrainingType.PGRM_MASTER_180_240.name] and \
               not self.object.is_common

    def show_content(self):
        return not self.object.is_common

    def show_utilization(self):
        return not self.object.is_common

    def show_admission_conditions(self):
        # @TODO: Need to refactor after business clarification
        return not self.object.is_main_common and \
               self.object.education_group_type.name in itertools.chain(TrainingType.with_admission_condition(),
                                                                        MiniTrainingType.with_admission_condition()) \
               and self.is_general_info_and_condition_admission_in_display_range()

    def show_skills_and_achievements(self):
        return not self.object.is_common and \
               self.object.education_group_type.name in itertools.chain(TrainingType.with_skills_achievements(),
                                                                        MiniTrainingType.with_admission_condition()) \
               and self.is_general_info_and_condition_admission_in_display_range()

    def is_general_info_and_condition_admission_in_display_range(self):
        return MIN_YEAR_TO_DISPLAY_GENERAL_INFO_AND_ADMISSION_CONDITION <= self.object.academic_year.year < \
               current_academic_year().year + 2


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
        context["versions"] = self.get_related_versions()
        context["show_coorganization"] = self.show_coorganization()
        return context

    def get_template_names(self):
        return self.templates.get(self.object.education_group_type.category)

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

    def show_coorganization(self):
        return self.object.education_group_type.category == "TRAINING" and \
               self.object.education_group_type.name not in [TrainingType.PGRM_MASTER_120.name,
                                                             TrainingType.PGRM_MASTER_180_240.name]


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
        common_education_group_year = None
        if not is_common_education_group_year:
            common_education_group_year = EducationGroupYear.objects.get_common(
                academic_year=self.object.academic_year,
            )
        sections_to_display = SECTIONS_PER_OFFER_TYPE.get(
            'common' if is_common_education_group_year
            else self.object.education_group_type.name,
            {'specific': [], 'common': []}
        )
        texts = self.get_translated_texts(sections_to_display, common_education_group_year, self.user_language_code)

        show_contacts = CONTACT_INTRO_KEY in sections_to_display['specific']
        context.update({
            'is_common_education_group_year': is_common_education_group_year,
            'sections_with_translated_labels': self.get_sections_with_translated_labels(
                sections_to_display,
                texts
            ),
            'contacts': self.get_contacts_section(sections_to_display, texts),
            'show_contacts': show_contacts,
            'can_edit_information': perms.is_eligible_to_edit_general_information(context['person'], context['object'])
        })
        return context

    @cached_property
    def user_language_code(self):
        return mdl.person.get_user_interface_language(self.request.user)

    def get_sections_with_translated_labels(self, sections_to_display, texts):
        # Load the labels
        Section = namedtuple('Section', 'title labels')
        sections_with_translated_labels = []
        for section in SECTION_LIST:
            translated_labels = []
            for label in section.labels:
                translated_labels += self.get_texts_for_label(label, sections_to_display, texts)
            if translated_labels:
                sections_with_translated_labels.append(Section(section.title, translated_labels))
        return sections_with_translated_labels

    def get_texts_for_label(self, label, sections_to_display, texts):
        translated_labels = []
        translated_label = next((text for text in texts['labels'] if text.text_label.label == label), None)
        if label in sections_to_display['common']:
            common_text = self.get_text_structure_for_display(label, texts['common'], translated_label)
            common_text.update({'type': 'common'})
            translated_labels.append(common_text)
        if label in sections_to_display['specific']:
            text = self.get_text_structure_for_display(label, texts['specific'], translated_label)
            text.update({'type': 'specific'})
            translated_labels.append(text)
        return translated_labels

    def get_text_structure_for_display(self, label, texts, translated_label):
        french, english = 'fr-be', 'en'
        text_fr = next(
            (
                text.text for text in texts
                if text.text_label.label == label and text.language == french
            ),
            None
        )
        text_en = next(
            (
                text.text for text in texts
                if text.text_label.label == label and text.language == english
            ),
            None
        )

        return {
            'label': label,
            'translation': translated_label if translated_label else
            (_('This label %s does not exist') % label),
            french: text_fr,
            english: text_en,
        }

    def get_translated_texts(self, sections_to_display, common_edy, user_language):
        specific_texts = TranslatedText.objects.filter(
            text_label__label__in=sections_to_display['specific'],
            entity=entity_name.OFFER_YEAR,
            reference=str(self.object.pk)
        ).select_related("text_label")

        common_texts = TranslatedText.objects.filter(
            text_label__label__in=sections_to_display['common'],
            entity=entity_name.OFFER_YEAR,
            reference=str(common_edy.pk)
        ).select_related("text_label") if common_edy else None

        labels = TranslatedTextLabel.objects.filter(
            text_label__label__in=sections_to_display['common']+sections_to_display['specific'],
            text_label__entity=entity_name.OFFER_YEAR,
            language=user_language
        ).select_related("text_label")

        return {'common': common_texts, 'specific': specific_texts, 'labels': labels}

    def get_contacts_section(self, sections_to_display, texts):
        introduction = self.get_texts_for_label(CONTACT_INTRO_KEY, sections_to_display, texts)
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
@require_http_methods(['POST'])
def publish(request, education_group_year_id, root_id):
    education_group_year = get_object_or_404(EducationGroupYear, pk=education_group_year_id)

    try:
        general_information.publish(education_group_year)
        message = _("The program %(acronym)s will be published soon") % {'acronym': education_group_year.acronym}
        display_success_messages(request, message, extra_tags='safe')
    except PublishException as e:
        display_error_messages(request, str(e))

    default_redirect_view = reverse('education_group_general_informations',
                                    kwargs={'root_id': root_id, 'education_group_year_id': education_group_year_id})
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', default_redirect_view))


class EducationGroupAdministrativeData(EducationGroupGenericDetailView):
    template_name = "education_group/tab_administrative_data.html"
    limited_by_category = (education_group_categories.TRAINING,)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        pgm_mgrs = ProgramManager.objects.filter(
            education_group=self.object.education_group
        ).order_by("person__last_name", "person__first_name")

        mandataries = Mandatary.objects.filter(
            mandate__education_group=self.object.education_group,
            start_date__lte=self.object.academic_year.start_date,
            end_date__gte=self.object.academic_year.end_date
        ).order_by(
            'mandate__function',
            'person__last_name',
            'person__first_name'
        ).select_related("person", "mandate")

        course_enrollment_dates = OfferYearCalendar.objects.filter(
            education_group_year=self.object,
            academic_calendar__reference=academic_calendar_type.COURSE_ENROLLMENT,
            academic_calendar__academic_year=self.object.academic_year
        ).first()

        context.update({
            'course_enrollment_dates': course_enrollment_dates,
            'mandataries': mandataries,
            'pgm_mgrs': pgm_mgrs,
            "can_edit_administrative_data": can_user_edit_administrative_data(self.request.user, self.object)
        })
        context.update(get_sessions_dates(self.object))

        return context


def get_sessions_dates(education_group_year):
    calendar_types = (academic_calendar_type.EXAM_ENROLLMENTS, academic_calendar_type.SCORES_EXAM_SUBMISSION,
                      academic_calendar_type.DISSERTATION_SUBMISSION, academic_calendar_type.DELIBERATION,
                      academic_calendar_type.SCORES_EXAM_DIFFUSION)
    calendars = AcademicCalendar.objects.filter(
        reference__in=calendar_types,
        academic_year=education_group_year.academic_year
    ).select_related(
        "sessionexamcalendar"
    ).prefetch_related(
        Prefetch(
            "offeryearcalendar_set",
            queryset=OfferYearCalendar.objects.filter(
                education_group_year=education_group_year
            ),
            to_attr="offer_calendars"
        )
    )

    sessions_dates_by_calendar_type = defaultdict(dict)

    for calendar in calendars:
        session = calendar.sessionexamcalendar
        offer_year_calendars = calendar.offer_calendars
        if offer_year_calendars:
            sessions_dates_by_calendar_type[calendar.reference.lower()]['session{}'.format(session.number_session)] = \
                offer_year_calendars[0]

    return sessions_dates_by_calendar_type


def get_dates(an_academic_calendar_type, an_education_group_year):
    try:
        dates = OfferYearCalendar.objects.get(
            education_group_year=an_education_group_year,
            academic_calendar__reference=an_academic_calendar_type,
            academic_calendar__academic_year=an_education_group_year.academic_year
        )
    except OfferYearCalendar.DoesNotExist:
        dates = None

    return {"dates": dates} if dates else {}


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
            child_id=Case(
                When(child_leaf__isnull=False, then=F("child_leaf__id")),
                When(child_branch__isnull=False, then=F("child_branch__id")),
            ),
        ).order_by('order')

        context['show_minor_major_option_table'] = self.object.is_minor_major_option_list_choice
        return context


class EducationGroupUsing(EducationGroupGenericDetailView):
    template_name = "education_group/tab_utilization.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["group_element_years"] = self.object.child_branch.select_related("parent")
        return context


class EducationGroupYearAdmissionCondition(EducationGroupGenericDetailView):
    template_name = "education_group/tab_admission_conditions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tab_lang = cache.get(get_tab_lang_keys(self.request.user)) or settings.LANGUAGE_CODE_FR

        acronym = self.object.acronym.lower()
        is_common = acronym.startswith('common-')
        is_specific = not is_common
        is_bachelor = self.object.is_bachelor

        is_master = acronym.endswith(('2m', '2m1'))
        is_aggregation = acronym.endswith('2a')
        is_mc = acronym.endswith('2mc')
        common_conditions = get_appropriate_common_admission_condition(self.object)

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
            'can_edit_information': perms.is_eligible_to_edit_admission_condition(context['person'], context['object']),
            'info': {
                'is_specific': is_specific,
                'is_common': is_common,
                'is_bachelor': is_bachelor,
                'is_master': is_master,
                'show_components_for_agreg': is_aggregation,
                'show_components_for_agreg_and_mc': is_aggregation or is_mc,
                'show_free_text': self._show_free_text()
            },
            'admission_condition': admission_condition,
            'common_conditions': common_conditions,
            'record': record,
            'language': {
                'list': ["fr-be", "en"],
                'tab_lang': tab_lang
            }
        })

        return context

    def _show_free_text(self):
        return not self.object.is_common and self.object.education_group_type.name in itertools.chain(
            TrainingType.with_admission_condition(),
            MiniTrainingType.with_admission_condition()
        )


def get_appropriate_common_admission_condition(edy):
    if not edy.is_common and any([
        edy.is_bachelor,
        edy.is_master60,
        edy.is_master120,
        edy.is_aggregation,
        edy.is_specialized_master,
        edy.is_master180
    ]):
        common_egy = EducationGroupYear.objects.look_for_common(
            education_group_type__name=TrainingType.PGRM_MASTER_120.name if edy.is_master60 or edy.is_master180
            else edy.education_group_type.name,
            academic_year=edy.academic_year
        ).get()
        common_admission_condition, created = AdmissionCondition.objects.get_or_create(education_group_year=common_egy)
        return common_admission_condition
    return None
