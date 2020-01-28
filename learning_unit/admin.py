from django.contrib import admin

from learning_unit.models import *

admin.site.register(learning_class_year.LearningClassYear,
                    learning_class_year.LearningClassYearAdmin)
