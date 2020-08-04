from enum import IntEnum

from django.urls import reverse
from django.utils.functional import cached_property
from django.views.generic import RedirectView

from base.business.education_groups.general_information_sections import SECTIONS_PER_OFFER_TYPE
from education_group.ddd.domain.training import TrainingIdentity
from program_management.ddd.business_types import *
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.domain.service.identity_search import NodeIdentitySearch
from program_management.ddd.repositories.node import NodeRepository

SUFFIX_IDENTIFICATION = 'identification'
SUFFIX_DIPLOMAS_CERTIFICATES = 'diplomas'
SUFFIX_ADMINISTRATIVE_DATA = 'administrative_data'
SUFFIX_CONTENT = 'content'
SUFFIX_UTILIZATION = 'utilization'
SUFFIX_GENERAL_INFO = 'general_information'
SUFFIX_SKILLS_ACHIEVEMENTS = 'skills_achievements'
SUFFIX_ADMISSION_CONDITION = 'admission_condition'


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

    def _get_current_path(self) -> str:
        return self.request.GET.get('path')

    def get_redirect_url(self, *args, **kwargs):
        url = get_tab_urls(
            path=self._get_current_path(),
            tab=self._get_current_tab(),
            node=self.node,
            anchor=self.request.GET.get('anchor')
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
        Tab.IDENTIFICATION: '{prefix}_{suffix}'.format(prefix=prefix, suffix=SUFFIX_IDENTIFICATION),
        Tab.DIPLOMAS_CERTIFICATES: '{prefix}_{suffix}'.format(prefix=prefix, suffix=SUFFIX_DIPLOMAS_CERTIFICATES),
        Tab.ADMINISTRATIVE_DATA: '{prefix}_{suffix}'.format(prefix=prefix, suffix=SUFFIX_ADMINISTRATIVE_DATA),
        Tab.CONTENT: '{prefix}_{suffix}'.format(prefix=prefix, suffix=SUFFIX_CONTENT),
        Tab.UTILIZATION: '{prefix}_{suffix}'.format(prefix=prefix, suffix=SUFFIX_UTILIZATION),
        Tab.GENERAL_INFO: '{prefix}_{suffix}'.format(prefix=prefix, suffix=SUFFIX_GENERAL_INFO),
        Tab.SKILLS_ACHIEVEMENTS: '{prefix}_{suffix}'.format(prefix=prefix, suffix=SUFFIX_SKILLS_ACHIEVEMENTS),
        Tab.ADMISSION_CONDITION: '{prefix}_{suffix}'.format(prefix=prefix, suffix=SUFFIX_ADMISSION_CONDITION),
    }[tab]


def get_tab_urls(tab: Tab, node: 'Node', path: 'Path' = None, anchor: 'str' = None) -> str:
    path = path or ""
    url = reverse(_get_view_name_from_tab(node, tab), args=[node.year, node.code])

    anchor_concat = "?"
    if path:
        url += "?path={}&tab={}#achievement_".format(path, tab)
        anchor_concat = "&"

    if anchor == 'True':
        url = "{}{}anchor=True".format(url, anchor_concat)

    return url


def get_tab_from_path_info(node: 'Node', path_info: str):
    if path_info:
        tabs = get_group_available_tabs(node)

        if node.is_training():
            tabs = get_training_available_tabs()

        if node.is_mini_training():
            tabs = get_mini_training_available_tabs()

        return next((tab for key, tab in tabs.items() if key in path_info), Tab.IDENTIFICATION)
    return Tab.IDENTIFICATION


def get_group_available_tabs(node: 'Node'):
    tabs = {
        SUFFIX_IDENTIFICATION: Tab.IDENTIFICATION,
        SUFFIX_CONTENT: Tab.CONTENT,
        SUFFIX_UTILIZATION: Tab.UTILIZATION,
    }
    if node.node_type.name in SECTIONS_PER_OFFER_TYPE.keys():
        tabs.update({
            SUFFIX_GENERAL_INFO: Tab.GENERAL_INFO,
        })
    return tabs


def get_training_available_tabs():
    return {
        SUFFIX_IDENTIFICATION: Tab.IDENTIFICATION,
        SUFFIX_DIPLOMAS_CERTIFICATES: Tab.DIPLOMAS_CERTIFICATES,
        SUFFIX_ADMINISTRATIVE_DATA: Tab.ADMINISTRATIVE_DATA,
        SUFFIX_CONTENT: Tab.CONTENT,
        SUFFIX_UTILIZATION: Tab.UTILIZATION,
        SUFFIX_GENERAL_INFO: Tab.GENERAL_INFO,
        SUFFIX_SKILLS_ACHIEVEMENTS: Tab.SKILLS_ACHIEVEMENTS,
        SUFFIX_ADMISSION_CONDITION: Tab.ADMISSION_CONDITION
    }


def get_mini_training_available_tabs():
    return {
        SUFFIX_IDENTIFICATION: Tab.IDENTIFICATION,
        SUFFIX_CONTENT: Tab.CONTENT,
        SUFFIX_UTILIZATION: Tab.UTILIZATION,
        SUFFIX_GENERAL_INFO: Tab.GENERAL_INFO,
        SUFFIX_SKILLS_ACHIEVEMENTS: Tab.SKILLS_ACHIEVEMENTS,
        SUFFIX_ADMISSION_CONDITION: Tab.ADMISSION_CONDITION
    }
