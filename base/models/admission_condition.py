from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from ordered_model.models import OrderedModel

from osis_common.models import osis_model_admin


class AdmissionCondition(models.Model):
    education_group_year = models.OneToOneField('base.EducationGroupYear', on_delete=models.CASCADE)

    # texte alert (2m et 2m1)
    text_alert_message = models.TextField(default='')

    # text libre pour 2eme partie
    text_free = models.TextField(default='')

    text_university_bachelors = models.TextField(default='')

    text_non_university_bachelors = models.TextField(default='')

    text_holders_second_university_degree = models.TextField(default='')
    text_holders_non_university_second_degree = models.TextField(default='')

    text_adults_taking_up_university_training = models.TextField(default='')
    text_personalized_access = models.TextField(default='')
    text_admission_enrollment_procedures = models.TextField(default='')

    text_ca_bacs_cond_generales = models.TextField(default='')
    text_ca_bacs_cond_particulieres = models.TextField(default='')
    text_ca_bacs_examen_langue = models.TextField(default='')
    text_ca_bacs_cond_speciales = models.TextField(default='')

    text_ca_cond_generales = models.TextField(default='')
    text_ca_maitrise_fr = models.TextField(default='')
    text_ca_allegement = models.TextField(default='')
    text_ca_ouv_adultes = models.TextField(default='')

    # English
    text_alert_message_en = models.TextField(default='')
    text_free_en = models.TextField(default='')

    text_university_bachelors_en = models.TextField(default='')

    text_non_university_bachelors_en = models.TextField(default='')

    text_holders_second_university_degree_en = models.TextField(default='')
    text_holders_non_university_second_degree_en = models.TextField(default='')

    text_adults_taking_up_university_training_en = models.TextField(default='')
    text_personalized_access_en = models.TextField(default='')
    text_admission_enrollment_procedures_en = models.TextField(default='')

    text_ca_bacs_cond_generales_en = models.TextField(default='')
    text_ca_bacs_cond_particulieres_en = models.TextField(default='')
    text_ca_bacs_examen_langue_en = models.TextField(default='')
    text_ca_bacs_cond_speciales_en = models.TextField(default='')

    text_ca_cond_generales_en = models.TextField(default='')
    text_ca_maitrise_fr_en = models.TextField(default='')
    text_ca_allegement_en = models.TextField(default='')
    text_ca_ouv_adultes_en = models.TextField(default='')

    def __str__(self):
        return "Admission condition - {}".format(self.education_group_year)


class AdmissionConditionAdmin(osis_model_admin.OsisModelAdmin):
    list_display = ('name',)

    def name(self, obj):
        return obj.education_group_year.acronym


CONDITION_ADMISSION_ACCESSES = [
    ('-', '-'),
    ('on_the_file', _('On the file: direct access or access with additional training')),
    ('direct_access', _('Direct Access')),
    ('access_with_training', _('Access with additional training')),
]


class AdmissionConditionLine(OrderedModel):
    admission_condition = models.ForeignKey(AdmissionCondition)

    section = models.CharField(max_length=32)
    # this external_id is used just for the import, once reddot is dead, we could remove it.
    external_id = models.CharField(max_length=32, null=True, db_index=True)

    access = models.CharField(choices=CONDITION_ADMISSION_ACCESSES, max_length=32,
                              default=CONDITION_ADMISSION_ACCESSES[0][0])

    diploma = models.TextField(default='')
    conditions = models.TextField(default='')
    remarks = models.TextField(default='')

    # English
    diploma_en = models.TextField(default='')
    conditions_en = models.TextField(default='')
    remarks_en = models.TextField(default='')

    order_with_respect_to = ('admission_condition', 'section')

    class Meta(OrderedModel.Meta):
        ordering = ('admission_condition', 'section', 'order')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.access not in dict(CONDITION_ADMISSION_ACCESSES):
            raise ValidationError({
                'access': _('%(access_value)s is not an accepted value') % {'access_value': self.access}
            })


class AdmissionConditionLineAdmin(osis_model_admin.OsisModelAdmin):
    list_display = ('name', 'section')

    def name(self, obj):
        return obj.admission_condition.education_group_year.acronym
