from django.urls import include, path, register_converter

from base.views.education_groups.achievement.create import CreateEducationGroupDetailedAchievement, \
    CreateEducationGroupAchievement
from base.views.education_groups.achievement.delete import DeleteEducationGroupAchievement, \
    DeleteEducationGroupDetailedAchievement
from base.views.education_groups.achievement.update import EducationGroupAchievementAction, \
    UpdateEducationGroupAchievement, EducationGroupDetailedAchievementAction, UpdateEducationGroupDetailedAchievement
from education_group.converters import GroupTypeConverter, TrainingTypeConverter, MiniTrainingTypeConverter, \
    AcronymConverter
from education_group.views import group, training, mini_training, general_information
from education_group.views.autocomplete import EducationGroupTypeAutoComplete, CertificateAimAutocomplete
from education_group.views.configuration.common_list import CommonListView
from education_group.views.configuration.home import ConfigurationHomeView
from education_group.views.mini_training.delete import MiniTrainingDeleteView
from education_group.views.proxy.read import ReadEducationGroupRedirectView
from education_group.views.training.delete import TrainingDeleteView
from education_group.views.training.update import TrainingUpdateView

register_converter(GroupTypeConverter, 'group_type')
register_converter(MiniTrainingTypeConverter, 'mini_training_type')
register_converter(TrainingTypeConverter, 'training_type')
register_converter(AcronymConverter, 'acronym')

urlpatterns = [
    path('groups/', include([
        path('<group_type:type>/create', group.GroupCreateView.as_view(), name='group_create'),
        path('<int:year>/<str:code>/', include([
            path('update/', group.GroupUpdateView.as_view(), name='group_update'),
            path('identification/', group.GroupReadIdentification.as_view(), name='group_identification'),
            path('content/', group.GroupReadContent.as_view(), name='group_content'),
            path('utilization/', group.GroupReadUtilization.as_view(), name='group_utilization'),
            path('general_information/', include([
                path('read/', group.GroupReadGeneralInformation.as_view(), name='group_general_information'),
                path('update/', group.GroupUpdateGeneralInformation.as_view(), name='group_general_information_update'),
            ])),
            path('delete/', group.GroupDeleteView.as_view(), name='group_delete')
        ]))
    ])),
    path('mini_trainings/', include([
        path('<mini_training_type:type>/create', mini_training.MiniTrainingCreateView.as_view(),
             name='mini_training_create'),
        path('<int:year>/<str:code>/', include([
            path(
                'identification/',
                mini_training.MiniTrainingReadIdentification.as_view(),
                name='mini_training_identification'
            ),
            path('<acronym:acronym>/update/', mini_training.MiniTrainingUpdateView.as_view(),
                 name='mini_training_update'),
            path('content/', mini_training.MiniTrainingReadContent.as_view(), name='mini_training_content'),
            path('utilization/', mini_training.MiniTrainingReadUtilization.as_view(), name='mini_training_utilization'),
            path(
                'general_information/',
                mini_training.MiniTrainingReadGeneralInformation.as_view(),
                name='mini_training_general_information'
            ),
            path(
                'skills_achievements/',
                mini_training.MiniTrainingReadSkillsAchievements.as_view(),
                name='mini_training_skills_achievements'
            ),
            path(
                'admission_conditions/',
                mini_training.MiniTrainingReadAdmissionCondition.as_view(),
                name='mini_training_admission_condition'
            ),
        ])),
    ])),
    path('mini_trainings/<int:year>/<str:code>/', include([
        path('create/', CreateEducationGroupAchievement.as_view(), name='minitraining_achievement_create'),
        path('delete/', MiniTrainingDeleteView.as_view(), name='mini_training_delete'),
        path('<int:education_group_achievement_pk>/', include([
            path('actions/', EducationGroupAchievementAction.as_view(), name='minitraining_achievement_actions'),
            path('create/', CreateEducationGroupDetailedAchievement.as_view(),
                 name='minitraining_detailed_achievement_create'),
            path('delete/', DeleteEducationGroupAchievement.as_view(), name='minitraining_achievement_delete'),
            path('update/', UpdateEducationGroupAchievement.as_view(), name='minitraining_achievement_update'),
            path('<int:education_group_detail_achievement_pk>/', include([
                path('actions/', EducationGroupDetailedAchievementAction.as_view(),
                     name='minitraining_detailed_achievement_actions'),
                path('delete/', DeleteEducationGroupDetailedAchievement.as_view(),
                     name='minitraining_detailed_achievement_delete'),
                path('update/', UpdateEducationGroupDetailedAchievement.as_view(),
                     name='minitraining_detailed_achievement_update'),
            ]))
        ])),
        path(
            'identification/',
            mini_training.MiniTrainingReadIdentification.as_view(),
            name='mini_training_identification'
        ),
        path('content/', mini_training.MiniTrainingReadContent.as_view(), name='mini_training_content'),
        path('utilization/', mini_training.MiniTrainingReadUtilization.as_view(), name='mini_training_utilization'),
        path(
            'general_information/',
            mini_training.MiniTrainingReadGeneralInformation.as_view(),
            name='mini_training_general_information'
        ),
        path(
            'skills_achievements/',
            mini_training.MiniTrainingReadSkillsAchievements.as_view(),
            name='mini_training_skills_achievements'
        ),
        path(
            'admission_conditions/',
            mini_training.MiniTrainingReadAdmissionCondition.as_view(),
            name='mini_training_admission_condition'
        ),
    ])),
    path('trainings/', include([
        path('<training_type:type>/create/', training.TrainingCreateView.as_view(), name='training_create'),
        path('<int:year>/<str:code>/', include([  # FIXME use acronym
            path('<acronym:title>/update/', TrainingUpdateView.as_view(), name='training_update'),
            path('create/', CreateEducationGroupAchievement.as_view(), name='training_achievement_create'),
            path('delete/', TrainingDeleteView.as_view(), name='training_delete'),
            path('achievement/<int:education_group_achievement_pk>/', include([
                path('actions/', EducationGroupAchievementAction.as_view(), name='training_achievement_actions'),
                path('create/', CreateEducationGroupDetailedAchievement.as_view(),
                     name='training_detailed_achievement_create'),
                path('delete/', DeleteEducationGroupAchievement.as_view(), name='training_achievement_delete'),
                path('update/', UpdateEducationGroupAchievement.as_view(), name='training_achievement_update'),
                path('<int:education_group_detail_achievement_pk>/', include([
                    path('actions/', EducationGroupDetailedAchievementAction.as_view(),
                         name='training_detailed_achievement_actions'),
                    path('delete/', DeleteEducationGroupDetailedAchievement.as_view(),
                         name='training_detailed_achievement_delete'),
                    path('update/', UpdateEducationGroupDetailedAchievement.as_view(),
                         name='training_detailed_achievement_update'),
                ]))
            ])),
            path('identification/', training.TrainingReadIdentification.as_view(), name='training_identification'),
            path('diplomas/', training.TrainingReadDiplomaCertificate.as_view(), name='training_diplomas'),
            path(
                'administrative_data/',
                training.TrainingReadAdministrativeData.as_view(),
                name='training_administrative_data'
            ),
            path('content/', training.TrainingReadContent.as_view(), name='training_content'),
            path('utilization/', training.TrainingReadUtilization.as_view(), name='training_utilization'),
            path(
                'general_information/',
                training.TrainingReadGeneralInformation.as_view(),
                name='training_general_information'
            ),
            path(
                'skills_achievements/',
                training.TrainingReadSkillsAchievements.as_view(),
                name='training_skills_achievements'
            ),
            path(
                'admission_conditions/',
                training.TrainingReadAdmissionCondition.as_view(),
                name='training_admission_condition'
            ),
        ])),
    ])),
    path('general_information/<int:year>/', include([
        path('common/', include([
            path('', general_information.CommonGeneralInformation.as_view(), name="common_general_information"),
            path(
                'update',
                general_information.UpdateCommonGeneralInformation.as_view(),
                name="update_common_general_information"
            ),
            path('publish', general_information.publish_common_pedagogy, name="publish_common_general_information"),
        ])),
        path('common-bachelor/', include([
            path(
                '',
                general_information.CommonBachelorAdmissionCondition.as_view(),
                name="common_bachelor_admission_condition"
            ),
            path(
                'update',
                general_information.UpdateCommonBachelorAdmissionCondition.as_view(),
                name="update_common_bachelor_admission_condition"
            ),
            path(
                'publish',
                general_information.publish_common_admission_conditions,
                {'redirect_view': 'common_bachelor_admission_condition'},
                name="publish_common_bachelor_admission_condition"
            ),
        ])),
        path('common-aggregate/', include([
            path(
                '',
                general_information.CommonAggregateAdmissionCondition.as_view(),
                name="common_aggregate_admission_condition"
            ),
            path(
                'update',
                general_information.UpdateCommonAggregateAdmissionCondition.as_view(),
                name="update_common_aggregate_admission_condition"
            ),
            path(
                'publish',
                general_information.publish_common_admission_conditions,
                {'redirect_view': 'common_aggregate_admission_condition'},
                name="publish_common_aggregate_admission_condition"
            ),
        ])),
        path('common-master/', include([
            path(
                '',
                general_information.CommonMasterAdmissionCondition.as_view(),
                name="common_master_admission_condition"
            ),
            path(
                'update',
                general_information.UpdateCommonMasterAdmissionCondition.as_view(),
                name="update_common_master_admission_condition"
            ),
            path(
                'publish',
                general_information.publish_common_admission_conditions,
                {'redirect_view': 'common_master_admission_condition'},
                name="publish_common_master_admission_condition"
            ),
        ])),
        path('common-master-specialized/', include([
            path(
                '',
                general_information.CommonMasterSpecializedAdmissionCondition.as_view(),
                name="common_master_specialized_admission_condition"
            ),
            path(
                'update',
                general_information.UpdateCommonMasterSpecializedAdmissionCondition.as_view(),
                name="update_common_master_specialized_admission_condition"
            ),
            path(
                'publish',
                general_information.publish_common_admission_conditions,
                {'redirect_view': 'common_master_specialized_admission_condition'},
                name="publish_common_master_specialized_admission_condition"
            ),
        ])),
    ])),
    path('<int:year>/<acronym:acronym>/', ReadEducationGroupRedirectView.as_view(), name='education_group_read_proxy'),
    path('configuration/', include([
        path('home/', ConfigurationHomeView.as_view(), name='catalog_configuration'),
        path('common-topics/', CommonListView.as_view(), name='common_topics_configuration'),
    ])),
    path('autocomplete/', include([
        path(
            'education-group-types/',
            EducationGroupTypeAutoComplete.as_view(),
            name='education_group_type_autocomplete'
        ),
        path('certificate-aims/', CertificateAimAutocomplete.as_view(), name='certificate_aim_autocomplete'),
    ])),
]
