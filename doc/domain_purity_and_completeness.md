# DDD : domaine "pure" et domaine "complet"

## Domaine complet : définition

- Un domaine est complet ssi il contient toute la logique métier de l'application

- Cas d'utilisation : modifier l'email d'un utilisateur

```python
from osis_common.ddd import interface
import attr

# Domain
@attr.s(slots=True)
class Company(interface.Entity):
    domain_name = attr.ib(type=str)
    
    def is_email_corporate(self, email: str) -> bool:
        email_domain = email.split('@')[1]
        return email_domain == self.domain_name


@attr.s(frozen=True, slots=True)
class UserIdentity(interface.Entity):
    username = attr.ib(type=str)


@attr.s(slots=True)
class User(interface.RootEntity):
    entity_identity = attr.ib(type=UserIdentity)
    company = attr.ib(type=Company)
    email = attr.ib(type=str)

    def change_email(self, new_email: str):
        if not self.company.is_email_corporate():
            raise interface.BusinessException("Incorrect email domain")
        self.email = new_email



#_____________________________________________________________________________________


# Application Service
def change_email_service(cmd: interface.CommandRequest) -> 'interface.EntityIdentity':
    repository = UserRepository()
    # Given
    user = repository.get(UserIdentity(username=cmd.username))
    
    # When
    user.change_email(new_email=cmd.email)

    # Then
    repository.update(user)
    
    return user.entity_identity
```

- "Domain logic fragmentation" est l'opposé d'un domaine complet : lorsque la logique métier (ici, `is_email_corporate`)
appartient à une autre couche que le domaine métier (couche de services, couche repository...)


<br/><br/><br/><br/><br/><br/><br/><br/>



## Domaine pure : définition

- Un domaine est "pure" ssi
    - il n'a aucune dépendance externe ou à d'autres couches de code
    - il dépend uniquement de types primitifs ou d'autres classes du domaines


- "Dépendance externe" signifie tout service (classe, fonction...) à connotation technique qui ne fait pas partie intégrante du domaine. Exemples :
    - base de données
    - gestion de fichiers
    - envoi de mail
    - envoi de messages (queues)

- Cas d'utilisation : règle métier : interdit de modifier si l'email existe déjà

- Essai n°1 : vérifier cette règle dans l'application service
```python
from osis_common.ddd import interface
import attr

# Application Service
def change_email_service(cmd: interface.CommandRequest) -> 'interface.EntityIdentity':
    repository = UserRepository()
    # Given
    if repository.search(email=new_email):
        raise interface.BusinessException("Email already exists")

    user = repository.get(UserIdentity(username=cmd.username))
    
    # When
    user.change_email(new_email=cmd.email)

    # Then
    repository.update(user)
    
    return user.entity_identity

```


- Notre implémentation rend-elle notre domaine pure ?
- Notre implémentation rend-elle notre domaine complet ?


<br/><br/><br/><br/><br/><br/><br/><br/>

- Essai n°2 : Injection du repository dans le domain

```python
from osis_common.ddd import interface
import attr

# Domain
@attr.s(slots=True)
class User(interface.Entity):
    entity_identity = attr.ib(type=UserIdentity)
    company = attr.ib(type=Company)
    email = attr.ib(type=str)

    def change_email(self, new_email: str, repository: UserRepository):
        if not self.company.is_email_corporate():
            raise interface.BusinessException("Incorrect email domain")
        if repository.search(email=new_email):
            raise interface.BusinessException("Email already exists")
        self.email = new_email



# Application Service
def change_email_service(cmd: interface.CommandRequest) -> 'interface.EntityIdentity':
    repository = UserRepository()
    # Given
    user = repository.get(UserIdentity(username=cmd.username))
    
    # When
    user.change_email(new_email=cmd.email, repository=repository)

    # Then
    repository.update(user)
    
    return user.entity_identity

```

- Notre implémentation rend-elle notre domaine pure ?
- Notre implémentation rend-elle notre domaine complet ?
 


<br/><br/><br/><br/><br/><br/><br/><br/>


- Essai n°3 : passer la liste des utilisateurs existants à notre domaine

```python
from osis_common.ddd import interface
import attr

# Application Service
def change_email_service(cmd: interface.CommandRequest) -> 'interface.EntityIdentity':
    repository = UserRepository()
    # Given
    all_users = repository.search()
    user = repository.get(UserIdentity(username=cmd.username), all_users=all_users)
    
    # When
    user.change_email(new_email=cmd.email)

    # Then
    repository.update(user)
    
    return user.entity_identity


# Domain
@attr.s(slots=True)
class User(interface.Entity):
    entity_identity = attr.ib(type=UserIdentity)
    company = attr.ib(type=Company)
    email = attr.ib(type=str)

    def change_email(self, new_email: str, all_users: List['User']):
        if not self.company.is_email_corporate():
            raise interface.BusinessException("Incorrect email domain")
        if new_email in {u.email for u in all_users}:
            raise interface.BusinessException("Email already exists")
        self.email = new_email

```

<br/><br/>

- Notre implémentation rend-elle notre domaine pure ?
- Notre implémentation rend-elle notre domaine complet ?
- Quel inconvénient à cette solution ? 

<br/><br/><br/><br/><br/><br/><br/><br/>


## Trilemme

- Il est impossible de satisfaire les 3 concepts suivants : 
    - Domaine complet
    - Domaine pure
    - Performance

- Choix possibles :

**1.** Placer toutes les opérations de lecture et écritures aux limites d'une opération métier (sandwich pattern)
    
- Domaine "pure" et "complet" **au détriment des performances**

**2.** Partager la logique métier entre le domaine et l'application service

- Domaine "pure" et performances **au détriment d'un domaine "complet"**

**3.** Injecter les dépendances hors processus dans le domaine

- Domaine "complet" et performances **au détriment d'un domaine "pure"**

<br/><br/>

- Décision : 
    - Toujours privilégier un domaine "pure" et "complet" **au détriment des performances** (**1.**)

<br/><br/>

- Et si j'ai des problèmes de performances ?
    - Privilégier un domaine "pure" et une application performante (**2.**)
        - Il est plus facile de maintenir un "domain logic fragmentation" plutôt que des dépendances externes (mocks, etc.)

        
<br/><br/><br/><br/><br/><br/><br/><br/>


## Questions

- Puis-je faire des `try-except` dans un application service ?
- Puis-je placer un `if` dans un application service ?
- Puis-je lancer une BusinessException dans un application service ?


<br/><br/><br/><br/><br/><br/><br/><br/>

- Réponse aux 3 questions :
    - Non. Aucune logique n'est permise dans l'application service. Si la logique ne peut pas être contenue dans
    le domaine (car cela le rendrait impure ou incomplet), encapsuler la logique dans un DomainService.
    - Cf. [Application service vs Domain service](#application_service_vs_domain_service.md)

<br/><br/><br/><br/><br/><br/><br/><br/>


## Exercices dans le code : domaines pures et/ou complets ?

- program_management.ddd.service.write.create_standard_program_tree_service.create_standard_program_tree
- program_management.ddd.service.write.paste_element_service.paste_element
- program_management.ddd.service.write.update_program_tree_version_service.update_program_tree_version
- education_group.ddd.service.write.delete_orphan_training_service.delete_orphan_training
- education_group.ddd.service.write.copy_training_service.copy_training_to_next_year
- program_management.ddd.service.write.up_link_service.up_link
- education_group.ddd.service.write.update_group_service.update_group
