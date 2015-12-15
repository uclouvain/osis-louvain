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

from openerp import models, fields, api, _, exceptions
import datetime


class SessionExam(models.Model):
    _name = 'osis.session_exam'
    _description = "Session Exam"

    learning_unit_year_id = fields.Many2one('osis.learning_unit_year', string='Learning unit year')
    exam_enrollment_ids = fields.One2many('osis.exam_enrollment','session_exam_id', string='Exam enrollment')

    date_session = fields.Date('Session date')
    encoding_status = fields.Selection([('COMPLETE','Complete'),('PARTIAL','Partial'),('MISSING','Missing')])
    # encoding_status = fields.Char()
    session_name = fields.Char('Session Name',compute='_get_session_name', store=True)

    session_month = fields.Char('Session month',compute='_get_session_month', store=True)#Utiliser dans le filtre pour l'encodage des notes

    academic_year_id = fields.Many2one('osis.academic_year', related="learning_unit_year_id.academic_year_id")

    learning_unit_acronym = fields.Char(related="learning_unit_year_id.acronym")
    learning_unit_title = fields.Char(related="learning_unit_year_id.title")

    notes_encoding_ids = fields.One2many('osis.notes_encoding','session_exam_id', string='Notes encoding')

    offer_filter_id = fields.Many2one('osis.offer', domain="[('id', 'in', offer_ids[0][2])]")

    offer_ids = fields.Many2many('osis.offer', compute='_get_all_offer')

    tutor_ids = fields.Many2many('osis.tutor', compute='_get_all_tutor')

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
                r.session_name = session_date.strftime("%B")


    @api.depends('date_session')
    def _get_session_month(self):
        for r in self:
            r.session_month=''
            if r.date_session:
                session_date = fields.Datetime.from_string(r.date_session)
                r.session_month = session_date.strftime("%m")

    @api.multi
    def encode_session_notes(self):
        wiz_id = self.env['osis.notes_wizard'].create({
            'acronym': self.learning_unit_acronym,

            'line_ids':[(0,0,{'notes_encoding_id': rec_notes_encoding.id,
                              'encoding_stage' : 1,
                              'student_name': rec_notes_encoding.student_name,
                              'score_1': rec_notes_encoding.score_1,
                              'justification_1':rec_notes_encoding.justification_1,
                              'score_2': rec_notes_encoding.score_2,
                              'justification_2':rec_notes_encoding.justification_2
                              }) for rec_notes_encoding in self.notes_encoding_ids],
        })

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'osis.notes_wizard',
            'res_id': wiz_id.id,
            'view_id' : self.env.ref('osis-louvain.resultswizard_form_view').id,
            'target': 'new',
        }


    @api.multi
    def double_encode_session_notes(self):
        encoding_stage_1_done = False
        for rec_notes_encoding in self.notes_encoding_ids:
            if rec_notes_encoding.encoding_stage_1_done:
                encoding_stage_1_done=True
                break

        if encoding_stage_1_done:
            print 'double_encode_session_notes'
            wiz_id = self.env['osis.notes_wizard'].create({
                'acronym': self.learning_unit_acronym,

                'line_ids':[(0,0,{'notes_encoding_id': rec_notes_encoding.id,
                                  'encoding_stage' : 2,
                                  'student_name': rec_notes_encoding.student_name,
                                  'score_1': rec_notes_encoding.score_1,
                                  'justification_1':rec_notes_encoding.justification_1,
                                  'score_2': rec_notes_encoding.score_2,
                                  'justification_2':rec_notes_encoding.justification_2
                                  }) for rec_notes_encoding in self.notes_encoding_ids],
            })
            print wiz_id.id
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'osis.notes_wizard',
                'res_id': wiz_id.id,
                'view_id' : self.env.ref('osis-louvain.double_resultswizard_form_view').id,
                'target': 'new',
            }
        else:
            raise exceptions.ValidationError(_("Encode notes before double encoding"))


    @api.multi
    def compare_session_notes(self):
        double_encoding_done = False
        for rec_notes_encoding in self.notes_encoding_ids:
            if rec_notes_encoding.double_encoding_done:
                double_encoding_done=True
                break

        if double_encoding_done:
            notes_encoding_ids=[]
            for rec in self.notes_encoding_ids:
                if rec.score_1 != rec.score_2 or rec.justification_1  != rec.justification_2:
                    notes_encoding_ids.append(rec)

            if notes_encoding_ids:
                wiz_id = self.env['osis.notes_wizard'].create({
                    'acronym': self.learning_unit_acronym,

                    'line_ids':[(0,0,{'notes_encoding_id': rec_notes_encoding.id,
                                      'encoding_stage' : 3,
                                      'student_name': rec_notes_encoding.student_name,
                                      'score_1': rec_notes_encoding.score_1,
                                      'justification_1':rec_notes_encoding.justification_1,
                                      'score_2': rec_notes_encoding.score_2,
                                      'justification_2':rec_notes_encoding.justification_2
                                      }) for rec_notes_encoding in notes_encoding_ids],
                })
                print wiz_id.id
                return {
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'osis.notes_wizard',
                    'res_id': wiz_id.id,
                    'view_id' : self.env.ref('osis-louvain.compare_resultswizard_form_view').id,
                    'target': 'new',
                }
            else:
                raise exceptions.ValidationError(_("All notes are identical"))
        else:
            raise exceptions.ValidationError(_("Encode notes before double encoding"))

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
            'view_id' : self.env.ref('osis-louvain.consulting_notes_session_form_primherit_view').id
        }


    @api.multi
    def print_session_notes(self):
        print 'print_session_notes'


        datas = {
        'ids': [self.id]
        }
        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'osis-louvain.report_session_exam_notes',
            'datas' : datas,
            }

    @api.depends('learning_unit_year_id')
    def _get_all_offer(self):
        print "compute offer_ids"
        enrollement_ids = self.env['osis.learning_unit_enrollment'].search([('learning_unit_year_id', '=', self.learning_unit_year_id.id)])
        enrol_ids = []
        for enrol in enrollement_ids:
            # if self.offer_filter_id:
            enrol_ids.append(enrol.offer_enrollment_id.offer_year_id.offer_id.id)
            self.offer_ids |= enrol.offer_enrollment_id.offer_year_id.offer_id
            # else:
            #     if self.offer_filter_id == enrol.offer_enrollment_id.offer_year_id.offer_id:
            #         enrol_ids.append(enrol.offer_enrollment_id.offer_year_id.offer_id.id)
            #         self.offer_ids |= enrol.offer_enrollment_id.offer_year_id.offer_id

    @api.depends('learning_unit_year_id')
    def _get_all_tutor(self):

        attribution_ids = self.env['osis.attribution'].search([('learning_unit_id', '=', self.learning_unit_year_id.learning_unit_id.id)])
        attrib_ids = []
        for a in attribution_ids:
            self.tutor_ids |= a.tutor_id


    @api.multi
    def xls_export_session_notes(self):
    #    @api.multi
    #
    #         :param fields_to_export: list of fields
    #         :param raw_data: True to return value in native Python type
    #         :rtype: dictionary with a *datas* matrix
    # def export_data(self, fields_to_export, raw_data=False):
        Model = self.env['osis.session_exam']

        ids =[]
        ids.append(self.id)

        field_names=[]
        field_names.append('session_name')

        read= self.env['osis.session_exam'].export_data(ids, field_names)
        result = False
        for rec in read['datas']:
            if rec[0]:
                result = rec[0]
                print rec[0]
            else:
            	result = (rec[1] or '') + ' - ' + (rec[2] or '')
                print rec[1]

        context['result']= result

        # if import_compat:
        #     columns_headers = field_names
        # else:
        #     columns_headers = [val['label'].strip() for val in fields]
        #
        #
        # return request.make_response(self.from_data(columns_headers, import_data),
        #     headers=[('Content-Disposition',
        #                     content_disposition(self.filename(model))),
        #              ('Content-Type', self.content_type)],
        #     cookies={'fileToken': token})
