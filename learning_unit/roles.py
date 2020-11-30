from learning_unit.auth.roles import central_manager, faculty_manager
from osis_role import role

role.role_manager.register(central_manager.CentralManager)
role.role_manager.register(faculty_manager.FacultyManager)
