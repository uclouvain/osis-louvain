import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _


@login_required
def geocode(request):
    """
    This is just a proxy to the geocoding service
    :param request:
    :return:
    """
    search = request.GET.get('q')
    if not search:
        return JsonResponse({'error': _("Missing search address")})

    url = "{esb_api}/{endpoint}".format(
        esb_api=settings.ESB_API_URL,
        endpoint=settings.ESB_GEOCODING_ENDPOINT,
    )
    response = requests.get(url, {'address': search}, headers={
        'Authorization': settings.ESB_AUTHORIZATION,
    })
    if response.status_code != 200:
        return JsonResponse({'error': _("No result!")})

    # Only return what's needed
    results = []
    for result in response.json()['results']:
        results.append({
            'label': result['formatted_address'],
            'location': result['geometry']['location'],
        })
    return JsonResponse({'results': results})
