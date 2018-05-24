from django.urls import reverse


class Helper:
    def _get_url(self, year, language, acronym):
        return reverse(self.URL_NAME,
                       kwargs=dict(year=year, language=language, acronym=acronym))

    def _get_response(self, year, language, acronym):
        return self.client.get(self._get_url(year, language, acronym), format='json')