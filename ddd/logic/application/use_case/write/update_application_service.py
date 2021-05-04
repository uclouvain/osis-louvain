##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.db import transaction

from ddd.logic.application.commands import UpdateApplicationCommand
from ddd.logic.application.domain.model.application import ApplicationIdentity
from ddd.logic.application.repository.i_application_repository import IApplicationRepository


@transaction.atomic()
def update_application(
        cmd: UpdateApplicationCommand,
        application_repository: IApplicationRepository,
) -> ApplicationIdentity:
    # GIVEN
    application_identity = ApplicationIdentity(uuid=cmd.application_id)
    application = application_repository.get(entity_id=application_identity)

    # WHEN
    ## application.update()  (Via domain service ou via method dans model avec injection de commande...)

    # THEN
    application_repository.save(application)
    return application.entity_id

