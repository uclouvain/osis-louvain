from django.conf.urls import url
from rest_framework_swagger.views import get_swagger_view

from webservices.views import ws_catalog_group
from webservices.views import ws_catalog_offer

schema_view = get_swagger_view(title='Training Catalog API')

urlpatterns = [
    url('^v0.1/catalog/offer/(?P<year>[0-9]{4})/(?P<language>[a-zA-Z]{2})/(?P<acronym>[a-zA-Z0-9]+)$',
        ws_catalog_offer,
        name='v0.1-ws_catalog_offer'),
    url('^v0.1/catalog/group/(?P<year>[0-9]{4})/(?P<language>[a-zA-Z]{2})/(?P<acronym>[a-zA-Z0-9]+)$',
        ws_catalog_group,
        name='v0.1-ws_catalog_group'),
    url(r'^doc$', schema_view),
]
