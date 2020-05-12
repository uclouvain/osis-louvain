from education_group.auth.roles import faculty_manager, central_manager, central_admission_manager
from osis_role import role

role.role_manager.register(faculty_manager.FacultyManager)
role.role_manager.register(central_manager.CentralManager)
role.role_manager.register(central_admission_manager.CentralAdmissionManager)
