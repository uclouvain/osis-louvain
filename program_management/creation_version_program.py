
# Créer Version programme spécifique
# - sur base version standard existante
# - intitulé fr, entitulé EN, nom_version, date de fin
# - nom_version entré ne peut pas exister dans le futur et sur l'année en cours
# - générer sigle non existant (code - partial_acronym)
# - Lorsqu'on crée from scratch, le contenu de la version doit créer des groupements par défaut en-dessous de la version
#     - Création du squelette

# --------------------------------------
# - Si la version entrée existe dans le passé, on peut prolonger le programme existant dans le passé:
#     - Recopier le contenu sur les années suivantes
from typing import List

from base.ddd.utils.business_validator import BusinessValidator
from program_management.ddd.domain.program_tree_version import ProgramTreeVersion


def create_program_version(
        acronym_offer: str,
        year_offer: int,
        title_fr: str,
        title_en: str,
        nom_version: str,
        date_de_fin: int
) -> ProgramTreeVersion:
    """Devrait créer une version de programme, sur base des paramètres entrés"""
    # Couche service
    tree_version = init_program_tree_version()
    persist_specific_version_program(tree_version)


def init_program_tree_version(
        acronym_offer: str,
        year_offer: int,
        title_fr: str,
        title_en: str,
        nom_version: str,
        date_de_fin: int
) -> ProgramTreeVersion:
    """Instancie un ProgramTreeVersion"""
    # builder = ProgramTreeVersionBuilder()
    # program_tree_version = builder.build_from(param1, param2)
    # return program_tree_version
    return ProgramTreeVersion(
        program_tree=ProgramTree(
            root_node=Node(
                champs1=None,
            )
        ),
        title_fr=title_fr,
        title_en=title_en,
    )


def persist_specific_version_program(program_tree: ProgramTreeVersion) -> None:
    """Persister en DB le programme passé en paramètre."""
    # Couche repo
    pass


class VersionNameExistsValidator(BusinessValidator):

    # Couche validators
    def __init__(self, working_year: int, version_name: str, is_transition: bool):
        super(VersionNameExistsValidator, self).__init__()
        self.working_year = working_year
        self.version_name = version_name
        self.is_transition = is_transition

    def validate(self, *args, **kwargs):
        if check_version_name_exists(self.working_year, self.version_name, self.is_transition):
            self.add_error_message("Acronym {} already exists".format(self.version_name))


def check_version_name_exists(working_year: int, version_name: str, is_transition: bool) -> bool:
    """Vérifier en DB si le nom de version entré en paramètre existe déjà sur l'année en cours ou futures."""
    # Couche repository
    pass


def generate_node_code(code_from_standard_root_node: str) -> str:
    """Incrémenter la parie numérique du code de la version standard jusqu'à ce que le nouveau code n'existe pas."""
    # Incrémenter la partir numérique
    # Couche service
    code = ""
    check_node_code_exists(code)
    return ""


def check_node_code_exists(code: str) -> bool:
    """Accès DB pour vérifier l'existance du code"""
    # Couche repository
    pass
