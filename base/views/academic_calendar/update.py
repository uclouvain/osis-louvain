import attr
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.utils.functional import cached_property
from django.views.generic import FormView
from django.utils.translation import gettext_lazy as _

from base.business.event_perms import AcademicEventRepository
from base.forms.academic_calendar.update import AcademicCalendarUpdateForm
from base.views.mixins import AjaxTemplateMixin
from osis_role.contrib.views import PermissionRequiredMixin


class AcademicCalendarUpdate(SuccessMessageMixin, PermissionRequiredMixin, AjaxTemplateMixin, FormView):
    template_name = "academic_calendar/update_inner.html"
    permission_required = 'base.can_access_academic_calendar'
    raise_exception = True
    form_class = AcademicCalendarUpdateForm

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            'academic_event': self.academic_event
        }

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            'initial': {
                'start_date': self.academic_event.start_date,
                'end_date':  self.academic_event.end_date,
            }
        }

    def form_valid(self, form):
        academic_event = attr.evolve(
            self.academic_event,
            start_date=form.cleaned_data['start_date'],
            end_date=form.cleaned_data['end_date']
        )
        AcademicEventRepository().update(academic_event)
        return super().form_valid(form)

    @cached_property
    def academic_event(self):
        return AcademicEventRepository().get(self.kwargs['academic_calendar_id'])

    def get_success_message(self, cleaned_data):
        return _("%(title)s has been updated") % {"title": self.academic_event.title}

    def get_success_url(self):
        return reverse('academic_calendars')
