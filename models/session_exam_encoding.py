from openerp import models, fields, api, exceptions, _

class SessionExamEncoding(models.TransientModel):
    _name = 'osis.session_exam_encoding'

    tutor = fields.Many2one('osis.tutor', string='Tutor')
    academic_year = fields.Many2one('osis.academic_year', string='Academic year')
    session_month_selection = fields.Selection([('JANUARY','January'),('JUNE','June'),('SEPTEMBER','September')])
    session_exam_ids = fields.Many2many('osis.session_exam', 'rel_sessions', 'session_exam_encoding_id','session_exam_id',string='Sessions')


    @api.onchange('tutor','academic_year','session_month_selection')
    def _session_list(self):
        if self.tutor and self.academic_year:
            self.session_exam_ids = self.env['osis.session_exam'].search([('learning_unit_year_id.learning_unit_id.attribution_ids.tutor_id', '=', self.tutor.id),
                                                         ('learning_unit_year_id.academic_year_id', '=', self.academic_year.id)])
                                                        #  ('session_name', '=', self.session_month_selection)])
            print self.session_exam_ids
        else:
            self.session_exam_ids=None
