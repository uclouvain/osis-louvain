from openerp import models, fields, api, exceptions, _

class NotesWizard(models.TransientModel):
    _name = 'osis.notes_wizard'


    acronym = fields.Char('Learning unit')
    line_ids = fields.One2many('osis.wizard.note.line', 'result_id')

    @api.one
    def validate_results(self):
        for result in self.line_ids:
            print result.notes_encoding_id
            res_ee_ids = self.env['osis.notes_encoding'].search([('id', '=', result.notes_encoding_id.id)])
            if res_ee_ids:
                if result.encoding_stage == 1:
                    res_ee_ids.write({'score_1': result.score_1,'justification_1':result.justification_1,'encoding_stage_1_done':True})
                else:
                    if result.encoding_stage == 2:
                        res_ee_ids.write({'score_2': result.score_2,'justification_2':result.justification_2,'double_encoding_done':True})
                    else:
                        res_ee_ids.write({'score_1': result.score_1,'justification_1':result.justification_1,'score_2': result.score_2,'justification_2':result.justification_2})
        return True

    @api.one
    def submit_results(self):
        #si dessous copie de validate_results car je n'arrivais pas a faire appel a la fonction
        for result in self.line_ids:
            print result.notes_encoding_id
            res_ee_ids = self.env['osis.notes_encoding'].search([('id', '=', result.notes_encoding_id.id)])
            if res_ee_ids:
                if result.encoding_stage == 1:
                    res_ee_ids.write({'score_1': result.score_1,'justification_1':result.justification_1,'encoding_stage_1_done':True})
                else:
                    if result.encoding_stage == 2:
                        res_ee_ids.write({'score_2': result.score_2,'justification_2':result.justification_2,'double_encoding_done':True})
                    else:
                        res_ee_ids.write({'score_1': result.score_1,'justification_1':result.justification_1,'score_2': result.score_2,'justification_2':result.justification_2})
        #ici on va sauver dans exam_enrollment et changer le status
        for rec in self.line_ids:
            for rec_note in rec.notes_encoding_id:
                print 'zut '+str(rec_note.score_1)
                rec_note.exam_enrollment_id.write({'score': rec_note.score_1,'justification': rec_note.justification_1,'encoding_status':'SUBMITTED'})
                #ici il faut supprimer l'enregistrement notes_encoding
                rec_note.unlink()
        return True


    @api.multi
    def double_encoding(self):
        self.ensure_one()
        print 'double_encoding'
        print 'double_encode_session_notes'
        notes_encoding_ids =  []
        for result in self.line_ids:
            print result.notes_encoding_id
            rec = self.env['osis.notes_encoding'].search([('id', '=', result.notes_encoding_id.id)])
            if rec :
                notes_encoding_ids.append(rec)

        wiz_id = self.env['osis.notes_wizard'].create({
            'acronym': 'dddd',

            'line_ids':[(0,0,{'notes_encoding_id': rec_notes_encoding.id,
                              'encoding_stage' : 2,
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
            'view_id' : self.env.ref('osis-louvain.double_resultswizard_form_view').id,
            'target' : 'new'
        }


class NotesWizardLine(models.TransientModel):
    _name = 'osis.wizard.note.line'

    result_id = fields.Many2one('osis.notes_wizard')
    encoding_stage = fields.Integer()
    notes_encoding_id = fields.Many2one('osis.notes_encoding')
    student_name = fields.Char('Student')
    score_1 = fields.Float('Score 1')
    justification_1 = fields.Selection([('ILL',_('Ill')),('ABSENT',_('Absent')),('JUSTIFIED_ABSENCE',_('Justified absence')),('CHEATING',_('Cheating')),('SCORE_MISSING',_('Score missing'))])
    score_2 = fields.Float('Score 2')
    justification_2 = fields.Selection([('ILL',_('Ill')),('ABSENT',_('Absent')),('JUSTIFIED_ABSENCE',_('Justified absence')),('CHEATING',_('Cheating')),('SCORE_MISSING',_('Score missing'))])
