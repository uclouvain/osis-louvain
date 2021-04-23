
## Bounded Context

- "Partie définie du logiciel dans laquelle des termes, définitions et règles particulières s'appliquent de manière cohérente"

- Cf. https://martinfowler.com/bliki/BoundedContext.html

- Dans Osis, l'UE a-t-elle une définition exactement la même dans les contextes suivants ?
    - "UE" dans le catalogue de formation
    - "UE" dans parcours
    - "UE" dans attribution

- Exemples de bounded contexts :
    - Catalogue de formations
    - Parcours
    - Inscription centrale
    - Admission d'un étudiant

- Bounded context = design from scratch



<br/><br/><br/><br/><br/><br/><br/><br/>



## Et pour les éléments de même définition à travers les bounded contexts ?

### Shared Kernel

- Regroupe les objets réutilisables à travers les bounded contexts
    - Souvent des ValueObjects

- Exemples :
    - IbanAccount
    - Language
    - Country
    - ...

- Attention : un shared kernel est difficile à faire évoluer car utilisé dans TOUS les bounded contexts 
