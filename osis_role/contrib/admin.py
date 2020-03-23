from osis_common.models.osis_model_admin import OsisModelAdmin


class RoleModelAdmin(OsisModelAdmin):
    list_display = ('person',)
    search_fields = [
        'person__first_name',
        'person__last_name',
    ]


class EntityRoleModelAdmin(OsisModelAdmin):
    list_display = ('person', 'entity', 'latest_entity_version_name', 'with_child')
    search_fields = [
        'person__first_name',
        'person__last_name',
        'entity__entityversion__acronym'
    ]

    def latest_entity_version_name(self, obj):
        from base.models import entity_version
        entity_v = entity_version.get_last_version(obj.entity)
        if entity_v:
            entity_v_str = "{}".format(entity_v.acronym)
        else:
            entity_v_str = "Not found"
        return entity_v_str
    latest_entity_version_name.short_description = 'Latest entity version'
