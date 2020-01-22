# Register your models here.
from django.contrib import admin

from .models import element

# Register your models here.
admin.site.register(element.Element,
                    element.ElementAdmin)
