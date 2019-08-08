from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.views.generic import ListView

from base.models.person import Person
from base.models.student import Student


class UserListView(LoginRequiredMixin, ListView):
    model = Person
    paginate_by = "20"
    ordering = 'last_name', 'first_name', 'global_id'
    # template_name = ''

    def get_queryset(self):
        qs = super().get_queryset().select_related('user')\
                    .prefetch_related('managed_entities',
                                      'personentity_set',
                                      'partnershipentitymanager_set',
                                      'programmanager_set',
                                      'user__groups')\
                    .filter(user__is_active=True)\
                    .exclude(user__groups__name='tutors')\
                    .exclude(pk__in=Student.objects.all().values_list('person_id', flat=True))
        return qs

    def paginate_queryset(self, queryset, page_size):
        """ The cache can store a wrong page number,
        In that case, we return to the first page.
        """
        try:
            return super().paginate_queryset(queryset, page_size)
        except Http404:
            self.kwargs['page'] = 1

        return super().paginate_queryset(queryset, page_size)
