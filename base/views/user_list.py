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
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Prefetch
from django.db.models import Subquery, OuterRef
from django.http import Http404
from django.views.generic import ListView

from base.models.academic_year import current_academic_year
from base.models.education_group_year import EducationGroupYear
from base.models.entity_manager import EntityManager
from base.models.entity_version import EntityVersion
from base.models.person import Person
from base.models.person_entity import PersonEntity
from base.models.program_manager import ProgramManager


class UserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Person
    paginate_by = "20"
    ordering = 'last_name', 'first_name', 'global_id'
    permission_required = 'base.can_read_persons_roles'
    raise_exception = True

    def get_queryset(self):
        prefetch_pgm_mgr = Prefetch(
            "programmanager_set",
            queryset=ProgramManager.objects.all().annotate(
                most_recent_acronym=Subquery(
                    EducationGroupYear.objects.filter(
                        education_group=OuterRef('education_group__pk'),
                        academic_year=current_academic_year()
                    ).values('acronym')
                )
            ).order_by('most_recent_acronym')
        )

        most_recent_acronym_subquery = Subquery(
            EntityVersion.objects.filter(
                entity=OuterRef('entity__pk')
            ).order_by('-start_date').values('acronym')[:1]
        )

        prefetch_managed_entity = Prefetch(
            "entitymanager_set",
            queryset=EntityManager.objects.annotate(
                entity_recent_acronym=most_recent_acronym_subquery
            ).order_by('entity_recent_acronym')
        )

        prefetch_personentity = Prefetch(
            "personentity_set",
            queryset=PersonEntity.objects.annotate(
                entity_recent_acronym=most_recent_acronym_subquery
            ).order_by('entity_recent_acronym')
        )

        qs = super().get_queryset().select_related(
                'user'
            ).prefetch_related(
                'user__groups'
            ).prefetch_related(
                prefetch_pgm_mgr,
                prefetch_managed_entity,
                prefetch_personentity
            ).filter(
                user__is_active=True,
                student__isnull=True,
                tutor__isnull=True,
            )

        if 'partnership' in settings.INSTALLED_APPS:
            from partnership.models import PartnershipEntityManager
            qs = qs.prefetch_related(
                Prefetch(
                    'partnershipentitymanager_set',
                    queryset=PartnershipEntityManager.objects.annotate(
                        entity_recent_acronym=most_recent_acronym_subquery
                    ).order_by('entity_recent_acronym')
                )
            )

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
