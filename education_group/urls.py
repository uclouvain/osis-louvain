from django.urls import include, path, register_converter, re_path

from base.views.education_groups.achievement.create import CreateEducationGroupDetailedAchievement, \
    CreateEducationGroupAchievement
from base.views.education_groups.achievement.delete import DeleteEducationGroupAchievement, \
    DeleteEducationGroupDetailedAchievement
from base.views.education_groups.achievement.update import EducationGroupAchievementAction, \
    UpdateEducationGroupAchievement, EducationGroupDetailedAchievementAction, UpdateEducationGroupDetailedAchievement
from education_group.converters import GroupTypeConverter, TrainingTypeConverter, MiniTrainingTypeConverter
from education_group.views import group, training, mini_training, general_information
from education_group.views.mini_training.delete import MiniTrainingDeleteView
from education_group.views.proxy.read import ReadEducationGroupRedirectView
from education_group.views.training.delete import TrainingDeleteView

register_converter(GroupTypeConverter, 'group_type')
register_converter(MiniTrainingTypeConverter, 'mini_training_type')
register_converter(TrainingTypeConverter, 'training_type')

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
        path('<int:year>/<str:code>/', include([
            path('create/', CreateEducationGroupAchievement.as_view(), name='training_achievement_create'),
            path('delete/', TrainingDeleteView.as_view(), name='training_delete'),
            path('<int:education_group_achievement_pk>/', include([
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
        path('common/', general_information.CommonGeneralInformation.as_view(), name="common_general_information"),
        path(
            'common-bachelor/',
            general_information.CommonBachelorAdmissionCondition.as_view(),
            name="common_bachelor_admission_condition"
        ),
        path(
            'common-aggregate/',
            general_information.CommonAggregateAdmissionCondition.as_view(),
            name="common_aggregate_admission_condition"
        ),
        path(
            'common-master/',
            general_information.CommonMasterAdmissionCondition.as_view(),
            name="common_master_admission_condition"
        ),
        path(
            'common-master-specialized/',
            general_information.CommonMasterSpecializedAdmissionCondition.as_view(),
            name="common_master_specialized_admission_condition"
        ),
    ])),
    path('<int:year>/<str:code>/publish', general_information.publish, name='publish_general_information'),
    re_path(
        r'^(?P<year>[\d]{4})/(?P<acronym>[\w]+(?:[/ ]?[a-zA-Z]{1,2}){0,2})/$',
        ReadEducationGroupRedirectView.as_view(),
        name='education_group_read_proxy'
    ),
]
