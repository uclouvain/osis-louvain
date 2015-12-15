# -*- coding: utf-8 -*-
######################################################################
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

from openerp import models, fields, api, tools, exceptions, _
import datetime


class Attribution(models.Model):
    _name = 'osis.attribution'
    _description = "Attribution"
    _sql_constraints = [('attribution_unique','unique(tutor_id,function,learning_unit_id)','A attribution must be unique on tutor_id/learning unit/function')]


    learning_unit_id = fields.Many2one('osis.learning_unit', string='Learning unit')
    tutor_id = fields.Many2one('osis.tutor', string='Tutor')

    start_date = fields.Date('Start date', required = True)
    end_date = fields.Date('End date')
    function = fields.Selection([('UNKNOWN','Unknown'),('PROFESSOR','Professor'),('COORDINATOR','Coordinator')])

    @api.constrains('start_date','end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date:
                if record.end_date:
                    if fields.Datetime.from_string(record.start_date) > fields.Datetime.from_string(record.end_date):
                        raise exceptions.ValidationError(_("End date must be greater or equal than start year"))

    def name_get(self,cr,uid,ids,context=None):
        result={}
        for record in self.browse(cr,uid,ids,context=context):
            name = u"%s" % record.tutor_id.person_id.name
            result[record.id] = u" %s" % (name)
        return result.items()
