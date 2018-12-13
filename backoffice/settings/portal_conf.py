from collections.__init__ import namedtuple

from django.utils.translation import ugettext_lazy as _

# the parameter labels is a list of string and tuple
# labels=['welcome_introduction',
#         ('caap', 'specific,custom')]
# second parameter can have few values:
# specific
# common
# specific,common
# Used base.views.education_groups.detail.EducationGroupGeneralInformation#get_sections_with_translated_labels
Section = namedtuple('Section', 'title labels')

SECTION_LIST = [
    Section(title=_('Welcome'),
            labels=[
                ('welcome_introduction', 'specific'),
                ('welcome_profil', 'specific'),
                ('welcome_job', 'specific'),
                ('welcome_programme', 'specific'),
                ('welcome_parcours', 'specific'),
            ]),
    Section(title=_('Teaching profile'),
            labels=[
                ('structure', 'specific')
            ]),
    Section(title=_('Detailed programme'),
            labels=[
                ('mineures', 'specific'),
                ('majeures', 'specific'),
                ('programme_detaille', 'specific'),
                ('finalites', 'specific'),
                ('options', 'specific'),
                ('finalites_didactiques', 'common'),
                ('caap', 'specific,common'),
                ('agregation', 'common'),
                ('prerequis', 'common'),
            ]),
    Section(title=_('Admission'),
            labels=[
                ('acces_professions', 'specific'),
                ('bacheliers_concernes', 'specific'),
                ('module_complementaire', 'specific,common')
            ]),
    Section(title=_('Benefits and organization'),
            labels=[
                ('pedagogie', 'specific'),
                ('evaluation', 'specific,common'),
                ('mobilite', 'specific'),
                ('formations_accessibles', 'specific'),
                ('certificats', 'specific'),
                ('infos_pratiques', 'specific'),
            ]),
]
