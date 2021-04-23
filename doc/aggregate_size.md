
## Taille d'un agrégat (RootEntity)

- Rappel : un agrégat est un objet représentant un objet métier dans le domaine

- Rappel : un agrégat est public d'utilisation (accessible par les couches ayant accès à la couche "domaine")

- Un agrégat définit la limite d'une transaction dans notre application
    - Toute modification d'un agrégat **doit** être consistant en tout temps
    - Pas possible de persister un agrégat en plusieurs fois (transactions)

<br/><br/><br/><br/><br/><br/><br/><br/>

- Un grand agrégat 
    - amène la simplicité
        - plus facile d'assurer la consistance des invariants métier car par de dépendances externes
    - au détriment des performances
        - nécessaire de charger plus de données pour assurer la consistance des invariants
    - Domaine "complet" **au détriment des performances**

<br/><br/><br/><br/><br/><br/><br/><br/>

- Un petit agrégat 
    - amène la performance
        - possibilité de modifier les petits agrégats simultanément
        - pas besoin de charger toute la 
    - au détriment de la simplicité
        - la logique est séparée dans différents agrégats
        - dépendances externes dans les services (plus compliqué)
    - Application performante **au détriment d'un domaine "complet"**

<br/><br/><br/><br/><br/><br/><br/><br/>

- Taille d'un agrégat peut être influencée par le métier : 
    - Exemple : Un groupement peut-il exister sans ProgramTree ?
        - Oui -> transactions différentes : groupement peut être séparé de l'agrégat
    - Exemple : Les liens entre groupements peuvent-ils exister sans ProgramTree ?
        - Non -> transaction commune : les liens font partie intégrante du ProgramTree

<br/><br/><br/><br/><br/><br/><br/><br/>


## Conclusion (pour Osis)
- Privilégier les grands agrégats au détriment des performances
- Plusieurs agrégats possibles dans un même domaine
    - Note : un nombre grandissant d'agrégats dans un même domaine est signe que notre domaine 
    vise une problématique métier trop large

