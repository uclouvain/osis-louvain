from osis_role import role

from learning_unit.auth.roles import central_manager, faculty_manager, student_worker

role.role_manager.register(central_manager.CentralManager)
role.role_manager.register(faculty_manager.FacultyManager)
role.role_manager.register(student_worker.StudentWorker)
