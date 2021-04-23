# DTO : Data Transfer Object

### Cas d'utilisation

- En tant qu'utilisateur, je veux rechercher toutes les formations et versions de formations sur base d'un formulaire de recherche :
    - année académique
    - Sigle (intitulé abrégé) (toutes versions confondues)
    - code
    - intitulé
    - type
    - entité
- Dans la vue "liste", je veux afficher 
    - année académique
    - Sigle (intitulé abrégé)
    - intitulé
    - type
    - entité de charge
        - acronym
        - intitulé (en helptext)
    
```python
# Application service
def search_program_trees_versions_service(cmd: interface.CommandRequest) -> List['ProgramTreeVersion']:
    return ProgramTreeVersionRepository().search(**cmd)
```

<br/><br/><br/><br/>

Constats : 
- Recherche lente (performance)
    - Renvoie ProgramTreeVersion objet complet du domaine avec toutes entities imbriquées (ProgramTree, etc)
- Charge beaucoup de données inutiles
    - Peu de champs de l'objet du domaine sont utiles




<br/><br/><br/><br/><br/><br/><br/><br/>



### Solution


```python

# ddd/dtos.py
class SearchProgramTreeVersionDTO(interface.DTO):
    academic_year = attr.ib(type=int)
    acronym_abbreviated_title = attr.ib(type=str)
    title = attr.ib(type=str)
    type = attr.ib(type=str)
    entity_acronym = attr.ib(type=str)
    entity_title = attr.ib(type=str)
    code = attr.ib(type=str)

#--------------------------------------------------------------------------------------------------------
# ddd/repository/program_tree_version.py

class ProgramTreeVersionRepository(interface.AbstractRepository):

    def search(self, **searchparams) -> List[SearchProgramTreeVersionDTO]:
        # To implement
        return []

    def search_program_trees_versions(self, **searchparams) -> List[ProgramTreeVersion]:
        # To implement
        return []

```

Avantages :
- Découplage de la DB (et des querysets)
    - Contrat de données attendues pour la recherche d'une liste de versions de programmes
- Performances


Inconvénients :
- Mapping supplémentaire entre notre DB et un objet "de vue" (notre DTO)
    - Maintenance supplémentaire


```python

class ProgramTreeVersionRepository(interface.AbstractRepository):

    def search(self, **searchparams) -> List[SearchProgramTreeVersionDTO]:
        # To implement
        return []

    def search_program_trees_versions(self, **searchparams) -> List[ProgramTreeVersion]:
        # To implement
        return []

    def search_for_trainings_only(self, **searchparams) -> List[SearchForTrainingsOnlyDTO]:
        """
        Uniquement si les données affichées dans la vue liste sont différentes de SearchProgramTreeVersionDTO.
        Sinon, on réutilise search().
        """
        # To implement
        return []

    def search_for_transitions_only(self, **searchparams) -> List[SearchForTransitionsOnlyDTO]:
        """
        Uniquement si les données affichées dans la vue liste sont différentes de SearchProgramTreeVersionDTO.
        Sinon, on réutilise search().
        """
        # To implement
        return []

```


<br/><br/><br/><br/><br/><br/><br/><br/>



## Quand utiliser un DTO ?

- Dans le `Repository`, tout ce qui vient d'un `Queryset` Django, car :
    - Utilise les Factory (autre couche) pour créer un objet du domaine
    - Permet de typer les valeurs de retour des querysets

- En cas de problème de performance en lecture
    - Cas possibles : 
        - Vue de recherche (vue liste)
        - données initiales de Forms filtrées : DTO ou domain service ? (exemple : filtrer les etds en états X ou Y)
        - Fichier Excel
        - Fichier PDF
    - Dans ce cas, les Views/forms/pdf/excel... réutilisent un ApplicationService qui renvoie un DTO à partir d'un Repository

- En cas d'inexistence du domaine métier (développement d'écrans en lecture seule)

- Données initiales de nos formulaires (ChoiceField, django-autocomplete-light) - à la place des querysets
    - ApplicationService (lecture) qui renvoie un DTO à partir d'un Repository
    - **Attention : pas de logique métier dans Queryset !**
        - Exemple : afficher les campus de l'organisation UCL uniquement
            - CampusRepository.search(...)
            - SearchUCLCampusOnlyDomainService qui filtre en mémoire le résultat de CampusRepository.search(...) 
