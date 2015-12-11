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

class Notes_encoding(models.Model):
        _name = 'osis.notes_encoding'
        _description = "Notes encoding"

        score_1 = fields.Float('Score 1')
        score_2 = fields.Float('Score 2')

        session_exam_id = fields.Many2one('osis.session_exam', string='Session exam')
        exam_enrollment_id =fields.Many2one('osis.exam_enrollment', string='Exam enrollment')

        student_name = fields.Char(related="exam_enrollment_id.learning_unit_enrollment_id.offer_enrollment_id.student_id.person_id.last_name")
