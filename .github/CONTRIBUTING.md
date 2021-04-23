# Table of Contents
- [Coding styles](#coding-styles)
    - [PEP8](#pep8)
    - [Style de code Django](#style-de-code-django)
    - [Conventions de nommage](#conventions-de-nommage)
    - [Indentation](#indentation)
    - [Signature des fonctions](#signature-des-fonctions)
    - [Constantes](#constantes)
    - [Enumérations](#enums)
    - [Kwargs](#kwargs)
    - [Commits](#commits)
    - [Pull requests](#pull-requests)
    - [Performance](#performance)
    - [Sécurité](#sécurité)
- [Onion Architecture](https://dev.to/barrymcauley/onion-architecture-3fgl)
- [Arborescence des packages](#arborescence-des-packages)
- [Couche Django app](#couche-django-app)
    - [API](#api)
    - Calendar (événements académiques) - Documentation/guidelines à développer
    - [Forms (Django)](#formulaire-django-forms)
    - [Model (Django)](#modèle-django-model)
    - [Views (Django)](#vue-django-view)
    - [Templates (Django)](#gabarit-django-templates)
    - [Template Tags (Django)](#filtres-de-gabarits-django-template-tags)
    - Tests (unit tests) - Documentation/guidelines à développer
- [Couche DDD : Domain Driven Design](#domain-driven-design)
    - [Exemple concret d'implémentation des guidelines](https://github.com/uclouvain/osis/tree/dev/ddd/logic)
    - [Conventions générales](#conventions-générales)
    - [Builder (factory)](#dddbuilder)
    - [Domain](#ddddomain)
        - Model
            - [Entity](#ddddomainentity)
            - [RootEntity (aggregate)](#ddddomainrootentity)
            - [ValueObject](#ddddomainvalueobject)
            - [EntityIdentity](#ddddomainentityidentity)
        - [Service (Domain Service)](#domain-services)
        - Validator
            - [ValidatorList (validators_by_business_action.py)](#dddvalidator-list)
            - [Validator](#dddvalidator)
            - [BusinessException (exceptions.py)](#ddddomainbusinessexception)
    - [Repository (interface)](#dddrepository) (implémentation dans la couche "infrastructure")
    - Test (unit tests) - Documentation/guidelines à développer
    - [Use case (Application Service)](#dddservice-application-service)
    - [Commande (commands.py)](#dddcommandpy)
    - [DTOs (dtos.py)](#dto--data-transfer-object)
- [Couche Infrastructure](#couche-infrastructure)
    - [Exemple concret d'implémentation des guidelines](https://github.com/uclouvain/osis/tree/dev/infrastructure)
    - [Repository (implémentation)](#repository-implémentation)
- [Droits de merge et reviews](#droits-de-merge-et-reviews)
- [Emails](#emails)
- [Gestion des permissions](#permissions)
- [PDF](#pdf)
- [FAQ : questions - réponses](faq.md)
- [Références](references.md)


<br/><br/>

# Coding styles

## PEP8
- [Guide PEP8](https://www.python.org/dev/peps/pep-0008/#indentation)


## Style de code Django
- [Coding Style de Django](https://docs.djangoproject.com/en/2.2/internals/contributing/writing-code/coding-style/).


## Conventions de nommage

- Dans le code qui implémente le DDD, **seuls des termes métier doivent apparaître** (pas de termes techniques).
Se référer aux termes utilisés dans la description des analyses. Cf. [L'analyse est en français, le code en anglais : comment traduire correctement le métier ??](faq.md#question-lanalyse-est-en-franais-le-code-en-anglais--comment-traduire-correctement-le-mtier-)


- Toute fonction qui renvoie un seul résultat : get_<sth>
    
    Exemple : ```def get_something() -> object```
    
- Toute fonction qui renvoie un booléen doit être nommé sous forme de question fermée (dont la réponse ne peut être que "Oui" ou "Non")

    Exemples : ```def has_something() -> bool```, ```def is_something() -> bool```, ```def containes_something() -> bool```

- Toute fonction qui renvoie une `list`, `set`, `dict` :
    - Types de retour de fonctions non autorisés (pas assez explicites) :
        - `dict` ==> utiliser `Dict[KeyType, ValueType]`
        - `list` ==> utiliser `List[TypeOfElement]`
        - `set` ==> utiliser `Set[TypeOfElement]`

    - get_<nom_pluriel>() -> renvoie tout , sans filtres. Toujours avec un "s". 
    
    Exemple: ```def get_nodes() -> List['Node']```

    - Pour les fonctions de recherche : search_<nom_pluriel>()
    
    Exemple: ```def search_nodes(*typed_filters) -> List['Node']```

- Nommage des fonctions, fichiers **privés** (uniquement scope de la classe ou du fichier) : __function

    Exemple: ```def __my_private_function(param: str) -> None```

- Nommage des fonctions, fichiers **protégés** (uniquement visible / utilisable dans le package) : _function

    Exemple: ```def _my_protected_function(param: str) -> None```



## Indentation

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


## Traductions
- Voir [manuel technique](https://github.com/uclouvain/osis/blob/dev/doc/technical-manual.adoc#internationalization)
- Supprimer les `Fuzzy` après avoir vérifié la traduction


## Signature des fonctions
- Doit être typée ([python typing](https://docs.python.org/fr/3.6/library/typing.html))
- Éviter l'utilisation de fonctions qui renvoient plus d'un seul paramètre (perte de contrôle sur ce que fait la fonction et perte de réutilisation du code)


## Constantes
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

## Enums
- Utiliser des `ChoiceEnum` plutôt que des `CONSTANTES` contenant des tuples
- Doit être déclaré dans le [domaine (DDD)](#ddddomain)
    - Note : à refactorer : le code Osis actuel définit encore les énumérations dans les fichiers Django "models"
- Les modèles Django peuvent réutiliser les énumérations du Domaine (pour les `ChoiceField`)
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

## kwargs
- Toujours déclarer `kwarg=None` (jamais instancier un objet mutable comme une `list`, `dict`...)

## Commits
- Ajouter un message explicite à chaque commit
- Commiter souvent = diff limitée = facilité d'identification de commits amenant une régression = facilité de revert = facilité et rapidité de review

## Pull requests
- Réduire au minimum le nombre de fichiers de migrations par fonctionnalité (limite le temps de création de la DB de test, facilite la review, limite les conflits)
- Ajouter la référence au ticket Jira dans le titre de la pull request (format = "OSIS-12345")
- Utiliser un titre de pull request qui identifie son contenu (facilite la recherche de pull requests et permet aux contributeurs du projet d'avoir une idée sur son contenu)
    - Le titre doit correspondre à l'intitulé du ticket Jira associé



## Performance
- Suivre les bonnes pratiques Django :
    - [Guide des performances Django](https://docs.djangoproject.com/en/2.2/topics/performance/)
    - [Guide des optimisations Django](https://docs.djangoproject.com/en/2.2/topics/db/optimization/)


## Sécurité
- Ne pas laisser de données sensibles/privées dans les commentaires/dans le code
- Dans les URL (`urls.py`), ne jamais passer un ID auto-incrémenté (fourni par le moteur DB) en paramètre 
    - À éviter : `<site_url>/?tutor_id=1234` ou `<site_url>/score_encoding/print/34`
    - Alternative : utiliser un UUID 
- Dans le cas d'insertion/modification des données venant de l'extérieur (exemple : fichiers excels), s'assurer que l'utilisateur qui injecte des données a bien tous les droits sur les données qu'il désire injecter.



<br/><br/><br/><br/>


# Arborescence des packages

```
Osis (racine projet git)
 ├─ ddd
 |   ├─ logic (aucun import externe comme Django, etc.)
 |       ├─ bounded_context_1
 |       |   |
 |       |   ├─ builder (factory)
 |       |   |   ├─ <root_entity>_builder.py  (Builder pour RootEntity)
 |       |   |   ├─ <root_entity_entity>_builder.py  (Builder pour EntityIdentity)
 |       |   |
 |       |   ├─ domain
 |       |   |   ├─ model
 |       |   |   |   ├─ <root_entity>.py  (Aggregate)
 |       |   |   |   ├─ _<entity>.py (protected)
 |       |   |   |   ├─ _<value_object>.py (protected)
 |       |   |   |
 |       |   |   ├─ service (Domain Service)
 |       |   |   |   ├─ <domain_service_name>.py
 |       |   |   |
 |       |   |   ├─ validator
 |       |   |       ├─ _should_<business_validator_rule>.py
 |       |   |       ├─ exceptions.py
 |       |   |       ├─ validator_by_business_action.py
 |       |   |
 |       |   ├─ repository (uniquement interfaces !)
 |       |   |   ├─ i_<root_entity>.py
 |       |   |
 |       |   ├─ test
 |       |   |   ├─ ...
 |       |   |
 |       |   ├─ use_case (Application Service)
 |       |   |   ├─ read
 |       |   |   |   ├─ <action_métier>_service.py
 |       |   |   |
 |       |   |   ├─ write
 |       |   |       ├─ <action_métier>_service.py
 |       |   |
 |       |   ├─ commands.py
 |       |   |
 |       |   ├─ dtos.py
 |       |   |
 |       |   ├─ events.py
 |       |
 |       ├─ bounded_context_2
 |       |
 |       ├─ bounded_context_3
 |       |
 |       ├─ shared_kernel
 |   
 ├─ infrastructure
 |   ├─ bounded_context_1
 |   |   ├─ repository (implémentation des interfaces)
 |   |       ├─ <objet_métier>.py
 |   |
 |   ├─ bounded_context_2
 |   |
 |   ├─ bounded_context_3
 |   |
 |   ├─ message_bus.py
 |
 ├─ django_app_1
 |   ├─ api
 |   ├─ calendar (événements académiques)
 |   ├─ forms
 |   ├─ locale (traductions)
 |   ├─ migrations (migrations DB)
 |   ├─ models
 |   ├─ tasks (tâches planifiées)
 |   ├─ templates
 |   ├─ templatetags
 |   ├─ tests
 |   ├─ views
 |
 ├─ django_app_2
 |
 ...

```


<br/><br/><br/><br/>


# Couche Django app


## API
- Regroupe le `schema.yml`, les views REST et serializers (Django-Rest-Framework)
- Incrémenter la version du schema.yml (cf. `info: version: 'X.Y'`) à chaque modification de celui-ci
- Tout champ utilisé dans les filters (django-filters) doit se trouver aussi dans le serializer (tout champ "filtre" doit se trouver dans la donnée renvoyée)
 
 
 
<br/><br/><br/><br/>



## Formulaire (Django Forms)
- Regroupe les objets qui permettent de faciliter l'affichage du code HTML côté template
- Valide uniquement les règles métier suivantes : 
    - Types de champs (int, str, ...)
    - Champs requis
    - Énumérations (ChoiceField)
    - Toutes ces validations sont **dupliquées** dans notre domaine ([couche Validators](#dddvalidator))
    - Cf. [doc sur "two steps validation"](https://github.com/uclouvain/osis/blob/dev/doc/two_steps_validation.md)
- Doit hériter de `DisplayExceptionsByFieldNameMixin`
    - Fournit `field_name_by_exception` et `get_command()` - Cf. [doc sur "two steps validation"](https://github.com/uclouvain/osis/blob/dev/doc/two_steps_validation.md)

- Accès :
  - [couche Commands](#dddcommandpy)


```python
# Django Form
class UpdateTrainingForm(DisplayExceptionsByFieldNameMixin, forms.Form):
    code = UpperCaseCharField(label=_("Code"))
    min_constraint = forms.IntegerField(label=_("minimum constraint").capitalize())
    max_constraint = forms.IntegerField(label=_("maximum constraint").capitalize())

    field_name_by_exception = {
        CodeAlreadyExistException: ('code',),
        ContentConstraintMinimumMaximumMissing: ('min_constraint', 'max_constraint'),
        ContentConstraintMaximumShouldBeGreaterOrEqualsThanMinimum: ('min_constraint', 'max_constraint'),
        ContentConstraintMinimumInvalid: ('min_constraint',),
        ContentConstraintMaximumInvalid: ('max_constraint',),
    }
    
    def get_command(self) -> CommandRequest:
        return CommandRequest(**self.validated_data)

```


<br/><br/><br/><br/>




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
  - Uniquement vues "list" et "excel" : [couche Django Models](#modle-django-model) (à analyser au cas par cas ; le DDD risquerait de complexifier ces vues - cf. [Quand doit-on appliquer le DDD ? Quid du CRUD ?](faq.md#question-quand-doit-on-appliquer-le-ddd--quid-du-crud--quid-des-views-de-recherche-fichiers-excels-pdfs-))

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





<br/><br/><br/><br/><br/><br/><br/><br/>





# Domain driven design

## Conventions générales
- Cf. [Quand doit-on appliquer le DDD ? Quid du CRUD ?](faq.md#question-quand-doit-on-appliquer-le-ddd--quid-du-crud--quid-des-views-de-recherche-fichiers-excels-pdfs-)
- Utiliser la librairie [python attrs](https://www.attrs.org/en/stable/)
- Gestion des urls : utiliser des urls contenant clés naturelles et pas des ids de la DB. 
Dans de rares cas plus complexes (exemple: identification d'une personne : UUID) (Attention aux données privées)



> :information_source: **Info : Toutes les interfaces et classes abstraites réutilisables pour l'implémentation du DDD
> (ValueObject, EntityObject...) sont définies [dans osis_common](https://github.com/uclouvain/osis-common/tree/master/ddd)**
> et [dans base.ddd.utils.business_validator](https://github.com/uclouvain/osis/blob/dev/base/ddd/utils/business_validator.py)**


<br/><br/><br/><br/>


## ddd/builder

- Regroupe l'ensemble des factories et builders pour nos objets du domaine
    - Cf. [Patterns Factory et Builder](#../doc/patterns_factory_builder_singleton.md)
- Obligatoire pour tous nos objets `RootEntity` et `EntityIdentity`
    - Tout ce qui est `publique` dans notre domaine possède un `Builder`
- Nommage des fichiers : <objet_métier>_builder.py
- Nommage des objets : <ObjetMetier>Builder
- Accès :
    - [couche Domain](#ddddomain)
- Cf. [interface.EntityIdentity](https://github.com/uclouvain/osis-common/blob/master/ddd/interface.py#L28)
- Note : le pattern 'builder' peut être réutilisé pour nos `Entity` et `ValueObject` 
    - scope : `privé`
    - encapsulé dans le même fichier que `Entity` / `ValueObject`

Exemple :
```python
from osis_common.ddd import interface


class TrainingBuilder(interface.RootEntityBuilder):
    @classmethod
    def build_from_command(cls, cmd: 'CreateTrainingCommand') -> 'Training':
        raise NotImplementedError()

    @classmethod
    def build_from_repository_dto(cls, dto_object: 'DTO') -> 'Training':
        raise NotImplementedError()

```


<br/><br/><br/><br/>


## ddd/domain
- Encapsule la logique métier, capturée dans les **objets** suivants:
    - Entity
    - RootEntity
    - ValueObject
    - EntityIdentity
    - BusinessException
- Cf. [domaine pure et domain complet](application_service_vs_domain_service.md)
- Ne possède aucune dépendance externe
- Contient uniquement des termes métier non techniques -> doit être compréhensible par le métier
- Un même domaine peut posséder plusieurs RootEntity
- 1 fichier par objet du domaine métier. Nommage : <objet_métier>.py
- Nommage des objets : ObjetMetier
- Accès :
    - Aucun (tout ce qui se trouve dans le domaine ne doit avoir aucune dépendance externe à lui-même)

<br/><br/>

### ddd/domain/Entity

- Protected : utilisé uniquement par d'autres `Entity` ou par un [RootEntity](#rootentity)
- Ne possède pas de repository associé
- Cf. [interface.Entity](https://github.com/uclouvain/osis-common/blob/master/ddd/interface.py#L32)
- Possède une identité [EntityIdentity](#entityidentity)
- Deux entités sont identiques ssi leurs identités sont les mêmes
- Mutable
    - Toute modification de l'objet change l'état de l'objet
    - Possède un historique (à travers le temps)
- Exemple :

```python
# .../domain/_study_domain.py
import attr

from osis_common.ddd import interface

 
@attr.s(frozen=True, slots=True)
class StudyDomainIdentity(interface.EntityIdentity):
    decree_name = attr.ib(type=str)
    code = attr.ib(type=str)


@attr.s(slots=True)
class StudyDomain(interface.Entity):
    entity_id = attr.ib(type=StudyDomainIdentity)
    name = attr.ib(type=str)

```


<br/><br/>


### ddd/domain/RootEntity

- Même définition qu'une Entity, sauf : 
    - **Public** : utilisable par les couches en dehors du domaine ([service](#dddservice-application-service), [repository](#dddrepository)...)
    - Possède un [repository](#dddrepository) associé
        - persistence : 1 transaction par aggrégat (tout l'aggrégat est persisté, ou rien du tout - mais pas à moitié)
    - Si un aggregate en contient un autre, référencer l'Aggregates par EntityIdentity **pour assurer le découplage**
- Exemple : 
```python
# .../domain/training.py
import attr

from osis_common.ddd import interface


@attr.s(slots=True)
class Training(interface.RootEntity):
    entity_id = attr.ib(type=TrainingIdentity)
    title = attr.ib(type=str)
    study_domains = attr.ib(type=List[StudyDomain])
    # Other fields ...

```


<br/><br/>


### ddd/domain/ValueObject

- Protected : utilisé uniquement par d'autres [ValueObject](#valueobject), [Entity](#entity) ou par un [RootEntity](#rootentity)
- Ne possède pas de repository associé
- Cf. [interface.ValueObject](https://github.com/uclouvain/osis-common/blob/master/ddd/interface.py#L20)
- Doit redéfinir les méthodes `__hash__()` et `__eq__()`
- Ne possède pas d'identité
    - L'ensemble de ses attributs composent son identité
- Deux ValueObjects sont les mêmes ssi l'ensemble des valeurs de leurs attributs sont les mêmes
- Immuable (librairie `attrs` => `frozen=True`)
    - Toute modification de l'objet signifie que c'est un nouvel objet
    - Ne possède pas d'historique
- Appartient d'office à une Entity
- Exemples :
    - Une date
    - Une adresse

```python
# .../domain/_address.py
import attr

from osis_common.ddd import interface


@attr.s(frozen=True, slots=True)
class Address(interface.ValueObject):
    country_name = attr.ib(type=str)
    street_name = attr.ib(type=str)
    street_number = attr.ib(type=str)
    city = attr.ib(type=str)
    postal_code = attr.ib(type=str)

    
    def __eq__(self, other):
        return self.country_name == other.country_name  \
            and self.city == other.city \
            and self.street_name == other.street_name \
            and self.street_number == other.street_number \
            and self.postal_code == other.postal_code

    def __hash__(self):
        return hash(self.country_name + self.street_name + self.street_number + self.city + self.postal_code)

```


<br/><br/>


### ddd/domain/EntityIdentity

- Représente l'identité d'une entité de notre domaine
- Représente un ValueObject (si n'importe quelle valeur change, ce n'est plus la même "identité")
- Visibilité :
    - `protected` (si c'est l'identité d'une Entity)
    - `publique` (si c'est l'identité d'une RootEntity)
- Déclaré dans le même fichier que l'Entity qui l'utilise
- Cas d'exception (rare) : si l'identité logique est complexe à construire 
(exemple : identité d'une personne - nom, prénom, age, lieu de naissance...), l'EntityIdentity sera composé d'un `UUID`
- Cf. [interface.EntityIdentity](https://github.com/uclouvain/osis-common/blob/master/ddd/interface.py#L28)

- Exemple : 
```python
# .../domain/training.py
import attr
from osis_common.ddd import interface


# Identité d'un Training
@attr.s(frozen=True, slots=True)
class TrainingIdentity(interface.EntityIdentity):
    acronym = attr.ib(type=str)
    year = attr.ib(type=int)


# Aggregate (RootEntity)
@attr.s(slots=True)
class Training(interface.RootEntity):
    entity_id = attr.ib(type=TrainingIdentity)
    # Other fields ...

```



<br/><br/><br/><br/>



## Domain services

- Regroupe les **objets** qui ne représentent pas un `ValueObject` ou une `Entity` du domaine. 
Exemple : un calculateur de taxe
- Encapsule de la logique métier, qui ne sait pas être contenue directement dans le domaine
    - Le plus rarement possible ! 
    - Cf. [domaine pure et domain complet](application_service_vs_domain_service.md)
    - Cf. [application service VS domain service](application_service_vs_domain_service.md)
- Renvoie uniquement des types primitifs, des Entity ou ValueObjects
- Peut recevoir une Entity, ValueObject, type_primitif ou repository
- Accès :
    - [couche Domain](#ddddomain) (via injection de dépendance)
    - [couche Repository](#dddrepository) (via injection de dépendance)
    - [couche BusinessException](#ddddomainbusinessexception)

Exemple :
```python
# ddd/domain/service/sequence_generator.py
from osis_common.ddd import interface

class GenerateSequenceId(interface.DomainService):
    
    def generate(self, entity: RootEntity) -> int:
        """Chargé de générer un nouveau numéro de séquence (unique) dans un système externe (database, etc.)"""
        pass

```


<br/><br/><br/><br/>


## ddd/validator list
- Regroupe le listing des règles métier à respecter par action métier
- Doit hériter de [TwoStepsMultipleBusinessExceptionListValidator](https://github.com/uclouvain/osis/blob/dev/doc/two_steps_validation.md)
- Visibilité : `protected` (accessibles uniquement par le Domain)
- 1 fichier pour toutes les règles par action : `validators_by_business_action.py`
- Accès : 
    - [couche Domain](#ddddomain) (Les validateurs font partie du domaine)
    - [couche Validator](#dddvalidator) (Les validateurs font partie du domaine)
Exemple :
```python


@attr.s(frozen=True, slots=True)
class BusinessActionValidatorList(TwoStepsMultipleBusinessExceptionListValidator):

    command = attr.ib(type=CommandRequest)
    any_domain_object = attr.ib(type=Union[RootEntity, Entity, EntityIdentity, ValueObject, PrimitiveType])

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return [
            FieldNameRequiredFieldValidator(self.command.field_name),
            FieldNameChoiceFieldValidator(self.command.field_name),
            FieldNameTypeFieldValidator(self.command.field_name),
        ]

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldValidateRuleAValidator(self.command.field_name, self.any_domain_object),
            ShouldValidateRuleBValidator(self.command.other_field, self.command.field_a, self.command.field_b),
            ShouldValidateRuleCValidator(self.any_domain_object),
            # ...
        ]


```

<br/><br/>



## ddd/validator

- Regroupe les invariants métier (règles business)
- Chargé de raise des `BusinessException` en cas d'invariant métier non respecté
- Doit hériter de BusinessValidator
- Visibilité : `protected` (accessibles uniquement par le Domain)
- 1 fichier par invariant métier
- Nommage des fichiers : should_<invariant_metier>.py
- Nommage des objets : Should<InvariantMetier>Validator
- Accès : 
    - [couche Domain](#ddddomain) (Les validateurs font partie du domaine)
    - [couche Exceptions (business exceptions)](#ddddomainbusinessexception)


Exemple : 
```python
from base.ddd.utils import business_validator

@attr.s(frozen=True, slots=True)
class MyBusinessValidator(BusinessValidator):
    object_used_for_validation = attr.ib(type=Union[RootEntity, Entity, EntityIdentity, ValueObject, PrimitiveType])
    other_object_used_for_validation = attr.ib(type=Union[RootEntity, Entity, ValueObject, EntityIdentity, PrimitiveType])

    def validate(self):
        if self.object_used_for_validation != self.other_object_used_for_validation:
            raise MyOwnValidatorBusinessException()

```


<br/><br/>



## ddd/domain/BusinessException
- Regroupe les exceptions qui représentent des règles métier non respectée
- Déclare les messages d'erreur **traduits** destinés aux utilisateurs
    - Unique endroit qui "casse" l'isolation du domaine (utilisation externe au domaine) : module de traduction Django
- Visibilité : `protected` (utilisé uniquement par les validateurs et objets notre domaine)
- Hérite de `BusinessException`
- Accès :
    - Aucun (une Exception ne doit avoir aucune dépendance externe à elle-même)

- Exemple :

```python
### .../domain/exceptions.py
from osis_common.ddd.interface import BusinessException
from django.utils.translation import gettext_lazy as _


class CannotDeleteDueToExistingStudentsEnrolled(BusinessException):
    def __init__(self, training_identity: 'TrainingIdentity', *args, **kwargs):
        message = _('Cannot delete because there are students enrolled to {}'.format(training_identity))
        super().__init__(message, **kwargs)

```


<br/><br/><br/><br/>


## ddd/repository

- Regroupe les **interfaces** qui déclarent les fonctions de liaison entre le stockage des données et nos objets du domaine
- Chargée de persister et charger les données
- Hérite de `AbstractRepository`
- Persiste uniquement des RootEntity qui sont [complets](https://github.com/uclouvain/osis/blob/dev/doc/domain_purity_and_completeness.md)
    - Évite les risque d'inconsistance dans les vérifications des invariants métier (cf. [validation avant ou après?](https://github.com/uclouvain/osis/blob/dev/doc/two_steps_validation.md#appliquer-les-validateurs-avant-ou-apr%C3%A8s-ex%C3%A9cution-dune-action-m%C3%A9tier-de-lobjet-du-domaine-))
- Peut déclarer des fonctions qui renvoient des [DTOs](https://github.com/uclouvain/osis/blob/dev/doc/dto.md) 
dans des cas spécifiques relatifs à la consultation (cf. [quand utiliser des DTO ?](https://github.com/uclouvain/osis/blob/dev/doc/dto.md#quand-utiliser-un-dto-))
- Nommage des fichiers : i_<objet_métier>.py
- Nommage des objets : <ObjetMetier>IRepository
- Cf. [interface.AbstractRepository](https://github.com/uclouvain/osis-common/blob/master/ddd/interface.py#L53)
- Accès :
    - [couche Django Model](#modle-django-model)
    - [couche Domain](#ddddomain)
    - [couche Builder](#dddbuilder)

Exemple :
```python
# ddd/repository/training.py
from osis_common.ddd import interface

class TrainingIRepository(interface.AbstractRepository):
    """
    Chargé de déclarer les fonctions que devra fournir toute implémentation d'un stockage de données.
    L'interface peut être vide (déclairer uniquement les fonctions de bases proposées par AbstractRepository).
    """
    
    def search_only_for_specific_list_view(self, search_param1: str, search_param2: int) -> List[DTO]:
        raise NotImplementedError


```


<br/><br/><br/><br/>


## ddd/service (application service)

- Regroupe les **fonctions** qui implémentent les uses cases des utilisateurs (Given when then)
- Chargé d'orchestrer les appels vers les couches du DDD (repository, domain...) et de déclencher les événements (exemple : envoi de mail)
- Reçoit en paramètre :
    - 1 CommandRequest ([ddd/command.py](#ddd/command.py))
    - 1 ou plusieurs [repositories](#dddrepository)
- Renvoit toujours un EntityIdentity ; c'est la responsabilité des views de gérer les messages de succès ;
- Séparé en 2 catégories : `write` et `read`
- Doit être documentée (car couche publique réutilisable)
- Visibilité : `publique`
- Nommage des fichiers : <action_metier>_service.py
- Nommage des fonctions : <action_metier>
- Cf. [application service VS domain service](application_service_vs_domain_service.md)
- Accès:
    - [couche Builder](#dddbuilder)
    - [couche Domaine](#ddddomain)
    - [couche DomainService](#domain-services)
    - [couche Repository](#dddrepository) (via injection de dépendance)


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

<br/><br/><br/><br/>


## ddd/command.py
- Regroupe les **objets** qui sont transmis en paramètre d'un service (ddd/service)
- Représente une simple "dataclass" possédant des attributs primitifs (qui sont des données entrées par l'utilisateur)
- Public : utilisables en dehors de la couche du domaine ([service](#dddservice-application-service), [views](#vue-django-view)...)
- Séparé en read/write ([CQS](CQS_command_query_separation.md))
- Doit obligatoirement hériter de l'objet CommandRequest
- Pas d'héritage d'une autre commande, 1 commande = 1 action métier = 1 application service (use case)
    - Cf. [message bus](https://github.com/uclouvain/osis/blob/dev/doc/messages_bus.md)
- Nommage des classes de commande : <ActionMetier>Command

Exemple : 
```python
# command.py
import attr
from osis_common.ddd import interface


@attr.s(frozen=True, slots=True)
class UpdateTrainingCommand(interface.CommandRequest):
    acronym = attr.ib(type=str)
    year = attr.ib(type=str)
    title = attr.ib(type=str)
    # ... other fields

```


<br/><br/><br/><br/>



## DTO : Data Transfer Object

- "Objet de transfert de données"
- Patron de conception d'architecture
- Objectif : simplifier le transfert des données entre les couches d'une application logicielle 
- Possède uniquement des déclarations d'attributs
- Aucune logique technique, métier, fonction...
- "Contrat de données" qui nous aide à atteindre la compatibilité entre les différentes couches d'une application
- Enlève l'interdépendance entre couches
    - Facilite le refactoring
- Cf. [quand utiliser un DTO ?](https://github.com/uclouvain/osis/blob/dev/doc/dto.md#quand-utiliser-un-dto-)    


<br/><br/><br/><br/><br/><br/><br/><br/>






# Couche Infrastructure


## Repository (implémentation)

- Regroupe les **objets** qui implémentent les [interfaces IRepository](#dddrepository) pour les accès à la couche de persistence
- Chargée de persist / load les données : **il est le seul à connaître les Querysets Django**
- Hérite de [interfaces IRepository](#dddrepository)
- Nommage des fichiers : <objet_métier>.py
- Nommage des objets : <ObjetMetier>Repository
- Accès :
    - [couche Django Model](#modle-django-model)
    - [couche Domain](#ddddomain)
    - [couche Builder](#dddbuilder)

Exemple :
```python
# ddd/repository/training.py
from ddd.logic.training_bounded_context.repository import TrainingIRepository

class TrainingRepository(TrainingIRepository):
    """Chargé d'implémenter les fonctions fournies par TrainingIRepository."""
    pass
 
```









<br/><br/><br/><br/><br/><br/><br/><br/>



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


## Permissions
- Voir [Osis-role](https://github.com/uclouvain/osis/blob/dev/osis_role/README.md)
- Lorsqu'une view nécessite des permissions d'accès spécifiques (en dehors des permissions fournies par Django) : 
    - créer un décorateur dans le dossier `app_django/views/perms`
    - exemple : `base/views/learning_units/perms/`
    
<br/><br/>

## PDF
- Utiliser WeasyPrint ou pour la création de documents PDF (https://weasyprint.org/)
- Utilisation de ReportLab dépréciée (car compliqué d'utilisation)