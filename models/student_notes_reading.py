# -*- coding: utf-8 -*-
from openerp import models, fields, api, tools, _

class Student_notes_reading(models.Model):
    _name = 'osis.student_notes'
    _description = 'Student notes'
    _auto = False
    _order = 'acronym'

    acronym = fields.Char('Acronym', readonly=True)
    title = fields.Char('Title', readonly=True)
    year = fields.Integer('Year', readonly=True)
    status = fields.Boolean('Statusss', readonly=True)
    session_name = fields.Char('Session name', readonly=True)
    session_exam_id = fields.Char('Exam id', readonly=True)
    learning_unit_year_id = fields.Integer('Learning Unit Year Id', readonly=True)
    learning_unit_id = fields.Integer('Learning Unit Id', readonly=True)
    # tutor_name = fields.Char('Tutor name', compute='_get_tutors_names' , search='_search_tutor_name')
    tutor_name = fields.Char('Tutor name', compute='_get_tutors_names')

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


    # @api.model
    # def default_get(self, fields_list):
    #     print 'zut',default_get
    #     # trigger view init hook
    #     self.view_init(fields_list)
    #
    #     defaults = {}
    #     parent_fields = defaultdict(list)
    #
    #     for name in fields_list:
    #         print 'zut', name
    #         # 1. look up context
    #         key = 'default_' + name
    #         if key in self._context:
    #             defaults[name] = self._context[key]
    #             continue
    #
    #         # 2. look up ir_values
    #         #    Note: performance is good, because get_defaults_dict is cached!
    #         ir_values_dict = self.env['ir.values'].get_defaults_dict(self._name)
    #         if name in ir_values_dict:
    #             defaults[name] = ir_values_dict[name]
    #             continue
    #
    #         field = self._fields.get(name)
    #
    #         # 3. look up property fields
    #         #    TODO: get rid of this one
    #         if field and field.company_dependent:
    #             defaults[name] = self.env['ir.property'].get(name, self._name)
    #             continue
    #
    #         # 4. look up field.default
    #         if field and field.default:
    #             defaults[name] = field.default(self)
    #             continue
    #
    #         # 5. delegate to parent model
    #         if field and field.inherited:
    #             field = field.related_field
    #             parent_fields[field.model_name].append(field.name)

    #
    def fields_view_get(self, cr, uid, view_id=None, view_type=None, context=None, toolbar=False, submenu=False):

        res = super(Student_notes_reading,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        # print res
        if context is None:
            context = {}
        # print 'zut res' ,res


        # if view_type == 'tree':
        #     print res
        #     for field in res['fields']:
        #         print 'zut field :',field
        #         if field == 'acronym' :
        #             print res['fields'][field]
        #     doc = etree.XML(res['arch'])
        #     print 'zut'  , etree
        #     for node in doc.xpath("//field[@name='acronym']"):
        #         print 'zut node' , node
        #         node.set('invisible', '0')
        #     res['arch'] = etree.tostring(doc)

        return res
