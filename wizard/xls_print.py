from openerp import models, fields, api, exceptions, _
from datetime import datetime

class XlsPrint(models.TransientModel):
    _name = 'osis.xls_print'

    content = fields.Binary()
    file_name = fields.Char()
