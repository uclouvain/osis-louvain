## [W3] Formation 3

- Finalisation des uses cases 1 + 2 + 3 (workshop 2)
- Théorie
    - Update or create ?
    - Design patterns "Factory" et "Builder"
- Workshop
    - Question : notre LearningUnitRepository.get() respecte-t-il nos guidelines ?
    - Refactoring UE : éviter la duplication de code qui instancie notre LearningUnit 
        - instancié dans repository
        - instancié dans le domaine
    - Demande métier supplémentaire
    - Use case 1 : En tant qu'utilisateur facultaire, je veux recopier une UE vers l'année suivante
    - Use case 2 : En tant qu'utilisateur facultaire, je veux prolonger une UE jusqu'à N+6

-------------------------------
## Demande métier supplémentaire
- Création d'une UE : sous-type stage obligatoire si type=stage, sinon vide obligatoire


## Cas d'utilisation 1
### user story
En tant qu'utilisateur facultaire, je veux recopier une UE vers l'année suivante

### business rules
- Interdit de recopier si : 
    - l'UE existe déjà l'année suivante (sigle, année)
    - si sa date de fin d'enseignement est dépassée


## Cas d'utilisation 2
### user story
En tant qu'utilisateur facultaire, je veux prolonger une UE jusqu'à N+6

### business rules
- Le "N" de "N+6" représente l'année académique officielle (14/09/X -> 13/09/X+1) en cours

