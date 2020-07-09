from enum import IntEnum

from django.urls import reverse
from django.utils.functional import cached_property
from django.views.generic import RedirectView

from program_management.ddd.business_types import *
from education_group.ddd.domain.training import TrainingIdentity
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.domain.service.identity_search import NodeIdentitySearch
from program_management.ddd.repositories.node import NodeRepository


class Tab(IntEnum):
    IDENTIFICATION = 0
    DIPLOMAS_CERTIFICATES = 1
    ADMINISTRATIVE_DATA = 2
    CONTENT = 3
    UTILIZATION = 4
    GENERAL_INFO = 5
    SKILLS_ACHIEVEMENTS = 6
    ADMISSION_CONDITION = 7


class ReadEducationGroupRedirectView(RedirectView):
    """Proxy used only for training and minitraining"""
    permanent = False
    query_string = False

    @cached_property
    def training_identity(self) -> TrainingIdentity:
        return TrainingIdentity(acronym=self.kwargs['acronym'], year=self.kwargs['year'])

    @cached_property
    def node_identity(self) -> NodeIdentity:
        return NodeIdentitySearch().get_from_training_identity(self.training_identity)

    @cached_property
    def node(self) -> 'Node':
        return NodeRepository.get(self.node_identity)

    def _get_current_tab(self) -> Tab:
        try:
            return Tab(int(self.request.GET.get('tab')))
        except ValueError:
            return Tab.IDENTIFICATION

    def get_redirect_url(self, *args, **kwargs):
        url = get_tab_urls(
            tab=self._get_current_tab(),
            node=self.node,
        )
        self.url = url
        return super().get_redirect_url(*args, **kwargs)


def _get_view_name_from_tab(node: 'Node', tab: Tab):
    prefix = None
    if node.is_training():
        prefix = 'training'
    elif node.is_mini_training():
        prefix = 'mini_training'
    return {
        Tab.IDENTIFICATION: '{prefix}_identification'.format(prefix=prefix),
        Tab.DIPLOMAS_CERTIFICATES: '{prefix}_diplomas'.format(prefix=prefix),
        Tab.ADMINISTRATIVE_DATA: '{prefix}_administrative_data'.format(prefix=prefix),
        Tab.CONTENT: '{prefix}_content'.format(prefix=prefix),
        Tab.UTILIZATION: '{prefix}_utilization'.format(prefix=prefix),
        Tab.GENERAL_INFO: '{prefix}_general_information'.format(prefix=prefix),
        Tab.SKILLS_ACHIEVEMENTS: '{prefix}_skills_achievements'.format(prefix=prefix),
        Tab.ADMISSION_CONDITION: '{prefix}_admission_condition'.format(prefix=prefix),
    }[tab]


def get_tab_urls(tab: Tab, node: 'Node', path: 'Path' = None) -> str:
    path = path or ""
    url = reverse(_get_view_name_from_tab(node, tab), args=[node.year, node.code])
    if path:
        url += "?path={}".format(path)
    return url
