# -*- coding: utf-8 -*-
from openerp import models, fields, api, tools, _
from lxml import etree

class Student_notes_reading(models.Model):
    _name = 'osis.student_notes'
    _description = 'Student notes'
    _auto = False
    _order = 'acronym'

    acronym = fields.Char('Acronym', readonly=True)
    title = fields.Char('Title', readonly=True)
    year = fields.Integer('Year', readonly=True)
    status = fields.Boolean('Status', readonly=True)
    session_name = fields.Char('Session name', readonly=True)
    session_exam_id = fields.Char('Exam id', readonly=True)
    learning_unit_year_id = fields.Integer('Learning Unit Year Id', readonly=True)
    learning_unit_id = fields.Integer('Learning Unit Id', readonly=True)
    # tutor_name = fields.Char('Tutor name', compute='_get_tutors_names' , search='_search_tutor_name')
    tutor_name = fields.Char('Tutor name', compute='_get_tutors_names')
    id_student_notes  = fields.Integer('ID student notes')


    @api.multi
    def _get_tutors_names(self):
        for r in self:
            noms=list()
            recs = self.env['osis.attribution'].search([('learning_unit_id', '=', r.learning_unit_id)])
            for at in recs:
                recs_tutor = self.env['osis.tutor'].search([('id', '=', at.tutor_id.id)])
                for rt  in recs_tutor:
                    recs_pers = self.env['osis.person'].search([('id', '=', rt.person_id.id)])
                    noms.append(recs_pers[0].name)
            string_of_names=''
            cpt=0
            for nom in noms:
                if cpt>0:
                    string_of_names += ', '
                string_of_names += nom
                cpt = cpt+1

            r.tutor_name = string_of_names

    # quand j'utilise ceci avec le search parameter on dirait que ça boucle
    # def _search_tutor_name(self, operator, value):
    #     if operator == 'like':
    #         operator = 'ilike'
    #     return [('tutor_name', operator, value)]


    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'osis_student_notes')
        cr.execute('''CREATE OR REPLACE VIEW osis_student_notes AS (
            select se.closed as status,
                   luy.title as title,
                   ay.year as year,
                   se.session_name as session_name,
                   se.id as session_exam_id,
                   se.learning_unit_year_id as learning_unit_year_id,
                   se.id as id,
                   luy.acronym as acronym,
                   lu.id as learning_unit_id
            from osis_session_exam se
                 join osis_learning_unit_year luy on se.learning_unit_year_id = luy.id
                 join osis_academic_year ay on luy.academic_year_id = ay.id
                 join osis_learning_unit lu on luy.learning_unit_id = lu.id

        )''',)


    @api.multi
    def display_students_notes(self):
       print 'methode display_students_notes'
       view_ref = self.env['ir.model.data'].get_object_reference('osis-louvain', 'student_notes_display_tree_view')
       view_id = view_ref[1] if view_ref else False

       res = {
           'type': 'ir.actions.act_window',
           'name': _('Student notes'),
           'res_model': 'osis.student_notes_display',
           'view_type': 'tree',
           'view_mode': 'tree',
           'view_id': view_id,
           'target': 'current',
           'domain':[['exam_ref','=',self.session_exam_id]]
       }

       return res
