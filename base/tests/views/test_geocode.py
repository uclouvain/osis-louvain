from unittest import mock

from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from base.tests.factories.user import UserFactory


class GecodeViewTestCase(TestCase):
    def test_geocode_view_anonymous(self):
        response = self.client.get('/geocoding')
        self.assertNotEqual(response.status_code, 200)

    def test_geocode_view_no_query(self):
        self.client.force_login(UserFactory())
        response = self.client.get('/geocoding')
        self.assertEqual(response.json(), {
            'error': _("Missing search address"),
        })

    @mock.patch('requests.get')
    def test_geocode_view(self, mock_request_get):
        self.client.force_login(UserFactory())

        mock_response = mock.Mock()
        mock_response.content_type = "application/json"
        mock_response.json.return_value = {'results': [
            {
                'formatted_address': '10 Downing St, Westminster, London, UK',
                'geometry': {'location': [51.5033635, -0.1298135]},
            }
        ]}
        mock_response.status_code = 200
        mock_request_get.return_value = mock_response

        response = self.client.get('/geocoding', {'q': "10 Downing Street"})

        self.assertTrue(mock_request_get.called)
        self.assertEqual(response.json(), {'results': [
            {
                'label': '10 Downing St, Westminster, London, UK',
                'location': [51.5033635, -0.1298135],
            }
        ]})

    @mock.patch('requests.get')
    def test_geocode_view_error(self, mock_request_get):
        self.client.force_login(UserFactory())

        mock_response = mock.Mock()
        mock_response.status_code = 500
        mock_request_get.return_value = mock_response

        response = self.client.get('/geocoding', {'q': "Hiding place"})

        self.assertTrue(mock_request_get.called)
        self.assertEqual(response.json(), {'error': _("No result!")})
