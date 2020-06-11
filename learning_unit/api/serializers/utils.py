##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from rest_framework import serializers
from rest_framework.reverse import reverse


class LearningUnitGetUrlMixin:
    def __init__(self, **kwargs):
        super().__init__(view_name='learning_unit_api_v1:learningunits_read', **kwargs)

    def get_url(self, obj, view_name, request, format):
        url_kwargs = {
            'acronym': obj.acronym,
            'year': obj.academic_year.year
        }
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)


class LearningUnitGetUrlFromDDDMixin(LearningUnitGetUrlMixin):
    def get_url(self, obj, view_name, request, format):
        url_kwargs = {
            'acronym': obj.code,
            'year': obj.academic_year.year
        }
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)


class LearningUnitHyperlinkedIdentityField(LearningUnitGetUrlMixin, serializers.HyperlinkedIdentityField):
    pass


class LearningUnitDDDHyperlinkedIdentityField(LearningUnitGetUrlFromDDDMixin, serializers.HyperlinkedIdentityField):
    pass


class LearningUnitHyperlinkedRelatedField(LearningUnitGetUrlMixin, serializers.HyperlinkedRelatedField):
    pass
