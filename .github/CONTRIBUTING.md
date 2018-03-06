### Lisibilité du code :
- Séparation des classes: deux lignes vides
- Séparation des methodes de class: une ligne vide
- Séparation des fonctions: deux lignes vides
- Le nom d'une fonction doit être explicite et claire sur ce qu'elle fait (un 'get_' renvoie un élément, un 'search_' renvoie une liste d'élements...)

### Documentation du code :
- Documenter les fonctions (paramètres, fonctionnement, ce qu'elle renvoie)
- Ne pas hésiter à laisser une ligne de commentaire dans le code, décrivant brièvement le fonctionnement d'algorithme plus compliqué/plus longs

### Clés de traduction :
- Toutes les variables et msgid (traduction) sont écrites en minuscules avec un '_' (underscore) comme séparateur 

### Réutilisation du code :
- Ne pas créer de fonctions qui renvoient plus d'un seul paramètre (perte de contrôle sur ce que fait la fonction et perte de réutilisation du code)
- Ne pas faire de copier/coller ; tout code dupliqué ou faisant la même chose doit être implémenté dans une fonction documentée qui est réutilisable
- Ne pas utiliser de 'magic_number' (constante non déclarée dans une variable). Par exemple, pas de -1, 1994, 2015 dans le code, mais déclarer en haut du fichier des variables sous la forme LIMIT_START_DATE=1994, LIMIT_END_DATE=2015, etc.

### Performance :
- Ne pas faire d'appel à la DB (pas de queryset) dans une boucle 'for' :
    - Récupérer toutes les données nécessaires en une seule requête avant d'effectuer des opérations sur les attributs renvoyés par le Queryset
    - Si la requête doit récupérer des données dans plusieurs tables, utiliser le select_related fourni par Django (https://docs.djangoproject.com/en/1.9/ref/models/querysets/#select-related)
    - Forcer l'évaluation du Queryset avant d'effectuer des récupération de données avec *list(a_queryset)* 

### Modèle :
- Chaque fichier décrivant un modèle doit se trouver dans le répertoire *'models'*
- Chaque fichier contenant une classe du modèle ne peut renvoyer que des instances du modèle qu'elle déclare. Autrement dit, un fichier my_model.py contient une classe MyModel() et des méthodes qui ne peuvent renvoyer que des records venant de MyModel
- Un modèle ne peut pas avoir un champs de type "ManyToMany" ; il faut toujours construire une table de liaison, qui contiendra les FK vers les modèles composant la relation ManyToMany.
- Lorsqu'un nouveau modèle est créé (ou que de nouveaux champs sont ajoutés), il faut penser à mettre à jour l'admin en conséquence (raw_id_fields, search_fields, list_filter...). 

### Business :
- Les fonctions propres à des fonctionnalités business (calculs de crédits ou volumes, etc.) doivent se trouver dans un fichier business. Ces fichiers sont utilisés par les Views et peuvent appeler des fonctions du modèle (et non l'inverse !). 
- Les fonctions business ne peuvent pas recevoir l'argument 'request', qui est un argument propre aux views.

### Migration :
- Ne pas utiliser le framework de persistence de Django lorsqu'il y a du code à exécuter dans les fichiers de migration. Il faut plutôt utiliser du SQL natif (voir https://docs.djangoproject.com/fr/1.10/topics/db/sql/ et https://docs.djangoproject.com/fr/1.10/ref/migration-operations/)

### Dépendances entre applications : 
- Ne pas faire de références des applications principales ("base" et "reference") vers des applications tierces (Internship, assistant...)
- Une application peut faire référence à une autre app' en cas de dépendance business (exemple: 'assessments' a besoin de 'attribution').

### Vue :
- Ne pas faire appel à des méthodes de queryset dans les views (pas de MyModel.filter(...) ou MyModel.order_by() dans les vues). C'est la responsabilité du modèle d'appliquer des filtres et tris sur ses queryset. Il faut donc créer une fonction dans le modèle qui renvoie une liste de records filtrés sur base des paramètres entrés (find_by_(), search(), etc.).
- Ajouter les annotations pour sécuriser les méthodes dans les vues (user_passes_tests, login_required, require_permission)
- Les vues servent de "proxy" pour aller chercher les données nécessaires à la génération des pages html, qu'elles vont chercher dans la couche "business" ou directement dans la couche "modèle". Elles ne doivent donc pas contenir de logique business

### Formulaire :
- Utiliser les objets Forms fournis par Django (https://docs.djangoproject.com/en/1.9/topics/forms/)

### Template (HTML)
- Privilégier l'utilisation Django-Bootstrap3
- Tendre un maximum vers la réutilisation des blocks ; structure :
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

### Sécurité :
- Ne pas laisser de données sensibles/privées dans les commentaires/dans le code
- Dans les URL (url.py), on ne peut jamais passer l'id d'une personne en paramètre (par ex. '?tutor_id' ou '/score_encoding/print/34' sont à éviter! ). 
- Dans le cas d'insertion/modification des données venant de l'extérieur (typiquement fichiers excels), s'assurer que l'utilisateur qui injecte des données a bien tous les droits sur ces données qu'il désire injecter. Cela nécessite une implémentation d'un code de vérification.

### Permissions :
- Lorsqu'une view nécessite des permissions d'accès spécifiques (en dehors des permissions frounies par Django), créer un décorateur dans le dossier "perms" des "views". Le code business propre à la permission devra se trouver dans un dossier "perms" dans "business". Voir "base/views/learning_units/perms/" et "base/business/learning_units/perms/".

### Pull request :
- Ne fournir qu'un seul fichier de migration par issue/branche (fusionner tous les fichiers de migrations que vous avez en local en un seul fichier)

### Ressources et dépendances :
- Ne pas faire de référence à des librairie/ressources externes ; ajouter la librairie utilisée dans le dossier 'static'
