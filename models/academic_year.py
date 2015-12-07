# -*- coding: utf-8 -*-
##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    A copy of this license - GNU Affero General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################

from openerp import models, fields, api, exceptions, _
import datetime

class Academic_year(models.Model):
    _name = "osis.academic_year"
    _description = "Academic year"
    _rec_name = "year"

    year = fields.Integer('Year', required = True)
    start_date = fields.Date('Start date')
    end_date = fields.Date('End date')
    offer_year_ids = fields.One2many('osis.offer_year', 'academic_year_id', string='Offer year')
    learning_unit_year_ids = fields.One2many('osis.learning_unit_year', 'academic_year_id', string='Learnint unit year')

    @api.constrains('start_date','end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date:
                if record.end_date:
                    if fields.Datetime.from_string(record.start_date) > fields.Datetime.from_string(record.end_date):
                        raise exceptions.ValidationError(_("End date must be greater or equal than start year"))
