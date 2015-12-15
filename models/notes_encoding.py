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

class Notes_encoding(models.Model):
        _name = 'osis.notes_encoding'
        _description = "Notes encoding"

        score_1 = fields.Float('Score 1')
        justification_1 = fields.Selection([('ILL',_('Ill')),('ABSENT',_('Absent')),('JUSTIFIED_ABSENCE',_('Justified absence')),('CHEATING',_('Cheating')),('SCORE_MISSING',_('Score missing'))])
        score_2 = fields.Float('Score 2')
        justification_2 = fields.Selection([('ILL',_('Ill')),('ABSENT',_('Absent')),('JUSTIFIED_ABSENCE',_('Justified absence')),('CHEATING',_('Cheating')),('SCORE_MISSING',_('Score missing'))])
        notes_status = fields.Char(compute = '_get_notes_status')
        session_exam_id = fields.Many2one('osis.session_exam', string='Session exam')
        exam_enrollment_id =fields.Many2one('osis.exam_enrollment', string='Exam enrollment')

        student_name = fields.Char(related="exam_enrollment_id.learning_unit_enrollment_id.offer_enrollment_id.student_id.person_id.last_name")
        student_first_name = fields.Char(related="exam_enrollment_id.learning_unit_enrollment_id.offer_enrollment_id.student_id.person_id.first_name")
        student_registration_number = fields.Char(related="exam_enrollment_id.learning_unit_enrollment_id.offer_enrollment_id.student_id.registration_number")
        offer = fields.Char(related="exam_enrollment_id.learning_unit_enrollment_id.offer_enrollment_id.offer_year_id.offer_id.acronym")

        encoding_stage_1_done = fields.Boolean('Encoding stage 1 done', default = False)
        double_encoding_done = fields.Boolean('Double encoding done', default = False)
        # offer_id = fields.Integer(related="exam_enrollment_id.learning_unit_enrollment_id.offer_enrollment_id.offer_year_id.offer_id.id")
        @api.multi
        def _get_notes_status(self):
            notes_status = 'NULL'
            for record in self:
                if record.score_1 and record.score_2:
                    if record.score_1 != record.score_2:
                        record.notes_status = 'DIFFERENT'
                    else:
                        record.notes_status = 'EQUAL'
                if record.justification_1 and record.justification_2:
                    if record.justification_1 != record.justification_2:
                        record.notes_status = 'DIFFERENT'
                    else:
                        record.notes_status = 'EQUAL'
                if (record.justification_1 and not record.justification_2) or (record.justification_2 and not record.justification_1):
                    record.notes_status = 'DIFFERENT'
