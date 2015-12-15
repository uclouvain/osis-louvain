# -*- coding: utf-8 -*-

from openerp import models, fields, api, _


class Person(models.Model):
    _name = 'osis.person'
    _inherits = {'res.partner':'partner_id'}

    last_name = fields.Char(_('Last name'))
    first_name = fields.Char(_('First name'))
    middle_name = fields.Char('Middle name')
    global_id = fields.Char('Global ID')
    gender = fields.Selection([('F','Female'),('M','Male'),('U','Unknown')], default= 'U')
    national_number = fields.Char('National number')

    def build_fullname(self, values):

        nom = ''
        if values.get('last_name') is None:
            if self.last_name:
                nom = u"%s" % self.last_name
        else:
            nom = u"%s" % values.get('last_name')
        prenom = ''
        if values.get('last_name') is None:
            if self.first_name:
                prenom = u"%s" % self.first_name
        else:
            prenom = u"%s" % values.get('first_name')
        prenoms = ''
        if values.get('middle_name') is None:
            if self.middle_name:
                prenoms = u"%s" % self.middle_name
        else:
            prenoms = u"%s" % values.get('middle_name')

        name = u"%s %s %s" % (nom,prenom,prenoms)
        return name


    def _build_fullname2(self):

        nom = ''

        if self.last_name:
            nom = u"%s" % self.last_name

        prenom = ''

        if self.first_name:
            prenom = u"%s" % self.first_name

        prenoms = ''

        if self.middle_name:
            prenoms = u"%s" % self.middle_name


        name = u"%s %s %s" % (nom,prenom,prenoms)
        return name


    # @api.model
    # def create(self,values):
    #     values['name']=build_fullname(self,values)
    #     return super(Rental,self).create(values)
    #
    # @api.multi
    # def write(self, values):
    #     values['name']=build_fullname(self,values)
    #     return super(Person, self).write(values)

    @api.onchange('last_name','first_name','middle_name')
    def _build_name(self):
        nom = ''

        if self.last_name:
            nom = u"%s" % self.last_name

        prenom = ''

        if self.first_name:
            prenom = u"%s" % self.first_name

        prenoms = ''

        if self.middle_name:
            prenoms = u"%s" % self.middle_name


        name = u"%s %s %s" % (nom,prenom,prenoms)
        self.name = name
