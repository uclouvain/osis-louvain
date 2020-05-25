import functools

from education_group.views.serializers import admission_condition
from education_group.views.training.common_read import TrainingRead, Tab


class TrainingReadAdmissionCondition(TrainingRead):
    template_name = "training/admission_condition_read.html"
    active_tab = Tab.ADMISSION_CONDITION

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "conditions": self.get_admission_condition(),
            "can_edit_information":
                self.request.user.has_perm("base.change_admissioncondition", self.get_education_group_version().offer),
            "training": self.get_offer(),
        }

    @functools.lru_cache()
    def get_offer(self):
        return self.get_education_group_version().offer

    def get_admission_condition(self):
        return self.__get_admission_condition()

    @functools.lru_cache()
    def __get_admission_condition(self):
        offer = self.get_offer()
        return admission_condition.get_admission_condition(offer)
