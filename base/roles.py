from base.auth.roles import entity_manager
from osis_role import role

role.role_manager.register(entity_manager.EntityManager)
