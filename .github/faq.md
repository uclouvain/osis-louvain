## FAQ

Regroupe les questions dont les réponses ne peuvent pas être formalisée sous forme de guideline/règle stricte, 
mais plutôt sous forme de **philosophie de développement**.


<br/><br/><br/><br/>


#### :question: Quand doit-on appliquer le DDD ? Quid du CRUD ? Quid des views de recherche, fichiers excels, pdfs ?

Le DDD n'est pas une réponse à tout. Comme le décrit très bien l'article [Domain Driven Design : des armes pour affronter la complexité](https://blog.octo.com/domain-driven-design-des-armes-pour-affronter-la-complexite/),
il y a des avantanges et inconvénients.

Dans le cadre du projet Osis, nous privilégions - pour le moment - l'utilisation du DDD pour les services `Read` et `Write` pour 2 raisons :
- Détacher notre base de code au maximum de la DB et limiter les coût de refactoring : Osis étant la réécriture d'un projet Legacy, sa base de code et son modèle DB est en constante évolution
- Éviter d'intégrer trop de nouveaux concepts en même temps dans l'équipe et dans le projet

Si des problèmes de performances sont constatés, diverses solutions pourront être mises en place (lazy load, ORM/SQL pour les services `Read`...). 
Nous modifierons notre manière de travailler et adapterons nos guidelines en conséquence.


<br/><br/><br/><br/>


#### :question: L'analyse est en français, le code en anglais : comment traduire correctement le métier ?

L'objectif du DDD est, entre autres, de construire un langage commun à travers tous les intervenants d'un projet.

Le vocabulaire métier utilisé dans les analyses du métier est notre référence : 
les termes métier **en français** doivent donc être clairs et non ambigus pour le développeur.

Toute ambiguïté sur un terme métier nécessite clarification auprès de l'analyste / du métier.

**Pour la partie en anglais**, les développeurs doivent être d'accord sur un terme qui identifie clairement l'élément métier, l'objet, la variable... 
Si lors de la review, le reviewer comprend le code développé (assez explicite - correspondance évidente en français) : c'est un accord.
 > :information_source: [WordReference - Dictionnaire en ligne fournissant toutes les traductions possibles d'un mot en fonction de son contexte](https://www.wordreference.com/fr/)

<br/><br/><br/><br/>


#### :question: Par où commencer pour implémenter une fonctionnalité ? Comment savoir quel code va dans quelle couche ?

Certains développeront dans un fichier vide pour ensuite déplacer le code dans les couches adéquates, 
d'autres implémenteront directement le code dans les couches pertinentes...
Il n'existe pas de règle stricte qui définit par où démarrer le développement d'une fonctionnalité.
Commencez par ce qui vous semble le plus évident à faire.

- J'ai une règle / contrainte / invariant métier ? 
    - --> Couche du domaine
- J'ai besoin de sauvegarder / extraire des données en base de données ? (Querysets, ...)
    - --> Couche repository
- J'ai besoin de soumettre un formulaire ? 
    - --> Couche Form (pour le formulaire html)
    - --> Couche Command + application service (pour l'action métier - use case)
    - --> Couche Views (pour l'utilisation du form) 


<br/><br/><br/><br/>


#### :question: Jusqu'où doit-on modifier un code non lié à notre ticket ? 

Cf. [Boyscout rule](https://www.matheus.ro/2017/12/11/clean-code-boy-scout-rule/)

Attention à ne pas tomber dans l'excès, qui mènerait à une PR complexe et longue à reviewer, 
ou trop détachée de l'objectif original du ticket.

<br/><br/><br/><br/>


#### :question: Quid si un code "legacy" que je dois modifier ne respecte pas nos guidelines ?

Il est possible que certaines parties de code (plus anciennes) ne respectent pas l'ensemble de ces guidelines
(qui sont en constante évolutions - comme nos compétences). 
Si cet ancien code doit être modifié, ces guidelines restent d'application (dans la mesure du bon sens bien évidemment ; 
la correction d'un bug dans du code "non DDD" ne demande pas la réécriture complète du module en DDD). 

La mise en application de certaines guidelines dans un ancien code peut mener à du travail supplémentaire. 
Ce travail supplémentaire est un gain de temps pour tout prochain développeur qui rentrera dans cette partie du code.

Si vous ne le faites pas, c'est votre collègue qui perdra du temps.

<br/><br/><br/><br/>


#### :question: Comment savoir si je dois filtrer une liste d'objets en mémoire via le Domain/DomainService ou via Repository.search/filter (querysets) ?

Réponse courte : tendre vers des queries génériques, et n'aller dans les filtres spécifiques QUE s'il y a des problèmes de performances.

Raisons : 
- Plus une query est générique, plus elle sera réutilisée par nos services, plus le mécanisme de cache pourra jouer son rôle
- Moins il y a de filtres côté repository, plus il y a de filtres côté Domain/DomainService


Se poser les questions suivantes peut nous aider : 
    
- Est-ce que mon filtre correspond à du métier ?
- Est-ce que le nom de ma fonction est explicite ?
- Est-ce que ma fonction respecte le "single responsibility principle" ?

Plus il y a de paramètres pour filtrer des querysets dans un Repository, 
plus on se rapproche d'une fonction qui possède du métier.

Exemple : 

```python

class EnrollmentRepository(interface.AbstractRepository):
    
    # MAUVAIS car : 
    # 1. le filtre 'enrollment_state' correspond à du code "métier" 
    # (le repository ne peut pas déterminer lui-même quels sont les 'enrollment_state' pertinents à un use case) 
    # 2. le nom de la fonction 'search_enrollments_by_student' ne fait pas explicitement référence à 'enrollment_state'  
    def search_enrollments_by_student(self, student_identity: StudentIdentity) -> List[FormationEnrollmentEntity]:
        data_from_db = EnrollmentDatabaseDjangoModel.objects.filter(
            student__registration_id=student_identity.registration_id,
            enrollment_state__in=[STATE1, STATE4, STATE8],
        )
        return [FormationEnrollmentEntity(...obj) for obj in data_from_db]    
    
    # À éviter car : 
    # 1. le filtre 'enrollment_states' amène une query très spécifique et variable 
    def search_enrollments_by_student_and_enrollment_states(
            self,
            student_identity: StudentIdentity,
            enrollment_states: List[EnrollmentState]
    ) -> List[FormationEnrollmentEntity]:
        data_from_db = EnrollmentDatabaseDjangoModel.objects.filter(
            student__registration_id=student_identity.registration_id,
            enrollment_state__in={state.name for state in states},
        )
        return [FormationEnrollmentEntity(...obj) for obj in data_from_db]    
    
    # CORRECT car :
    # 1. Le filtre reste générique (mécanisme de cache plus aisé)
    # 2. Respecte le single responsibility principle (on ne filtre que par Student, on ne fait rien d'autre)
    def search_enrollments_by_student(
            self,
            student_identity: StudentIdentity
    ) -> List[FormationEnrollmentEntity]:
        data_from_db = EnrollmentDatabaseDjangoModel.objects.filter(
            student__registration_id=student_identity.registration_id,
        )
        # Filter on "pertinent" enrollment_states is made in memory, inside DomainService (or Domain)
        return [FormationEnrollmentEntity(...obj) for obj in data_from_db]

```
    
<br/><br/><br/><br/>


#### :question: Comment déterminer si une règle métier doit se trouver dans Osis-role ou dans le domaine DDD ?

- Si c'est une permission d'accès à une action (application service) dans le sens "puis-je ou non faire cette action?"
    - Osis-role
    - Exemples :
        - Je ne peux accéder à la fonctionnalité "X" que si je suis un utilisateur central
        - Je ne peux accéder à la modification d'une UE qui si son entité de charge fait partie des entités que je gère
        - Je ne peux accéder à la consultation des UEs que si j'ai la permission "can read learning unit"

- Si c'est une règle en rapport avec le calendrier académique
    - Osis-role
    - (mais théoriquement : dans le DDD)
    - Exemple : 
        - Je ne peux accéder à la modification d'une UE que si l'événement "gestion journalière" est ouvert

- Si c'est une règle en rapport avec le contenu des données postées (formulaire) par le client
    - Validation de contenu -> Invariant métier -> DDD (domaine - validator)
    - Exemple : 
        - Lorsque je crée une UE, son entité de charge doit être une entité qui fait partie des entités que je gère



<br/><br/><br/><br/>


#### :question: Quelle était l'arborescence des packages pour le catalogue de formations ?

```
django_app
 ├─ ddd
 |   ├─ command.py
 |   |
 |   ├─ domain
 |   |   ├─ exceptions.py  (exceptions business)
 |   |   ├─ <objet_métier>.py  (RootEntity)
 |   |   ├─ _entity.py (protected)
 |   |   ├─ _value_object.py (protected)
 |   |
 |   ├─ builder
 |   |   ├─ <objet_métier>_builder.py  (Builder pour RootEntity)
 |   |   ├─ <identité_objet_métier>_builder.py  (Builder pour EntityIdentity)
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
