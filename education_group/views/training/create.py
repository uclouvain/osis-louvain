from typing import List, Dict, Union

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View

from base.models.academic_year import starting_academic_year, AcademicYear
from base.models.campus import Campus
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import GroupType, TrainingType
from base.utils.cache import RequestCache
from base.utils.urls import reverse_with_get
from base.views.common import display_success_messages, display_error_messages
from education_group.ddd import command
from program_management.ddd import command as program_management_command
from education_group.ddd.domain.exception import GroupCodeAlreadyExistException, ContentConstraintTypeMissing, \
    ContentConstraintMinimumMaximumMissing, ContentConstraintMaximumShouldBeGreaterOrEqualsThanMinimum, \
    AcronymAlreadyExist, StartYearGreaterThanEndYear, MaximumCertificateAimType2Reached
from education_group.ddd.domain.training import TrainingIdentity
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.domain.service.element_id_search import ElementIdSearch
from program_management.ddd.domain.service.identity_search import NodeIdentitySearch
from program_management.ddd.service.write import create_training_with_program_tree, create_and_attach_training_service
from education_group.forms.training import CreateTrainingForm
from education_group.templatetags.academic_year_display import display_as_academic_year
from education_group.views.proxy.read import Tab
from osis_role.contrib.views import PermissionRequiredMixin
from program_management.ddd.domain.program_tree import Path
from program_management.ddd.service.write.create_training_with_program_tree import \
    create_and_report_training_with_program_tree


class TrainingCreateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    # PermissionRequiredMixin
    permission_required = 'base.add_training'
    raise_exception = True

    template_name = "education_group_app/training/upsert/create.html"

    @cached_property
    def parent_node_identity(self) -> Union[None, 'NodeIdentity']:
        if self.get_attach_path():
            return NodeIdentitySearch().get_from_element_id(int(self.get_attach_path().split('|')[-1]))

    def get_context(self, training_form: CreateTrainingForm):
        training_type = self.kwargs['type']
        return {
            "training_form": training_form,
            "tabs": self.get_tabs(),
            "type_text": str(TrainingType.get_value(training_type)),
            "is_finality_types": training_type in TrainingType.finality_types(),
            "cancel_url": self.get_cancel_url(),
        }

    def get(self, request, *args, **kwargs):
        training_type = self.kwargs['type']
        training_form = CreateTrainingForm(
            user=self.request.user,
            training_type=training_type,
            initial=self._get_initial_form(),
            attach_path=self.get_attach_path(),
        )
        return render(request, self.template_name, self.get_context(training_form))

    def get_cancel_url(self) -> str:
        if self.get_attach_path():
            return reverse_with_get(
                'element_identification',
                kwargs={'code': self.parent_node_identity.code, 'year': self.parent_node_identity.year},
                get={'path': self.get_attach_path()}
            )
        return reverse('version_program')

    def _get_initial_form(self) -> Dict:
        default_campus = Campus.objects.filter(name='Louvain-la-Neuve').first()

        request_cache = RequestCache(self.request.user, reverse('version_program'))
        if self.get_attach_path():
            default_academic_year = AcademicYear.objects.get(
                year=self.parent_node_identity.year
            ).pk
        else:
            default_academic_year = request_cache.get_value_cached('academic_year') or starting_academic_year()
        return {
            'teaching_campus': default_campus,
            'academic_year': default_academic_year
        }

    def post(self, request, *args, **kwargs):
        training_form = CreateTrainingForm(
            data=request.POST,
            initial=self._get_initial_form(),
            user=self.request.user,
            training_type=self.kwargs['type'],
            attach_path=self.get_attach_path(),
        )
        if training_form.is_valid():
            create_training_data = _convert_training_form_to_data_for_service(training_form)
            training_ids = []
            try:
                training_ids = self._call_service(create_training_data)
            except GroupCodeAlreadyExistException as e:
                training_form.add_error('code', e.message)
            except AcronymAlreadyExist as e:
                training_form.add_error('acronym', e.message)
            except ContentConstraintTypeMissing as e:
                training_form.add_error('constraint_type', e.message)
            except (ContentConstraintMinimumMaximumMissing, ContentConstraintMaximumShouldBeGreaterOrEqualsThanMinimum)\
                    as e:
                training_form.add_error('min_constraint', e.message)
                training_form.add_error('max_constraint', '')
            except StartYearGreaterThanEndYear as e:
                training_form.add_error('end_year', e.message)
                training_form.add_error('academic_year', '')
            except MaximumCertificateAimType2Reached as e:
                training_form.add_error('certificate_aims', e.message)
                training_form.add_error('section', '')

            if not training_form.errors:
                self._display_success_messages(training_ids)
                return HttpResponseRedirect(self.get_success_url(training_ids[0]))

        if training_form.errors and not training_form.confirmed:
            self._display_default_error_message()

        return render(request, self.template_name, self.get_context(training_form))

    def _display_success_messages(self, training_ids: List['TrainingIdentity']):
        success_messages = [
            self.get_success_msg(training_id) for training_id in training_ids
        ]
        display_success_messages(self.request, success_messages, extra_tags='safe')

    def _display_default_error_message(self):
        msg = _("Error(s) in form: The modifications are not saved")
        display_error_messages(self.request, msg)

    def _call_service(self, create_training_data: dict) -> List['TrainingIdentity']:
        if self.get_attach_path():
            cmd = program_management_command.CreateAndAttachTrainingCommand(
                **create_training_data,
                path_to_paste=self.get_attach_path(),
            )
            training_ids = create_and_attach_training_service.create_and_attach_training(cmd)
        else:
            training_ids = create_and_report_training_with_program_tree(
                command.CreateTrainingCommand(**create_training_data)
            )
        return training_ids

    def get_success_url(self, training_id: TrainingIdentity):
        path = self.get_attach_path()
        if path:
            path += '|' + str(ElementIdSearch().get_from_training_identity(training_id))
            node_identity = NodeIdentitySearch().get_from_element_id(int(path.split('|')[0]))
            url = reverse_with_get(
                'element_identification',
                args=[node_identity.year, node_identity.code],
                get={"path": path}
            )
        else:
            url = reverse(
                'education_group_read_proxy',
                kwargs={'acronym': training_id.acronym, 'year': training_id.year}
            ) + '?tab={}'.format(Tab.IDENTIFICATION)
        return url

    def get_success_msg(self, training_id: TrainingIdentity):
        return _("Training <a href='%(link)s'> %(acronym)s (%(academic_year)s) </a> successfully created.") % {
            "link": self.get_success_url(training_id),
            "acronym": training_id.acronym,
            "academic_year": display_as_academic_year(training_id.year),
        }

    def get_tabs(self) -> List:
        return [
            {
                "text": _("Identification"),
                "active": True,
                "display": True,
                "include_html": "education_group_app/training/upsert/training_identification_form.html"
            },
            {
                "text": _("Diplomas /  Certificates"),
                "active": False,
                "display": True,
                "include_html": "education_group_app/training/upsert/blocks/panel_diplomas_certificates_form.html"
            },
        ]

    def get_attach_path(self) -> Union[Path, None]:
        return self.request.GET.get('path_to') or None

    def get_permission_object(self) -> Union[EducationGroupYear, None]:
        qs = EducationGroupYear.objects.select_related('academic_year', 'management_entity')
        path = self.get_attach_path()
        if path:
            # Take parent from path (latest element)
            # Ex:  path: 4456|565|5656
            parent_id = path.split("|")[-1]
            qs = qs.filter(
                educationgroupversion__root_group__element__id=parent_id,
            )
        else:
            qs = qs.filter(
                partial_acronym=self.request.POST.get('code'),
                academic_year__year=self.request.POST.get('year'),
            )
        try:
            return qs.get()
        except EducationGroupYear.DoesNotExist:
            return None


def _convert_training_form_to_data_for_service(training_form: CreateTrainingForm) -> Dict:
    return {
        'abbreviated_title': training_form.cleaned_data['acronym'],
        'status': training_form.cleaned_data['active'],
        'code': training_form.cleaned_data['code'],
        'year': training_form.cleaned_data['academic_year'].year,
        'type': training_form.training_type,
        'credits': training_form.cleaned_data['credits'],
        'schedule_type': training_form.cleaned_data['schedule_type'],
        'duration': training_form.cleaned_data['duration'],
        'start_year': training_form.cleaned_data['academic_year'].year,
        'title_fr': training_form.cleaned_data['title_fr'],
        'partial_title_fr': training_form.cleaned_data['partial_title_fr'],
        'title_en': training_form.cleaned_data['title_en'],
        'partial_title_en': training_form.cleaned_data['partial_title_en'],
        'keywords': training_form.cleaned_data['keywords'],
        'internship_presence': training_form.cleaned_data['internship_presence'],
        'is_enrollment_enabled': training_form.cleaned_data['is_enrollment_enabled'],
        'has_online_re_registration': training_form.cleaned_data['has_online_re_registration'],
        'has_partial_deliberation': training_form.cleaned_data['has_partial_deliberation'],
        'has_admission_exam': training_form.cleaned_data['has_admission_exam'],
        'has_dissertation': training_form.cleaned_data['has_dissertation'],
        'produce_university_certificate': training_form.cleaned_data['produce_university_certificate'],
        'decree_category': training_form.cleaned_data['decree_category'],
        'rate_code': training_form.cleaned_data['rate_code'],
        'main_language': training_form.cleaned_data['main_language'],
        'english_activities': training_form.cleaned_data['english_activities'],
        'other_language_activities': training_form.cleaned_data['other_language_activities'],
        'internal_comment': training_form.cleaned_data['internal_comment'],
        'main_domain_code': training_form.cleaned_data['main_domain'].code
        if training_form.cleaned_data['main_domain'] else None,
        'main_domain_decree': training_form.cleaned_data['main_domain'].decree.name
        if training_form.cleaned_data['main_domain'] else None,
        'secondary_domains': [
            (obj.decree.name, obj.code) for obj in training_form.cleaned_data['secondary_domains']
        ],
        'isced_domain_code': training_form.cleaned_data['isced_domain'].code
        if training_form.cleaned_data['isced_domain'] else None,
        'management_entity_acronym': training_form.cleaned_data['management_entity'],
        'administration_entity_acronym': training_form.cleaned_data['administration_entity'],
        'end_year': training_form.cleaned_data['end_year'].year
        if training_form.cleaned_data['end_year'] else None,
        'teaching_campus_name': training_form.cleaned_data['teaching_campus'].name,
        'teaching_campus_organization_name': training_form.cleaned_data['teaching_campus'].organization.name,
        'enrollment_campus_name': training_form.cleaned_data['enrollment_campus'].name,
        'enrollment_campus_organization_name': training_form.cleaned_data['enrollment_campus'].organization.name,
        'other_campus_activities': training_form.cleaned_data['other_campus_activities'],
        'can_be_funded': training_form.cleaned_data['can_be_funded'],
        'funding_orientation': training_form.cleaned_data['funding_direction'],
        'can_be_international_funded': training_form.cleaned_data['can_be_international_funded'],
        'international_funding_orientation': training_form.cleaned_data['international_funding_orientation'],
        'ares_code': training_form.cleaned_data['ares_code'],
        'ares_graca': training_form.cleaned_data['ares_graca'],
        'ares_authorization': training_form.cleaned_data['ares_authorization'],
        'code_inter_cfb': training_form.cleaned_data['code_inter_cfb'],
        'coefficient': training_form.cleaned_data['coefficient'],
        'academic_type': training_form.cleaned_data['academic_type'],
        'duration_unit': training_form.cleaned_data['duration_unit'],
        'leads_to_diploma': training_form.cleaned_data['leads_to_diploma'],
        'printing_title': training_form.cleaned_data['diploma_printing_title'],
        'professional_title': training_form.cleaned_data['professional_title'],
        'aims': [
            (aim.code, aim.section) for aim in (training_form.cleaned_data['certificate_aims'] or [])
        ],
        'constraint_type': training_form.cleaned_data['constraint_type'],
        'min_constraint': training_form.cleaned_data['min_constraint'],
        'max_constraint': training_form.cleaned_data['max_constraint'],
        'remark_fr': training_form.cleaned_data['remark_fr'],
        'remark_en': training_form.cleaned_data['remark_english'],
    }
