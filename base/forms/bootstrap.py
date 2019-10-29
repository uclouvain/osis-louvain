##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django import forms

from osis_common.decorators.deprecated import deprecated


class BootstrapModelForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(BootstrapModelForm, self).__init__(*args, **kwargs)
        set_form_control(self)


# Why ? Still used
@deprecated
def set_form_control(self):
    for field in iter(self.fields):
        attr_class = self.fields[field].widget.attrs.get('class') or ''
        # Exception because we don't apply form-control on widget checkbox
        if self.fields[field].widget.template_name != 'django/forms/widgets/checkbox.html':
            if isinstance(self.fields[field].widget, forms.MultiWidget):
                for widget in self.fields[field].widget.widgets:
                    widget.attrs['class'] = ' '.join((widget.attrs.get('class', ''), 'form-control'))
            else:
                self.fields[field].widget.attrs['class'] = ' '.join((attr_class, 'form-control'))
