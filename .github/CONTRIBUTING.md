## Table of Contents
- [Coding styles](#coding-styles)
    - [Indentation](#indentation)
    - [Signature des fonctions](#signature-des-fonctions)
    - [Constantes](#constantes)
    - [Enumérations](#enums)
    - [Kwargs](#kwargs)
    - [Commits](#commits)
    - [Pull requests](#pull-requests)
    - [Performance](#performance)
    - [Sécurité](#scurit)
- [API](#api)
- [Modèle (Django Model)](#modle-django-model)
- [Vue (Django View)](#vue-django-view)
- [Formulaire (Django Forms)](#formulaire-django-forms)
- [Gabarit (Django templates)](#gabarit-django-templates)
- [Filtre de gabarit (Django Template Tags)](#filtres-de-gabarits-django-template-tags)
- [Permissions](#permissions)
- [Droits de merge et reviews](#droits-de-merge-et-reviews)
- [Emails](#emails)
- [PDF](#pdf)
- [Domain driven design](#domain-driven-design)
    - [Conventions générales](#conventions-gnrales)
    - [Arborescence des packages](#arborescence-des-packages)
    - [Commande](#dddcommandpy)
    - [Domaine](#ddddomain)
    - [Repository](#dddrepository)
    - [Application service](#dddservice-application-service)
    - [Validator](#dddvalidator)


<br/><br/>

## Coding styles

#### PEP8
- [Guide PEP8](https://www.python.org/dev/peps/pep-0008/#indentation)


#### Style de code Django
- [Coding Style de Django](https://docs.djangoproject.com/en/2.2/internals/contributing/writing-code/coding-style/).


#### Indentation

```python
# Bon
return render(
    request,
    "template.html",
    {
        'students': students,
        'faculties': faculties,
        'teacher': teacher,
    }
)


# Mauvais
return render(request, "template.html", {
        'students': students, 'faculties': faculties,
        'teacher': teacher
        })

```
```python
# Bon
def my_function(
        arg1: str,
        arg2: int,
        kwarg1: str = None,
        kwarg2: int = None
) -> int:
    # Do something
    pass


# Mauvais
def my_function(arg1: str,
                arg2: int,
                kwarg1: str = None,
                kwarg2: int = None
) -> int:
    # Do something
    pass
```


#### Traductions
- Voir https://github.com/uclouvain/osis/blob/dev/doc/technical-manual.adoc#internationalization
- Supprimer les `Fuzzy` après avoir vérifié la traduction


#### Signature des fonctions
- Doit être typée ([python typing](https://docs.python.org/fr/3.6/library/typing.html))
- Types de retour de fonctions non autorisés (pas assez explicites) :
  - `dict` ==> utiliser `Dict[KeyType, ValueType]`
  - `list` ==> utiliser `List[TypeOfElement]`
- Éviter l'utilisation de fonctions qui renvoient plus d'un seul paramètre (perte de contrôle sur ce que fait la fonction et perte de réutilisation du code)


#### Constantes
- Ne pas utiliser de 'magic number' (constante non déclarée dans une variable) 
```python
# Bon
MINIMUM_AUTHORIZED_UPDATE_YEAR = 2026
NONE_OR_EMPTY_VERBOSE = "-"


def update_object(obj):
    if obj.year >= MINIMUM_AUTHORIZED_UPDATE_YEAR:
        pass

def verbose_value(value: int) -> str:
    return str(value) if value else NONE_OR_EMPTY_VERBOSE


# Mauvais
def update_object(obj):
    if obj.year >= 2019:
        pass


def verbose_value(value: int) -> str:
    return str(value) if value else "-"
```

#### Enums
- Utiliser des `ChoiceEnum` plutôt que des `CONSTANTES` contenant des tuples
```python
from base.models.utils.utils import ChoiceEnum

# Bon
class Categories(ChoiceEnum):
    TRAINING = _("Training")
    MINI_TRAINING = _("Mini-Training")
    GROUP = _("Group")
    
# Mauvais
TRAINING = "TRAINING"
MINI_TRAINING = "MINI_TRAINING"
GROUP = "GROUP"
CATEGORIES = (
    (TRAINING, _("Training")),
    (MINI_TRAINING, _("Mini-Training")),
    (GROUP, _("Group")),
)
```

#### kwargs
- Toujours déclarer `kwarg=None` (jamais instancier un objet mutable comme une `list`, `dict`...)

#### Commits
- Ajouter un message explicite à chaque commit
- Commiter souvent = diff limitée = facilité d'identification de commits amenant une régression = facilité de revert = facilité et rapidité de review

#### Pull requests
- Réduire au minimum le nombre de fichiers de migrations par fonctionnalité (limite le temps de création de la DB de test, facilite la review, limite les conflits)
- Ajouter la référence au ticket Jira dans le titre de la pull request (format = "OSIS-12345")
- Utiliser un titre de pull request qui identifie son contenu (facilite la recherche de pull requests et permet aux contributeurs du projet d'avoir une idée sur son contenu)
    - Le titre doit correspondre à l'intitulé du ticket Jira associé



#### Performance
- Suivre les bonnes pratiques Django :
    - [Guide des performances Django](https://docs.djangoproject.com/en/2.2/topics/performance/)
    - [Guide des optimisations Django](https://docs.djangoproject.com/en/2.2/topics/db/optimization/)


#### Sécurité
- Ne pas laisser de données sensibles/privées dans les commentaires/dans le code
- Dans les URL (`urls.py`), ne jamais passer un ID auto-incrémenté (fourni par le moteur DB) en paramètre 
    - À éviter : `<site_url>/?tutor_id=1234` ou `<site_url>/score_encoding/print/34`
    - Alternative : utiliser un UUID 
- Dans le cas d'insertion/modification des données venant de l'extérieur (exemple : fichiers excels), s'assurer que l'utilisateur qui injecte des données a bien tous les droits sur les données qu'il désire injecter.

<br/><br/>

## API
- Regroupe le `schema.yml`, les views REST et serializers (Django-Rest-Framework)
- Incrémenter la version du schema.yml (cf. `info: version: 'X.Y'`) à chaque modification de celui-ci
- Tout champ utilisé dans les filters (django-filters) doit se trouver aussi dans le serializer (tout champ "filtre" doit se trouver dans la donnée renvoyée)
 
<br/><br/>

## Modèle (Django Model)
- Regroupe les modèles Django et les classes pour la partie administration de Django
- 1 classe par fichier héritant de `django.db.models.Model`
- 1 classe par fichier héritant de `osis_common.models.osis_model_admin.OsisModelAdmin`
- Ne pas utiliser de `ManyToManyField` et déclarer explicitement les modèles de liaison (pour faciliter les noms de tables et synchronisations)
- Ne pas créer de **clé étrangère** vers le modèle auth.User, mais vers **base.Person**. Cela facilite la conservation des données du modèle `auth` lors des écrasements des DB de Dev, Test et Qa.
- Ne peut pas contenir de logique métier
- Accès : 
  - [couche Django Model](#modle-django-model) (un modèle peut référencer un autre modèle via FK)

<br/><br/>

## Vue (Django View)
- Ajouter les annotations pour sécuriser les méthodes dans les vues (user_passes_tests, login_required, require_permission)
- Ne peut pas contenir de logique métier
- Utiliser les [Class Based Views](https://docs.djangoproject.com/fr/2.2/topics/class-based-views/) à la place des function bases views
- Accès :
  - [couche Django Forms](#formulaire-django-forms)
  - [couche Application Service](#dddservice-application-service)
  - [couche Templates](#template-html)
  - [couche Template Tags](#template-django-template-tags)
  - Uniquement vues "list" et "excel" : [couche Django Models](#modle-django-model) (à analyser au cas par cas ; le DDD risquerait de complexifier ces vues)

<br/><br/>

## Formulaire (Django Forms)
- Regroupe les objets qui permettent de faciliter l'affichage du code HTML côté template
- Ne peut pas contenir de logique métier
- Accès :
  - [couche application service](#dddservice-application-service)

<br/><br/>

## Gabarit (Django Templates)
- Regroupe les fichiers `html` structurés en "blocks" afin de maximiser la réutilisation de templates
- Utilise Django-Bootstrap3 pour le rendering des [Django Forms](#formulaire-django-forms)
- Accès :
  - [couche Dango Templates](#gabarit-django-templates) (un template peut inclure d'autres templates)
  - [couche Dango Template Tags](#filtres-de-gabarits-django-template-tags)
- Arborescence des fichiers :
```
[templates]templates                                  # Root structure
├── [templates/blocks/]blocks                                # Common blocks used on all 
│   ├── [templates/blocks/forms/]forms
│   ├── [templates/blocks/list/]list
│   └── [templates/blocks/modal/]modal
├── [templates/layout.html]layout.html                      # Base layout 
└── [templates/learning_unit/]learning_unit
    ├── [templates/learning_unit/blocks/]blocks                        # Block common on learning unit
    │   ├── [templates/learning_unit/blocks/forms/]forms
    │   ├── [templates/learning_unit/blocks/list/]list
    │   └── [templates/learning_unit/blocks/modal/]modal
    ├── [templates/learning_unit/layout.html]layout.html               # Layout specific for learning unit
    ├── [templates/learning_unit/proposal/]proposal
    │   ├── [templates/learning_unit/proposal/create.html]create_***.html
    │   ├── [templates/learning_unit/proposal/delete.html]delete_***.html
    │   ├── [templates/learning_unit/proposal/list.html]list.html
    │   └── [templates/learning_unit/proposal/update.html]update_***.html
    └── [templates/learning_unit/simple/]simple
        ├── [templates/learning_unit/simple/create.html]create_***.html
        ├── [templates/learning_unit/simple/delete.html]delete_***.html
        ├── [templates/learning_unit/simple/list.html]list.html
        └── [templates/learning_unit/simple/update.html]update_***.html
```
<br/><br/>

## Filtres de gabarits (Django Template Tags)
- Regroupe les template tags Django
- Accès : 
  - Aucun (un template tag ne doit avoir aucune dépendance externe à lui-même)

<br/><br/>

## Permissions
- Voir [Osis-role](https://github.com/uclouvain/osis/blob/dev/osis_role/README.md)
- Lorsqu'une view nécessite des permissions d'accès spécifiques (en dehors des permissions fournies par Django) : 
    - créer un décorateur dans le dossier `app_django/views/perms`
    - exemple : `base/views/learning_units/perms/`

<br/><br/>

## Droits de merge et reviews
- Il est permis aux développeurs de merger la branche source (dev pour les branches technical et feature, qa ou master pour les branche hotfix) dans leur branche technical/feature/hotfix et de pusher cette modification directement sur la branche technical/feature/hotfix.
- La possibilité susvisée permet, techniquement, de merger toute PR vers ses propres branches technical/feature/hotfix. Il est donc impératif de respecter le principe selon lequel on ne merge pas son propre code vers les branches technical/feature/hotfix tant que ce code n'a pas été approuvé par un autre développeur. Quand la review est faite et le code approuvé, on peut merger sa PR si les checks sont au vert (Travis, codeclimate, Quality check).

<br/><br/>

## Emails
- Utiliser la fonction d'envoi de mail décrite dans `osis_common/messaging/send_mail.py`. Exemple:
```python
from osis_common.messaging import message_config, send_message as message_service
from base.models.person import Person

def send_an_email(receiver: Person):
    receiver = message_config.create_receiver(receiver.id, receiver.email, receiver.language)
    table = message_config.create_table(
        'Table title', 
        ['column 1', 'column 2'], 
        ['content col 1', 'content col 2']
    )
    context = {
        'variable_used_in_template': 'value',
    }
    subject_context = {
        'variable_used_in_subject_context': 'value',
    }
    message_content = message_config.create_message_content(
        'template_name_as_html', 
        'template_name_as_txt', 
        [table], 
        [receiver],
        context,
        subject_context
    )
    return message_service.send_messages(message_content)

```

<br/><br/>

## PDF
- Utiliser WeasyPrint ou pour la création de documents PDF (https://weasyprint.org/)
- Utilisation de ReportLab dépréciée (car compliqué d'utilisation)

<br/><br/>

## Domain driven design

#### Conventions générales
- Gestion des urls : utiliser des urls contenant clés naturelles et pas des ids de la DB. 
Dans de rares cas plus complexes (exemple: identification d'une personne : UUID) (Attention aux données privées)
- Tous les paramètres d'entrée et de sortie doivent être typés
- Les fonctions qui renvoient une objet, int, str doivent être nommés "get_<sth>"
- Les fonctions qui renvoient un booléen doivent être nommés de sorte à poser une question fermée 
(où la réponse ne peut être que "Oui" ou "Non"). Exemples : `is_<sth>`, `has_<sth>`, `contains_<sth>`...
- Les fonctions qui renvoient une list, set, dict :
    - get_<nom_pluriel>() -> renvoie tout , sans filtres. Toujours avec un "s". 
    
    Exemple: ```def get_nodes() -> List['Node']```

    - Pour les fonctions de recherche : search_<nom_pluriel>()
    
    Exemple: ```def search_nodes(*typed_filters) -> List['Node']```

- Nommage des fonctions, fichiers **privés** (uniquement scope de la classe ou du fichier) : __function

    Exemple: ```def __my_private_function(param: str) -> None```

- Nommage des fonctions, fichiers **protégés** (uniquement visible / utilisable dans le package) : _function

    Exemple: ```def _my_protected_function(param: str) -> None```
 - Implémentation des Value Objects en utilisant la librairie **attrs** en définissant la classe comme étant frozen (immutable) et faisant usage de slots.



> :information_source: **Info : Toutes les interfaces et classes abstraites réutilisables pour le DDD
> (ValueObject, EntityObject...) sont définies [dans osis_common](https://github.com/uclouvain/osis-common/tree/master/ddd)**



#### Arborescence des packages

```
django_app
 ├─ ddd
 |   ├─ command.py
 |   |
 |   ├─ domain
 |   |   ├─ <objet_métier>.py  (Aggregate root)
 |   |   ├─ _entity.py (protected)
 |   |
 |   ├─ repository
 |   |   ├─ <objet_métier>.py
 |   |   ├─ _<entity>.py  (protected)
 |   |
 |   ├─ service (application service)
 |   |   ├─ read
 |   |   |   ├─ <action_métier>_service.py
 |   |   |
 |   |   ├─ write
 |   |       ├─ <action_métier>_service.py
 |   |
 |   ├─ validators
 |       ├─ invariant_metier.py
 |       ├─ invariant_metier_2.py
 |
 ├── models
 |
 ├── views (gestion des httpRequests)
 |
 ├── API
 |   ├─ views
```

#### ddd/command.py
- Regroupe les **objets** qui sont transmis en paramètre d'un service (ddd/service)
- Représente une simple "dataclass" possédant des attributs primitifs
- Ces classes sont publiques : elles sont utilisées par les views
- Doit obligatoirement hériter de l'objet CommandRequest
- Nommage des classes de commande : <ActionMetier>Command

Exemple : 
```python
# command.py
import attr

from osis_common.ddd import interface
from program_management.ddd.business_types import Path


@attr.s(frozen=True, slots=True)
class DetachNodeCommand(interface.CommandRequest):
    path_to_detach = attr.ib(type=Path)


@attr.s(frozen=True, slots=True)
class AttachNodeCommand(interface.CommandRequest):
    path_to_node_to_attach = attr.ib(type=Path)
 
```

#### ddd/domain
- Regroupe les **objets** du domaine métier qui doivent obligatoirement hériter de ValueObject, Entity ou RootEntity
- Déclare les EntityIdentity (dans le même fichier que la classe du domaine qui utilise cet EntityIdentity)
- Les ValueObject doivent obligatoirement redéfinir les méthodes `__hash__()` et `__eq__()`
- Seuls les AggregateRoot (interface.RootEntity) sont publiques ; les `Entity` utilisées par l'aggregat root sont `protected`
- 1 fichier par objet du domaine métier. Nommage : <objet_métier>.py
- Nommage des objets : ObjetMetier.

Exemple :
```python
# ddd/domain/program_tree.py  -> Aggregate root du domaine "program_management"
import attr

from osis_common.ddd import interface


@attr.s(frozen=True, slots=True)
class ProgramTreeIdentity(interface.EntityIdentity):
    code = attr.ib(type=str)
    year = attr.ib(type=int)

class ProgramTree(interface.RootEntity):
    pass
 
```
```python
# ddd/domain/_node.py  -> Une Entity "protected" du domaine "program_management"
from osis_common.ddd import interface

class Node(interface.Entity):
    pass

```


#### ddd/repository

- Regroupe les **objets** qui permettent de faire le lien entre le stockage des données et nos objets du domaine.
- Chargée de persist / load les données (pour Osis, le stockage est fait une DB PostGres)
- Utilisation d'une interface commune AbstractRepository
- Les objets du repository doivent obligatoirement implémenter AbstractRepository
- Nommage des fichiers : <objet_métier>.py
- Nommage des objets : <ObjetMetier>Repository. 

Exemple :
```python
# ddd/repository/program_tree.py
from osis_common.ddd import interface

class ProgramTreeRepository(interface.AbstractRepository):
    """Chargé d'implémenter les fonctions fournies par AbstractRepository."""
    pass
 
```

#### ddd/service (application service)

- Regroupe les **fonctions** qui implémentent les uses cases des utilisateurs (Given when then)
- Chargée d'orchestrer les appels vers les couches du DDD (repository, domain...) et de déclencher les événements (exemple : envoi de mail)
- Les fonctions de service reçoivent en paramètres uniquement des objets CommandRequest ([ddd/command.py](#ddd/command.py))
- Les services renvoient toujours un EntityIdentity ; c'est la responsabilité des views de gérer les messages de succès ;
- Séparer les services write et read dans des dossiers séparés
- Doit être documentée (car couche publique réutilisable)
- Les fonctions de service sont toujours publiques
- Nommage des fichiers : <action_metier>_service.py
- Nommage des fonctions : <action_metier>

Exemple:
```python
# ddd/service/detach_node_service.py
from osis_common.ddd import interface

def detach_node(command_request_params: interface.CommandRequest) -> interface.EntityIdentity:
    # Given
    # Appel au repository pour charger les données nécessaires
    
    # When
    # Appel à l'action métier sur l'objet du domaine
    
    # Then
    pass
 
```

#### ddd/validator

- Regroupe les invariants métier (règles business)
- Se charge de raise des BusinessException en cas d'invariant métier non respecté
- Les messages doivent être traduits (si BusinessException s'en charge, le makemessages ne reprendra pas messages à traduire car ils seront stockés dans des variables...)
- Doit hériter de BusinessValidator
- Sont toujours `protected` (accessibles uniquement par le Domain)
- 1 fichier par invariant métier
- Nommage des fichiers : <invariant_metier>.py
- Nommage des objets : <InvariantMetier>Validator

Exemple : 
```python
# ddd/validator/_detach_root.py  # protected
from osis_common.ddd import interface
from django.utils.translation import gettext as _
from base.ddd.utils import business_validator

class DetachRootValidator(business_validator.BusinessValidator):

    def __init__(self, tree: 'ProgramTree', path_to_detach: 'Path'):
        super(DetachRootValidator, self).__init__()
        self.path_to_detach = path_to_detach
        self.tree = tree

    def validate(self):
        if self.tree.is_root(self.tree.get_node(self.path_to_detach)):
            raise interface.BusinessException(_("Cannot perform detach action on root."))

```

