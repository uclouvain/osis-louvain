from openerp import models, fields, api, exceptions, _
from datetime import datetime

class SessionExamEncoding(models.TransientModel):
    _name = 'osis.session_exam_encoding'

    def _get_default_academic_year(self):

        today = datetime.now()
        today_str = fields.Datetime.to_string(today)
        recs = self.env['osis.academic_year'].search([('start_date', '<=', today_str),
                                                     ('end_date', '>=', today_str)])
        if recs:
            for rec in recs:
                return rec
        return None;


    def _get_default_session_name(self):
        today = datetime.now()
        month_num = today.strftime("%m")
        print month_num
        if month_num > 1 and month_num<=6:
            return '06'
        if month_num > 6 and month_num<=9:
            return '09'
        else:
            return '01'


    tutor = fields.Many2one('osis.tutor', string='Tutor')
    academic_year = fields.Many2one('osis.academic_year', string='Academic year', default=_get_default_academic_year)
    session_month_selection = fields.Selection([('01','January'),('06','June'),('09','September')], default = _get_default_session_name)
    session_exam_ids = fields.Many2many('osis.session_exam', 'rel_sessions', 'session_exam_encoding_id','session_exam_id',string='Sessions', readonly=True)


    @api.onchange('tutor','academic_year','session_month_selection')
    def _session_list(self):
        if self.tutor and self.academic_year and self.session_month_selection:
            print "if"
            self.session_exam_ids = self.env['osis.session_exam'].search([
                                                         ('learning_unit_year_id.learning_unit_id.attribution_ids.tutor_id', '=', self.tutor.id),
                                                         ('learning_unit_year_id.academic_year_id', '=', self.academic_year.id),
                                                         ('session_month', '=', self.session_month_selection)])
            print self.session_exam_ids
        else:
            self.session_exam_ids=None

    # @api.onchange('academic_year')
    # def _onchange_lecturer(self):
    #      res = {}
    #      today = datetime.now()
    #      today_str = fields.Datetime.to_string(today)
    #      recs = self.env['osis.academic_year'].search([('start_date', '<=', today_str),
    #                                                   ('end_date', '>=', today_str)])
    #      if recs:
    #          for rec in recs:
    #              res['domain'] = {'academic_year_id': [('id', 'in', rec.id)]}
    #
    #      return res
