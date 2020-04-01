# Register your models here.
from django.contrib import admin

from .models import element, education_group_version

# Register your models here.
admin.site.register(element.Element,
                    element.ElementAdmin)
admin.site.register(education_group_version.EducationGroupVersion,
                    education_group_version.EducationGroupVersionAdmin)
