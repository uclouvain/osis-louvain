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

from openerp import http

class OsisLouvain(http.Controller):
    @http.route('/osis-louvain/osis-louvain/', auth='public')
    def index(self, **kw):
        Student_notes  = http.request.env['osis.student_notes']
        return http.request.render('osis-louvain.student_notes_listing', {
            'student_notes': Student_notes.search([]),
        })
        # Offers  = http.request.env['osis.offer']
        # return http.request.render('osis-louvain.offer', {
        #     'offers': Offers.search([]),
        # })
    # @http.route('/osis-louvain/osis-louvain/objects/', auth='public')
    # def list(self, **kw):
    #     return http.request.render('osis-louvain.listing', {
    #         'root': '/osis-louvain/osis-louvain',
    #         'objects': http.request.env['osis-louvain.osis-louvain'].search([]),
    #     })

#     @http.route('/osis-louvain/osis-louvain/objects/<model("osis-louvain.osis-louvain"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('osis-louvain.object', {
#             'object': obj
#         })
