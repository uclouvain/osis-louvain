from django import forms
from django.contrib.gis.geos import Point
from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _

from base.forms.widgets import LatLonField


class LatLonFieldTestCase(TestCase):
    def test_latlonfield_not_required(self):
        class TestForm(forms.Form):
            location = LatLonField(required=False)

        form = TestForm({})
        self.assertTrue(form.is_valid())

        form = TestForm({'location_1': 100})
        self.assertFalse(form.is_valid())
        self.assertIn(_('Enter a valid latitude.'), form.errors['location'])

        form = TestForm({'location_0': None, 'location_1': 100})
        self.assertFalse(form.is_valid())
        self.assertIn(_('Enter a valid latitude.'), form.errors['location'])

        form = TestForm({'location_0': "30.0", 'location_1': ""})
        self.assertFalse(form.is_valid())
        self.assertIn(_('Enter a valid longitude.'), form.errors['location'])

        form = TestForm({'location_0': "", 'location_1': ""})
        self.assertTrue(form.is_valid())

        form = TestForm({'location_0': -10, 'location_1': 100})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data, {
            'location': 'SRID=4326;POINT(100.000000 -10.000000)'
        })

    def test_latlonfield_required(self):
        class TestForm(forms.Form):
            location = LatLonField()

        form = TestForm({})
        self.assertFalse(form.is_valid())

        form = TestForm({'location_0': 100})
        self.assertFalse(form.is_valid())

        form = TestForm({'location_0': -99, 'location_1': 200})
        self.assertFalse(form.is_valid())

        form = TestForm({'location_0': -10, 'location_1': 100})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data, {
            'location': 'SRID=4326;POINT(100.000000 -10.000000)'
        })

        form = TestForm(initial={'location': Point(-3.14, 37.5)})
        subwidgets = form['location'].subwidgets[0]
        self.assertEqual(subwidgets.data['subwidgets'][0]['value'], '37.5')
        self.assertEqual(subwidgets.data['subwidgets'][1]['value'], '-3.14')


class LatLonWidgetTestCase(TestCase):
    @override_settings(MAPBOX={
        'ACCESS_TOKEN': "foobar",
        'CSS_PATHS': ['barbaz'],
        'JS_PATHS': ['bazbar'],
    })
    def test_widget_render(self):
        class TestForm(forms.Form):
            location = LatLonField()

        form = TestForm()
        self.assertIn("foobar", str(form))
        self.assertIn("barbaz", str(form.media))
        self.assertIn("bazbar", str(form.media))
        self.assertIn("css/lat-lon-widget.css", str(form.media))
        self.assertIn("js/lat-lon-widget.js", str(form.media))
