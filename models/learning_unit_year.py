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

class Learning_unit_year(models.Model):
    _name = 'osis.learning_unit_year'
    _description = "Learning unit year"

    title = fields.Char('Title', required = True)
    acronym = fields.Char('Acronym', required = True)

    academic_year_id = fields.Many2one('osis.academic_year', string='Academic year')
    learning_unit_id = fields.Many2one('osis.learning_unit', string='Learning unit')

    credits = fields.Float("Credits", default=0)
    learning_unit_enrollment_ids = fields.One2many('osis.learning_unit_enrollment', 'learning_unit_year_id', string='Learning unit enrollment')
    session_exam_ids = fields.One2many('osis.session_exam', 'learning_unit_year_id', string='Session exam')



    def name_get(self,cr,uid,ids,context=None):
        result={}
        for record in self.browse(cr,uid,ids,context=context):
            title = u"%s" % record.title
            acronym = u"%s" % record.acronym
            result[record.id] = u"%s - %s" % (acronym,title)
        return result.items()
