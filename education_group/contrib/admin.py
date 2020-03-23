from osis_common.models.osis_model_admin import OsisModelAdmin


class EducationGroupRoleModelAdmin(OsisModelAdmin):
    list_display = ('person', 'education_group',)
    search_fields = [
        'person__first_name',
        'person__last_name',
        'person__global_id',
        'education_group__educationgroupyear__acronym',
    ]


class EducationGroupYearRoleModelAdmin(OsisModelAdmin):
    list_display = ('person', 'education_group_year',)
    search_fields = [
        'person__first_name',
        'person__last_name',
        'person__global_id',
        'educationgroupyear__acronym',
    ]
