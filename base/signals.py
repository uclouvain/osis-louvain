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
from django.dispatch import Signal
from django.contrib.auth.models import Group

add_user_to_group = Signal(providing_args=["instance", "group", "kwargs"])
remove_user_from_group = Signal(providing_args=["instance", "group", "kwargs"])

def remove_user_from_group_handler(sender, instance, group, **kwargs):
    group_obj = Group.objects.get(name=group)
    instance.groups.remove(group_obj)

def add_to_tutors_group_handler(sender, instance, group, **kwargs):
    group_obj = Group.objects.get(name=group)
    instance.groups.add(group_obj)


# Signals definition
add_user_to_group.connect(add_to_tutors_group_handler)
remove_user_from_group.connect(remove_user_from_group_handler)
