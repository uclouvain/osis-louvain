from django.core.management import call_command
from django.db import migrations


def create_faculty_manager_rows(apps, shema_editor):
    """
    We will create a row to faculty managers for each user within faculty_managers_for_ue groups.
    The entity linked will be set from personentity
    """
    FacultyManager = apps.get_model('learning_unit', 'facultymanager')
    PersonEntity = apps.get_model('base', 'personentity')

    faculty_managers = PersonEntity.objects.filter(
        person__user__groups__name='faculty_managers_for_ue'
    )
    for faculty_manager in faculty_managers:
        FacultyManager.objects.create(
            person_id=faculty_manager.person_id,
            entity_id=faculty_manager.entity_id,
            with_child=faculty_manager.with_child,
        )

    # Resynchronize role managed with OSIS-Role with RBAC Django
    call_command('sync_perm_role', group='faculty_managers_for_ue')


def create_central_manager_rows(apps, shema_editor):
    """
    We will create a row to central managers for each user within central_managers_for_ue groups.
    The entity linked will be set from personentity
    """
    CentralManager = apps.get_model('learning_unit', 'centralmanager')
    PersonEntity = apps.get_model('base', 'personentity')

    central_managers = PersonEntity.objects.filter(
        person__user__groups__name='central_managers_for_ue'
    )
    for central_manager in central_managers:
        CentralManager.objects.create(
            person_id=central_manager.person_id,
            entity_id=central_manager.entity_id,
            with_child=central_manager.with_child,
        )

    # Resynchronize role managed with OSIS-Role with RBAC Django
    call_command('sync_perm_role', group='central_managers_for_ue')


class Migration(migrations.Migration):

    dependencies = [
        ('learning_unit', '0004_auto_20200618_1435'),
    ]

    operations = [
        migrations.RunPython(create_faculty_manager_rows, migrations.RunPython.noop),
        migrations.RunPython(create_central_manager_rows, migrations.RunPython.noop),
    ]
