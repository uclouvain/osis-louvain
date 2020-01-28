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
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from osis_common.models import osis_model_admin


class LearningClassYearAdmin(osis_model_admin.OsisModelAdmin):
    list_display = ('learning_component_year', 'acronym')
    search_fields = ['acronym']


only_letters_validator = RegexValidator(r'^[a-zA-Z]*$', _('Only letters are allowed.'))


class LearningClassYear(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    learning_component_year = models.ForeignKey(
        'base.LearningComponentYear',
        on_delete=models.CASCADE
    )
    acronym = models.CharField(max_length=3, validators=[only_letters_validator])
    description = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return u'{}-{}'.format(self.learning_component_year.acronym, self.acronym)
