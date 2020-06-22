from django.urls import reverse
from django.views.generic import RedirectView

from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.repositories.node import NodeRepository


class IdentificationRedirectView(RedirectView):
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        year = self.kwargs['year']
        code = self.kwargs['code']
        root_node = NodeRepository().get(NodeIdentity(code=code, year=year))
        if root_node.is_training():
            url_name = "training_identification"
            url_kwargs = {'year': root_node.year, 'code': root_node.code}
        elif root_node.is_mini_training():
            url_name = "mini_training_identification"
            url_kwargs = {'year': root_node.year, 'code': root_node.code}
        elif root_node.is_learning_unit():
            url_name = "learning_unit"
            url_kwargs = {'year': root_node.year, 'acronym': root_node.code}
        else:
            url_name = "group_identification"
            url_kwargs = {'year': root_node.year, 'code': root_node.code}
        self.url = reverse(url_name, kwargs=url_kwargs)
        return super().get_redirect_url(*args, **kwargs)
