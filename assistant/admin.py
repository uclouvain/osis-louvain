##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib import admin
from assistant.models import reviewer, manager, settings, academic_assistant, assistant_mandate
from assistant.models.assistant_document_file import AssistantDocumentFile
from assistant.models.mandate_structure import MandateStructure
from assistant.models.review import Review
from assistant.models.tutoring_learning_unit_year import TutoringLearningUnitYear


admin.site.register(assistant_mandate.AssistantMandate, assistant_mandate.AssistantMandateAdmin)
admin.site.register(AssistantDocumentFile)
admin.site.register(academic_assistant.AcademicAssistant, academic_assistant.AcademicAssistantAdmin)
admin.site.register(MandateStructure)
admin.site.register(Review)
admin.site.register(TutoringLearningUnitYear)
admin.site.register(reviewer.Reviewer, reviewer.ReviewerAdmin)
admin.site.register(manager.Manager, manager.ManagerAdmin)
admin.site.register(settings.Settings, settings.SettingsAdmin)
