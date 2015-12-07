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

class Offer_enrollment(models.Model):
    _name = 'osis.offer_enrollment'
    _description = 'Offer enrollment'
    _order = 'offer_year_id'

    offer_year_id = fields.Many2one('osis.offer_year', string='Offer year')
    student_id = fields.Many2one('osis.student', string='Student')
    date_enrollment = fields.Date('Enrollment date')
    learning_unit_enrollment_ids = fields.One2many('osis.learning_unit_enrollment', 'offer_enrollment_id', string='Learning unit enrollment')

    def name_get(self,cr,uid,ids,context=None):
        result={}
        for record in self.browse(cr,uid,ids,context=context):
            offer_acronym = u"%s" % record.offer_year_id.offer_id.acronym
            offer_title = u"%s" % record.offer_year_id.offer_id.title
            offer_year = u"%s" % record.offer_year_id.academic_year_id.year
            student = u"%s" % record.student_id.person_id.name
            result[record.id] = u"%s - %s - %s - %s" % (offer_acronym,offer_title,offer_year,student)
        return result.items()
