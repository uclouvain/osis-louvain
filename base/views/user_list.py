from django.http import Http404
from django.views.generic import ListView

from base.models.person import Person
from base.models.student import Student
from base.views.mixins import AjaxTemplateMixin


class UserListView(AjaxTemplateMixin, ListView):
    model = Person
    paginate_by = "200"
    ordering = 'global_id',
    # template_name = ''

    def get_queryset(self):
        qs = super().get_queryset().select_related('user')\
                    .prefetch_related('entitymanager_set',
                                      'personentity_set',
                                      'partnershipentitymanager_set',
                                      'programmanager_set')\
                    .exclude(pk__in=Student.objects.all())
        # qs = super().get_queryset().select_related('user')\
        #     .prefetch_related('entitymanager_set',
        #                       'personentity_set',
        #                       'partnershipentitymanager_set',
        #                       'programmanager_set')\
        #     .filter(user__username='admin')
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
