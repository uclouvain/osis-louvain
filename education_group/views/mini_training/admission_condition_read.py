import functools

from education_group.views.mini_training.common_read import MiniTrainingRead, Tab
from education_group.views.serializers import admission_condition


class MiniTrainingReadAdmissionCondition(MiniTrainingRead):
    template_name = "mini_training/admission_condition_read.html"
    active_tab = Tab.ADMISSION_CONDITION

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "admission_requirements_label": self.get_admission_requirements_label(),
            "can_edit_information":
                self.request.user.has_perm("base.change_admissioncondition", self.get_education_group_version().offer),
            "mini_training": self.get_offer()
        }

    @functools.lru_cache()
    def get_offer(self):
        return self.get_education_group_version().offer

    def get_admission_requirements_label(self):
        return self.__get_admission_condition()['admission_requirements']

    @functools.lru_cache()
    def __get_admission_condition(self):
        offer = self.get_offer()
        return admission_condition.get_admission_condition(offer)
