from django.contrib import admin

from learning_unit.auth.roles import central_manager, faculty_manager
from learning_unit.models import *

admin.site.register(learning_class_year.LearningClassYear,
                    learning_class_year.LearningClassYearAdmin)

admin.site.register(central_manager.CentralManager,
                    central_manager.CentralManagerAdmin)

admin.site.register(faculty_manager.FacultyManager,
                    faculty_manager.FacultyManagerAdmin)
