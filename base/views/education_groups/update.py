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

from dal import autocomplete
from django.utils.html import format_html

from base.models.certificate_aim import CertificateAim


class CertificateAimAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return CertificateAim.objects.none()

        qs = CertificateAim.objects.all()

        if self.q:
            if self.q.isdigit():
                qs = qs.filter(code=self.q)
            else:
                qs = qs.filter(description__icontains=self.q)

        section = self.forwarded.get('section', None)
        if section:
            qs = qs.filter(section=section)

        return qs

    def get_result_value(self, result: CertificateAim):
        return result.code

    def get_result_label(self, result: CertificateAim):
        return format_html('{} - {} {}', result.section, result.code, result.description)
