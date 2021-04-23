## [W2] Formation 2

- Partie 1 
    - Théorie
        - Domaine "pure" et domaine "complet"
        - Pattern "Sandwich"
    - Workshop
        - Sur base du code dans "program_management" :
            - Déterminer si notre domaine est "pure" et/ou "complet"
        - Sur base du code du workshop 1 :
            - Refactorer notre code (UE) pour le rendre "pure" (si nécessaire)
            - Refactorer notre code (UE) pour le rendre "complet" (si nécessaire)
        - Use case 1 : En tant qu'utilisateur facultaire, je veux supprimer une UE
- Partie 2
    - Théorie
        - Différence entre un DomainService et un ApplicationService
        - Taille et dépendances entre agrégats
    - Workshop
        - Refactoring UE : vérification des "DomainService" et "ApplicationService"
        - Use case 2 : En tant qu'utilisateur facultaire, je veux créer un Partim
        - Use case 3 : En tant qu'utilisateur facultaire, je veux créer les parties magistrales et pratiques d'un partim


-------------------------------


## Cas d'utilisation 1
### user story
En tant qu'utilisateur facultaire, je veux supprimer une UE

### business rules
- Je ne peux pas supprimer l'UE si 
    - je suis hors de la période "gestion journalière" du calendrier académique
    - l'UE est utilisée dans un programme type


## Cas d'utilisation 2
### user story
En tant qu'utilisateur facultaire, je veux créer un partim

### business rules
 
- (repris du workshop 1) Règle business supplémentaire pour UE : L'entité responsable
    - Doit être une entité liée à l'utilisateur
    - Doit respecter une des 2 conditions 
        - être de type SECTOR, FACULTY, SCHOOL, DOCTORAL_COMMISSION
        - avoir un sigle = ILV, IUFC, CCR ou LLL
- Un partim possède les mêmes champs qu'une UE, mais les champs suivants sont hérités de l'UE
    - Sigle (de l'UE)
    - Année académique
    - Type
    - Sous-type de stage
    - Intitulé commun (fr)
    - Intitulé commun (en)
    - Entité responsable du cahier des charges
- Je ne peux pas créer un Partim "orphelin" (un partim doit être lié à une UE)
- Le sigle d'un partim est le même que celui d'une UE, suffixée obligatoirement par 1 lettre
- Je ne peux pas créer un partim si son sigle existe déjà
- La valeur initiale des "crédits" doit être la même que celle de l'UE (mais peut être changée)



## Cas d'utilisation 3
### user story
En tant qu'utilisateur facultaire, je veux créer les parties magistrales et pratiques d'un partim (en même temps que le partim)

### business rules
- Même chose que pour la création des parties magistrales et pratiques d'une UE
- Le volume de chaque composant, pour chaque quadrimestre, doit être <= volume de l'UE complète sur le partim

