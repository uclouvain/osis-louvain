from django.urls import include, path

from education_group.views import group, training, mini_training, general_information
from education_group.views.proxy.read import ReadEducationGroupRedirectView

urlpatterns = [
    path(
        '<int:year>/<str:acronym>/',
        ReadEducationGroupRedirectView.as_view(),
        name='education_group_read_proxy'
    ),
    path('groups/<int:year>/<str:code>/', include([
        path('identification/', group.GroupReadIdentification.as_view(), name='group_identification'),
        path('content/', group.GroupReadContent.as_view(), name='group_content'),
        path('utilization/', group.GroupReadUtilization.as_view(), name='group_utilization'),
        path('general_information/', group.GroupReadGeneralInformation.as_view(), name='group_general_information'),
    ])),

    path('mini_trainings/<int:year>/<str:code>/', include([
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
    path('trainings/<int:year>/<str:code>/', include([
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
    path('<int:year>/<str:code>/publish', general_information.publish, name='publish_general_information')
]
