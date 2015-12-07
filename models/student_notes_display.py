# -*- coding: utf-8 -*-

from openerp import models, fields, api, tools, _
import openerp.pooler as pooler
import openerp
from openerp import SUPERUSER_ID
from lxml import etree

class Student_notes_display(models.Model):
    _name = 'osis.student_notes_display'
    _description = "Student notes display"
    _auto = False


    title_learning_unit = fields.Char('Title learning unit')
    # title_offer = fields.Char('Title offer')
    year = fields.Integer('Year')
    session_name = fields.Char('Session name')
    session_exam_id = fields.Char('Session exam id')
    student_name = fields.Char('Student name')
    score = fields.Char('Score')
    student_ref  = fields.Integer('Student ref')
    student_registration_number = fields.Char('Registration number')
    learning_unit_ref = fields.Integer('Learning unit id')
    learning_unit_enrollment_id = fields.Integer('Learning unit enrollment id')
    exam_enrollment_id = fields.Integer('Exam enrollment id')
    offer_id = fields.Integer('Offer id')
    offer_acronym = fields.Char('Offer acronym', compute = '_get_offer_title')
    color = fields.Char('Color', compute = '_get_color')

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'osis_student_notes_display')

        cr.execute('''CREATE OR REPLACE VIEW osis_student_notes_display AS (
            select ee.session_exam_id as session_exam_id,
                   p.name as student_name,
                   ee.score as score,
                   oe.student_id as student_ref,
                   ee.id as id,
                   ee.learning_unit_enrollment_id as learning_unit_enrollment_id,
                   ee.id as exam_enrollment_id,
                   oy.offer_id as offer_id,
                   s.registration_number as student_registration_number,
                   lue.learning_unit_year_id as learning_unit_ref

            from osis_exam_enrollment ee
                 join osis_learning_unit_enrollment lue on  ee.learning_unit_enrollment_id=lue.id
                 join osis_offer_enrollment oe on lue.offer_enrollment_id=oe.id
                 join osis_student s on oe.student_id= s.id
                 join osis_person p on  s.person_id=p.id
                 join osis_offer_year oy on oe.offer_year_id=oy.id
                 join osis_offer o on oy.offer_id = o.id
                 where ee.encoding_status is null or ee.encoding_status != 'SUBMITTED'
            )''')


    @api.multi
    def _get_color(self):
        old_offer_id  = None
        cpt = 1
        for r in self:

            if old_offer_id is None:
                old_offer_id=r.offer_id
                r.color ="couleur%d" % (cpt,)
            else:
                if old_offer_id != r.offer_id:
                    old_offer_id = r.offer_id
                    cpt = cpt+1

                r.color ="couleur%d" % (cpt,)


    def submit_results(self, cr, uid, ids, context=None) :
        for rec in self.pool.get('osis.exam_enrollment').browse(cr, uid, ids, context=context):

            if rec.score is not None:
                ids_update = [rec.id]
                self.pool.get('osis.exam_enrollment').write(cr, uid, ids_update, {'encoding_status': 'SUBMITTED'})


    def wizard_encode_results(self, cr, uid, ids, context=None) :
        # ATTENTION : il faut simplifier cette requête (lecgture assez difficile)
        model_exam_enrollment = self.pool.get('osis.exam_enrollment')
        model_learning_unit_enrollment = self.pool.get('osis.learning_unit_enrollment')
        model_student = self.pool.get('osis.student')
        model_offer_enrollment = self.pool.get('osis.offer_enrollment')
        student_score_list=list()
        for exam_enrollment_id in ids:
            recs_ee = model_exam_enrollment.search(cr,uid,[('id','=',exam_enrollment_id)])
            for rec_ee in model_exam_enrollment.browse(cr, uid, recs_ee, context=context):

                session_exam_id = rec_ee.session_exam_id
                recs_lue = model_learning_unit_enrollment.search(cr,uid,[('id','=',rec_ee.learning_unit_enrollment_id.id)])
                for rec_lue in model_learning_unit_enrollment.browse(cr, uid, recs_lue, context=context):
                    recs_oe = model_offer_enrollment.search(cr,uid,[('id','=',rec_lue.offer_enrollment_id.id)])
                    for rec_oe in model_offer_enrollment.browse(cr, uid, recs_oe, context=context):
                        recs_s = model_student.search(cr,uid,[('id','=',rec_oe.student_id.id)])
                        for rec_s in model_student.browse(cr, uid, recs_s, context=context):
                            score_line = Line(rec_oe.student_id.id,rec_ee.score,exam_enrollment_id)
                            student_score_list.append(score_line)


        wiz_id = self.pool.get('osis.wizard.result').create(cr, uid,{
            'exam_enrollment_id': exam_enrollment_id,
            'line_ids':[(0,0,{'student_id': student.student_id,'result': student.score,'exam_enrollment_id':student.exam_enrollment_id}) for student in student_score_list],
        })


        idd = None
        for rec_w in self.pool.get('osis.wizard.result').browse(cr, uid, wiz_id, context=context):

            idd=rec_w.id

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'osis.wizard.result',
            'res_id': idd,
            'target': 'new',
        }


    def remove_ir_values_button(self,cr,uid):
            rec_id=self.pool.get('ir.values').search(cr,uid,[('name', 'ilike', 'Encoding notes')])
            if rec_id:
                self.pool.get('ir.values').unlink(cr,uid,rec_id)

            rec_id=self.pool.get('ir.values').search(cr,uid,[('name', 'ilike', 'Submitting notes')])
            if rec_id:
                self.pool.get('ir.values').unlink(cr,uid,rec_id)


    def couleurs(self):
        return "blue:student_registration_number=='ddd';red:student_registration_number!='ddd'"

    def fields_view_get(self, cr, uid, view_id=None, view_type=None, context=None, toolbar=False, submenu=False):

        res = super(Student_notes_display,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if view_type == 'tree':
            print res

            doc =  etree.fromstring(res['arch'])
            for node in doc.xpath("/tree/colors"):
                print 'zut node' , node
            #
            # for node in doc.xpath("/tree/field[@name='score']"):
            #     print 'zut node' , node

            res['arch'] = etree.tostring(doc)
        encoding = False
        if context is None:
            context = {}

        if context.get('encoding') is not None:
            encoding = context.get('encoding')

            if encoding:
                # on crée les 2 boutons
                rec_id=self.pool.get('ir.values').search(cr,uid,[('name', 'ilike', 'Encoding notes')])

                if rec_id:
                    self.remove_ir_values_button(cr,uid)

                id_action_server=self.pool.get('ir.actions.server').search(cr,uid,[('name', 'ilike', 'Encoding notes')])
                vals=dict({})
                vals['id'] = "encoding_notes_more_item"
                vals['key2'] = "client_action_multi"
                vals['model'] = "osis.student_notes_display"
                vals['name'] = "Encoding notes"
                vals['value'] = "ir.actions.server,"+str(id_action_server[0])
                self.pool.get('ir.values').create(cr,uid,vals,context)

                id_action_server=self.pool.get('ir.actions.server').search(cr,uid,[('name', 'ilike', 'Submitting notes')])
                vals=dict({})
                vals['id'] = "submitting_more_item"
                vals['key2'] = "client_action_multi"
                vals['model'] = "osis.student_notes_display"
                vals['name'] = "Submitting notes"
                vals['value'] = "ir.actions.server,"+str(id_action_server[0])
                self.pool.get('ir.values').create(cr,uid,vals,context)

            else:
                self.remove_ir_values_button(cr,uid)

        return res

    @api.multi
    def _get_offer_title(self):
        for r in self:
            recs = self.env['osis.offer'].search([('id', '=', r.offer_id)])
            for at in recs:
                r.offer_acronym = at.acronym


    @api.multi
    def _check_color(self):
        cpt=0
        for r in self:
            r.color=cpt
            cpt=cpt+1

            # res = {}
            # for record in self.browse(cr, uid, ids, context):
            #     color = 0
            #     if record.student_name == u'Roux Bertrand':
            #         color = 4
            #         print 'zut 4'
            #     elif record.student_name == u'Segers Sophie':
            #         color = 3
            #         print 'zut 3'
            #     res[record.id] = color
            # return res


class ExamResults(models.Model):
    _name = 'osis.exam.result'

    exam_enrollment_id = fields.Many2one('osis.exam_enrollment', string='Exam')
    student_id = fields.Many2one('osis.student', string='Student', required=True)
    result = fields.Float('Result')

class Line:

    def __init__(self, student_id ,score,exam_enrollment_id) :
        self.student_id = student_id
        self.score = score
        self.exam_enrollment_id = exam_enrollment_id
