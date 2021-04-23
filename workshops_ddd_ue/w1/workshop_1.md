
## [W1] Formation 1

- Rappels théoriques :
    - DDD : définition, objectif, philosophie, couches, ValueObject <-> Entity
    - CQS : définition, exemple, avantages
- Workshop
    - Objectif : développer ensemble les uses cases suivants dans le DDD avec nos guidelines d'aujourd'hui
    - Use case 1 : En tant qu'utilisateur facultaire, je veux créer une UE
    - Use case 2 : En tant qu'utilisateur facultaire, je veux créer les parties magistrales et pratiques d'une UE



-------------------------------

## Cas d'utilisation 1
### user story
En tant qu'utilisateur facultaire, je veux créer une UE

### business rules
- Je peux encoder
    - année académique
    - intitulé commun en fr
    - intitulé spécifique en fr
    - intitulé commun en anglais
    - intitulé spécifique en anglais
    - sigle
    - crédits
    - type (Cours, stage, mémoire, autre collectif, autre individuel, thèse)
    - sous-type de stage (stage d'enseignement, stage clinique, stage professionnel, stage de recherche)
    - l'entité responsable (du cahier des charges) qui possède un sigle, un intitulé et une adresse
    - périodicité
    - langue
    - remarque de la faculté (non publiée)
    - remarque pour publication
    - remarque pour publication (en anglais)

- Je ne peux pas créer une unité d'enseignement dont l'année académique < 2019-20
- Tous les champs sont obligatoires, sauf
    - les 3 remarques
    - "intitulé commun en anglais"
    - "intitulé spécifique en anglais"
- sous-type stage obligatoire si type=stage, sinon vide obligatoire
- Crédits > 0
- Le calendrier académique de l'événement "gestion journalière" doit être ouvert à la date du jour (sans quoi je ne peux pas créer une UE)
- L'entité responsable
    - Doit être une entité liée à l'utilisateur
    - Doit respecter une des 2 conditions 
        - être de type SECTOR, FACULTY, SCHOOL, DOCTORAL_COMMISSION
        - avoir un sigle = ILV, IUFC, CCR ou LLL
- Je ne peux pas créer une UE dont le sigle existe déjà (sur n'importe quelle année)
- La langue doit être "français" par défaut
- La périodicité doit être "Annuelle" par défaut
- Le code doit être composé en 3 parties : 
    - Le site (1 lettre)
    - Partie alphabétique (2 à 4 lettres)
    - Partie numérique (4 chiffres - dont 1er != 0)


## Cas d'utilisation 2
### user story
En tant qu'utilisateur facultaire, je veux créer les parties magistrales et pratiques d'une UE

### business rules
- Valeurs concernées
    - année académique
    - sigle (PP, PM)
    - volume Q1
    - volume Q2
    - volume annuel
    - quadrimestre (Q1&Q2, Q1ORQ2, etc.)
- Volume annuel == Q1 + Q2
- Si partie pratique alors sigle == PP
- Si partie magistrale (théorique) alors sigle == PM
- Les volumes Q1 et Q2 ne doivent être remplis que s'ils correspondent à la valeur indiquée dans Quadrimestre
    - Exemple : si quadrimestre == Q1, alors Q1 est obligatoire, Q2 doit être vide
    - Exemple : si quadrimestre == Q1AndQ2, alors Q1 et Q2 sont obligatoires
