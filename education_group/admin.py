# Register your models here.
from django.contrib import admin
from osis_role.contrib import admin as osis_role_admin

from .auth.roles import faculty_manager, central_manager, central_admission_manager
from .models import group, group_year

# Register your models here.
admin.site.register(group.Group,
                    group.GroupAdmin)

admin.site.register(group_year.GroupYear,
                    group_year.GroupYearAdmin)

admin.site.register(faculty_manager.FacultyManager, faculty_manager.FacultyManagerAdmin)
admin.site.register(central_manager.CentralManager, central_manager.CentralManagerAdmin)
admin.site.register(central_admission_manager.CentralAdmissionManager, osis_role_admin.RoleModelAdmin)
