from django.db import models

from osis_common.models import osis_model_admin


class AdmissionCondition(models.Model):
    education_group_year = models.OneToOneField('base.EducationGroupYear', on_delete=models.CASCADE)

    # texte pour les bacheliers (ba)
    text_bachelor = models.TextField(default='')

    # texte alert (2m et 2m1)
    text_alert_message = models.TextField(default='')

    # texte standard pour 2a et 2mc
    text_standard = models.TextField(default='')

    # text libre pour 2eme partie
    text_free = models.TextField(default='')

    text_university_bachelors = models.TextField(default='')

    text_non_university_bachelors = models.TextField(default='')

    text_holders_second_university_degree = models.TextField(default='')
    text_holders_non_university_second_degree = models.TextField(default='')

    text_adults_taking_up_university_training = models.TextField(default='')
    text_personalized_access = models.TextField(default='')
    text_admission_enrollment_procedures = models.TextField(default='')

    # English
    text_bachelor_en = models.TextField(default='')

    text_alert_message_en = models.TextField(default='')
    text_standard_en = models.TextField(default='')
    text_free_en = models.TextField(default='')

    text_university_bachelors_en = models.TextField(default='')

    text_non_university_bachelors_en = models.TextField(default='')

    text_holders_second_university_degree_en = models.TextField(default='')
    text_holders_non_university_second_degree_en = models.TextField(default='')

    text_adults_taking_up_university_training_en = models.TextField(default='')
    text_personalized_access_en = models.TextField(default='')
    text_admission_enrollment_procedures_en = models.TextField(default='')


class AdmissionConditionAdmin(osis_model_admin.OsisModelAdmin):
    list_display = ('name',)

    def name(self, obj):
        return obj.education_group_year.acronym


class AdmissionConditionLine(models.Model):
    admission_condition = models.ForeignKey(AdmissionCondition)

    section = models.CharField(max_length=32)
    # this external_id is used just for the import, once reddot is dead, we could remove it.
    external_id = models.CharField(max_length=32, null=True)

    diploma = models.TextField(default='')
    conditions = models.TextField(default='')
    access = models.TextField(default='')
    remarks = models.TextField(default='')

    # English
    diploma_en = models.TextField(default='')
    conditions_en = models.TextField(default='')
    access_en = models.TextField(default='')
    remarks_en = models.TextField(default='')
