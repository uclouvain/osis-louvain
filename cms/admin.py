from django.contrib import admin

from .models import text_label, translated_text, translated_text_label

# Register your models here.
admin.site.register(text_label.TextLabel,
                    text_label.TextLabelAdmin)

admin.site.register(translated_text.TranslatedText,
                    translated_text.TranslatedTextAdmin)

admin.site.register(translated_text_label.TranslatedTextLabel,
                    translated_text_label.TranslatedTextLabelAdmin)
