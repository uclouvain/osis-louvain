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
from django.contrib.auth.decorators import user_passes_test
from assistant.forms import SettingsForm
from base.views import layout
from assistant.models import settings
from base.models import academic_year
from assistant.utils import manager_access


@user_passes_test(manager_access.user_is_manager, login_url='assistants_home')
def settings_edit(request):
    """Use to edit app settings."""
    global_settings = settings.get_settings()
    if global_settings:
        form = SettingsForm(initial={'starting_date': global_settings.starting_date,
                                     'ending_date': global_settings.ending_date,
                                     'assistants_starting_date': global_settings.assistants_starting_date,
                                     'assistants_ending_date': global_settings.assistants_ending_date
                                     }, prefix="set", instance=global_settings)
    else:
        form = SettingsForm(prefix="set", instance=global_settings)
    year = academic_year.current_academic_year().year
    return layout.render(request, 'settings.html', {'year': year,
                                                    'form': form,
                                                    })


@user_passes_test(manager_access.user_is_manager, login_url='assistants_home')
def settings_save(request):
    global_settings = settings.get_settings()
    form = SettingsForm(data=request.POST, instance=global_settings, prefix='set')
    if form.is_valid():
        form.save()
        return settings_edit(request)
    else:
        year = academic_year.current_academic_year().year
        return layout.render(request, 'settings.html', {'year': year,
                                                        'form': form})
