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
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from dissertation.models import *
from django.contrib import admin

admin.site.register(adviser.Adviser, adviser.AdviserAdmin)
admin.site.register(dissertation.Dissertation, dissertation.DissertationAdmin)
admin.site.register(dissertation_document_file.DissertationDocumentFile,
                    dissertation_document_file.DissertationDocumentFileAdmin)
admin.site.register(dissertation_group.DissertationGroup, dissertation_group.DissertationGroupAdmin)
admin.site.register(dissertation_location.DissertationLocation, dissertation_location.DissertationLocationAdmin)
admin.site.register(dissertation_role.DissertationRole, dissertation_role.DissertationRoleAdmin)
admin.site.register(dissertation_update.DissertationUpdate, dissertation_update.DissertationUpdateAdmin)
admin.site.register(faculty_adviser.FacultyAdviser, faculty_adviser.FacultyAdviserAdmin)
admin.site.register(offer_proposition.OfferProposition, offer_proposition.OfferPropositionAdmin)
admin.site.register(proposition_dissertation.PropositionDissertation,
                    proposition_dissertation.PropositionDissertationAdmin)
admin.site.register(proposition_document_file.PropositionDocumentFile,
                    proposition_document_file.PropositionDocumentFileAdmin)
admin.site.register(proposition_offer.PropositionOffer, proposition_offer.PropositionOfferAdmin)
admin.site.register(proposition_role.PropositionRole, proposition_role.PropositionRoleAdmin)
