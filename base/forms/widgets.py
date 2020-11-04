from django import forms
from django.conf import settings
from django.core import validators
from django.utils.translation import gettext_lazy as _


class LatLonWidget(forms.MultiWidget):
    """
    A Widget that splits Point input into two latitude/longitude boxes.
    """
    template_name = 'address/widgets/lat-long-widget.html'

    def __init__(self, attrs=None):
        widgets = (
            forms.NumberInput(attrs={'placeholder': _("Latitude"), 'step': 'any'}),
            forms.NumberInput(attrs={'placeholder': _("Longitude"), 'step': 'any'}),
        )
        super(LatLonWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return tuple(reversed(value.coords))
        return None, None

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['MAPBOX_ACCESS_TOKEN'] = settings.MAPBOX['ACCESS_TOKEN']
        return context

    @property
    def media(self):
        return forms.Media(
            css={'all': settings.MAPBOX['CSS_PATHS'] + [
                'css/lat-lon-widget.css',
            ]},
            js=settings.MAPBOX['JS_PATHS'] + ['js/lat-lon-widget.js'],
        )


class LatLonField(forms.MultiValueField):
    widget = LatLonWidget
    srid = 4326

    default_error_messages = {
        'invalid_latitude': _('Enter a valid latitude.'),
        'invalid_longitude': _('Enter a valid longitude.'),
    }

    def __init__(self, *args, **kwargs):
        fields = (
            forms.FloatField(min_value=-90, max_value=90),
            forms.FloatField(min_value=-180, max_value=180),
        )
        super(LatLonField, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            # Raise a validation error if latitude or longitude is empty
            # (possible if LatLonField has required=False).
            if data_list[0] in validators.EMPTY_VALUES:
                raise forms.ValidationError(
                    self.error_messages['invalid_latitude']
                )
            if data_list[1] in validators.EMPTY_VALUES:
                raise forms.ValidationError(
                    self.error_messages['invalid_longitude']
                )
            # SRID=4326;POINT(lon lat)
            srid_str = 'SRID=%d' % self.srid
            point_str = 'POINT(%f %f)' % tuple(reversed(data_list))
            return ';'.join([srid_str, point_str])
        return None
