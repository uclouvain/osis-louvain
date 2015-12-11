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

from openerp import models, fields, api, _
import datetime


class SessionExam(models.Model):
    _name = 'osis.session_exam'
    _description = "Session Exam"

    learning_unit_year_id = fields.Many2one('osis.learning_unit_year', string='Learning unit year')
    exam_enrollment_ids = fields.One2many('osis.exam_enrollment','session_exam_id', string='Exam enrollment')

    date_session = fields.Date('Session date')
    closed = fields.Boolean('Status')
    session_name = fields.Char('Session Name',compute='_get_session_name', store=True)

    academic_year_id = fields.Many2one('osis.academic_year', related="learning_unit_year_id.academic_year_id")

    learning_unit_acronym = fields.Char(related="learning_unit_year_id.acronym")
    learning_unit_title = fields.Char(related="learning_unit_year_id.title")

    notes_encoding_ids = fields.One2many('osis.notes_encoding','session_exam_id', string='Notes encoding')


    def name_get(self,cr,uid,ids,context=None):
        result={}
        for record in self.browse(cr,uid,ids,context=context):
            name_build = ''
            if record.learning_unit_year_id:
                name_build += str(record.learning_unit_year_id.academic_year_id.year)
                if record.learning_unit_year_id.title:
                    name_build+= ' - '
                    name_build += record.learning_unit_year_id.title
            if record.session_name:
                if record.session_name:
                    name_build+= ' - '
                name_build += record.session_name
            result[record.id]  = name_build
        return result.items()

    @api.depends('date_session')
    def _get_session_name(self):
        for r in self:
            r.session_name=''
            if r.date_session:
                session_date = fields.Datetime.from_string(r.date_session)
                r.session_name=session_date.strftime("%B")

    @api.multi
    def open_session_notes(self):
        self.ensure_one()
        for rec in self.exam_enrollment_ids:
            rec_notes_encoding =  self.env['osis.notes_encoding'].search([('exam_enrollment_id' ,'=', rec.id)])
            if rec_notes_encoding:
                print 'kk'
            else:
                self.env['osis.notes_encoding'].create({'session_exam_id':self.id,'exam_enrollment_id':rec.id})

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'osis.session_exam',
            'res_id': self.id,
            'target': 'current',
            'view_id' : self.env.ref('osis-louvain.encoding_notes_session_form').id
        }
