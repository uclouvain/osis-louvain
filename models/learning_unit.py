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

from openerp import models, fields, api

class Learning_unit(models.Model):
    _name = 'osis.learning_unit'
    _description = 'Learning unit'

    start_year = fields.Integer('Start year', required = True)
    end_year = fields.Integer('End year', required = True)

    attribution_ids = fields.One2many('osis.attribution', 'learning_unit_id', string='Attribution')
    learning_unit_year_ids = fields.One2many('osis.learning_unit_year', 'learning_unit_id' ,string='Learning Unit Year')

    def name_get(self,cr,uid,ids,context=None):
        result={}
        for record in self.browse(cr,uid,ids,context=context):
            result[record.id] = u"%s - %s" % (record.start_year,record.end_year)
        return result.items()


    @api.constrains('start_year','end_year')
    def _check_dates(self):
        for record in self:
            if record.start_year:
                if record.start_year < 1000 or record.start_year > 9999:
                    raise exceptions.ValidationError(_("Start year must be on 4 digits"))
                if record.end_year:
                    if record.end_year < 1000 or record.end_year > 9999:
                        raise exceptions.ValidationError(_("End year must be on 4 digits"))
                    if record.start_year > record.end_year:
                        raise exceptions.ValidationError(_("End year must be greater or equal than start year"))
