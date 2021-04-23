## [W4] Formation 4

- Théorie : les validateurs, questions posées :
    - Appliquer les validateurs avant ou après modification de l'objet du domaine?
    - Quid des validateurs dans les forms par rapport aux validateurs du domaine?
    - Comment afficher les BusinessExceptions dans les champs des forms ? Et comment génération un rapport avec toutes les erreurs ? Comment éviter de s'arrêter à la 1ère exception ?
    - Validateurs forms <-> domaine ?
        - Comment afficher tous les messages d'erreurs d'une action plutôt que de s'arrêter à la première ?

- Workshop :
    - Refactoring de notre code (UE) :
        - Utiliser attr pour nos validateurs et ValidatorList
    - Use case : En tant qu'utilisateur, je veux afficher toutes les erreurs en une seule fois (à l'écran - dans les champs de formulaire)
        - Créer une View (CreateLearningUnitView) + Form + url
    - (reprise du workshop 4) : Use case : créer les parties magistrales et pratiques d'une UE


## Cas d'utilisation
### user story
En tant qu'utilisateur facultaire, je veux afficher toutes les erreurs en une seule fois (à l'écran - dans les champs de formulaire)
### business rules
- Lorsque je soumets n'importe quel formulaire (création d'une UE, création d'un partim, suppression d'une UE...)
- Associer les erreurs métier aux champs du formulaire (CreateLearningUnitForm)

