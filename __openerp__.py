# -*- coding: utf-8 -*-
{
    'name': "osis_louvain",

    'summary': """
        Extension of the module OSIS to accommodate specific needs of UCLouvain.
    """,

    'description': """
        OSIS Louvain is an extension of OSIS customized for the needs of the Université catholique de Louvain.
    """,

    'author': "Université catholique de Louvain",
    'website': "http://www.uclouvain.be",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Education',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','osis_core'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'templates.xml',
        'views/menu.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}
