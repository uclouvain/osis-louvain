from __future__ import unicode_literals

from django.db import migrations


def update_justifications_forwards(apps,shema_editor):
    ExamEnrollment = apps.get_model('base', 'examenrollment')

    ExamEnrollment.objects.filter(justification_draft='ABSENT').update(justification_draft='ABSENCE_UNJUSTIFIED')
    ExamEnrollment.objects.filter(justification_draft='ILL').update(justification_draft='ABSENCE_JUSTIFIED')
    ExamEnrollment.objects.filter(justification_draft='JUSTIFIED_ABSENCE')\
        .update(justification_draft='ABSENCE_JUSTIFIED')

    ExamEnrollment.objects.filter(justification_final='ABSENT').update(justification_final='ABSENCE_UNJUSTIFIED')
    ExamEnrollment.objects.filter(justification_final='ILL').update(justification_final='ABSENCE_JUSTIFIED')
    ExamEnrollment.objects.filter(justification_final='JUSTIFIED_ABSENCE')\
        .update(justification_final='ABSENCE_JUSTIFIED')

    ExamEnrollment.objects.filter(justification_reencoded='ABSENT').update(justification_reencoded='ABSENCE_UNJUSTIFIED')
    ExamEnrollment.objects.filter(justification_reencoded='ILL').update(justification_reencoded='ABSENCE_JUSTIFIED')
    ExamEnrollment.objects.filter(justification_reencoded='JUSTIFIED_ABSENCE')\
        .update(justification_reencoded='ABSENCE_JUSTIFIED')

    ExamEnrollmentHystory = apps.get_model('base', 'examenrollmenthistory')

    ExamEnrollmentHystory.objects.filter(justification_final='ABSENT').update(justification_final='ABSENCE_UNJUSTIFIED')
    ExamEnrollmentHystory.objects.filter(justification_final='ILL').update(justification_final='ABSENCE_JUSTIFIED')
    ExamEnrollmentHystory.objects.filter(justification_final='JUSTIFIED_ABSENCE') \
        .update(justification_final='ABSENCE_JUSTIFIED')


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0044_auto_20160511_2247'),
    ]

    operations = [
        migrations.RunPython(update_justifications_forwards),
    ]

