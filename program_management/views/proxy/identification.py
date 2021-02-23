from distutils.util import strtobool
from typing import List
from urllib.parse import parse_qs

from django.urls import reverse
from django.views.generic import RedirectView

from education_group.views.proxy.read import SUFFIX_IDENTIFICATION, get_group_available_tabs, \
    get_mini_training_available_tabs, get_training_available_tabs
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.domain.service.identity_search import ProgramTreeVersionIdentitySearch
from program_management.ddd.repositories.node import NodeRepository
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository


class IdentificationRedirectView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        year = self.kwargs['year']
        code = self.kwargs['code']
        root_node = NodeRepository().get(NodeIdentity(code=code, year=year))
        keep_tab = bool(strtobool(parse_qs(self.request.META.get('QUERY_STRING')).get('keep-tab', 'yes')[0]))
        if root_node.is_training():
            version = ProgramTreeVersionRepository.get(ProgramTreeVersionIdentitySearch().get_from_node_identity(
                root_node.entity_id))
            url_name = "training_{}".format(
                get_url_name_suffix_from_referer(self.request.META.get('HTTP_REFERER'),
                                                 get_training_available_tabs(version.is_official_standard),
                                                 keep_tab)
            )
            url_kwargs = {'year': root_node.year, 'code': root_node.code}

        elif root_node.is_mini_training():
            url_name = "mini_training_{}".format(get_url_name_suffix_from_referer(self.request.META.get('HTTP_REFERER'),
                                                                                  get_mini_training_available_tabs(),
                                                                                  keep_tab))
            url_kwargs = {'year': root_node.year, 'code': root_node.code}
        elif root_node.is_learning_unit():
            url_name = "learning_unit"
            url_kwargs = {'year': root_node.year, 'acronym': root_node.code}
        else:
            url_name = "group_{}".format(get_url_name_suffix_from_referer(self.request.META.get('HTTP_REFERER'),
                                                                          get_group_available_tabs(root_node),
                                                                          keep_tab))
            url_kwargs = {'year': root_node.year, 'code': root_node.code}
        self.url = reverse(
            url_name,
            kwargs=url_kwargs
        )
        return super().get_redirect_url(*args, **kwargs)


def get_url_name_suffix_from_referer(referer: str, url_name_suffixes: List[str], keep_tab: bool = True):

    if referer and keep_tab:
        return next((suffix for suffix in url_name_suffixes if suffix in referer), SUFFIX_IDENTIFICATION)
    return SUFFIX_IDENTIFICATION
