## Appliquer les validateurs avant ou après exécution d'une action métier de l'objet du domaine ?

- Effectuer toujours les validations **AVANT** d'effectuer l'action métier sur l'objet
    - évite d'avoir un objet du domaine en état inconsistant (garantit qu'un objet du domaine est toujours consistant)
    - facilite les tests unitaires
    - exemple : je ne peux modifier une UE que si son année académique est >= 2019
        - si validation après : 
            - UE modifiée --> état inconsistant --> difficulté de maintenance

- Note : un validateur ne peut jamais modifier les arguments qu'il reçoit pour sa propre validation
    - Exemple (**à éviter**) : `self.transition_name = "TRANSITION " + transition_name` (https://github.com/uclouvain/osis/pull/9680/files#)
    - Exemple (**à éviter**) : `self.field_to_validate = str(field_to_validate)`
    - Solution : Utiliser la librairie [python attrs](https://www.attrs.org/en/stable/) pour les validateurs


```python
import attr
from base.ddd.utils.business_validator import BusinessValidator


@attr.s(frozen=True, slots=True)
class MyBusinessValidator(BusinessValidator):
    object_used_for_validation = attr.ib(type=Union[RootEntity, Entity, ValueObject, PrimitiveType])
    other_object_used_for_validation = attr.ib(type=Union[RootEntity, Entity, ValueObject, PrimitiveType])

    def validate(self):
        self.object_used_for_validation = ...  # Will raise an exception due to frozen=True
        if self.object_used_for_validation != self.other_object_used_for_validation:
            raise MyOwnValidatorBusinessException()

```



<br/><br/><br/><br/><br/><br/><br/><br/>




## BusinessValidator : frozen=True ? Quid des propriétés calculées ?

- Si une propriété ne doit être calculée qu'une seule fois : sandwich pattern.
    - À calculer au départ de la fonction "validate" **dans le domaine**
    - Propriété (variable) à passer en paramètre de chaque sous fonction, qui seront "statiques"
        - Car ne modifie pas l'état de l'objet

```python

@attr.s(frozen=True, slots=True)
class ComplexBusinessValidator(BusinessValidator):

    root_entity = attr.ib(type=RootEntity)
    attr2 = attr.ib(type=PrimitiveType)
    attr3 = attr.ib(type=PrimitiveType)
    attr4 = attr.ib(type=PrimitiveType)

    def validate(self, *args, **kwargs):
        complex_result = self.root_entity._complex_computation()
        other_result = self.some_computation(complex_result)
        another_result = self.some_other_computation(complex_result)
        # if ... raise ...
        
    @staticmethod
    def some_computation(complex_result):
        pass
            
    @staticmethod
    def some_other_computation(complex_result):
        pass    

```




<br/><br/><br/><br/><br/><br/><br/><br/>



## Quid des validateurs dans les forms par rapport aux validateurs du domaine ?

### Validations effectuées dans les forms

- Types de champs ("nettoyage" des données sérialisées venant du request.POST)
- Champs requis
- Liste de choix / choix multiples


<br/><br/><br/><br/><br/><br/><br/><br/>



### Proposition 1 : valider ces champs en dehors de nos ApplicationService

Avantages :
- Réutilisation aisée des outils externes de validation (Django forms, ...)

Inconvénients :
- Duplication : ces validations devront être répétées pour chaque client 
- Exemples de client : 
    - Forms / Views Django
    - API
    - Scripts
- Rend notre domaine **incomplet** : la logique métier est séparée de notre domaine
- Difficulté de testing : métier à tester dans 2 couches différentes



<br/><br/><br/><br/><br/><br/><br/><br/>



### Proposition 2 : valider ces champs dans notre commande

Avantages : 
- Moins de duplication : tout client faisant appel à cette même action (Command) aura les mêmes validations

Inconvénients :
- Duplication : toute action métier (Command) plus large qui englobe cette action devra dupliquer ces mêmes validations
    - Exemple : CreateOrphanGroupCommand, CreateTrainingWithOrphanGroupCommand, CreateMiniTrainingWithOrphanGroupCommand
- Rend notre domaine **incomplet** : la logique métier est séparée de notre domaine
- Nécessite l'implémentation d'un mapping Command.errors <-> Form.errors
- Difficulté de testing : métier à tester dans 2 couches différentes
- Validation déclarative (et non impérative)
    - `if command.is_valid(): ...`


<br/><br/><br/><br/><br/><br/><br/><br/>



### Proposition 3 : valider ces champs dans notre domaine (ValidatorList)

Avantages : 
- Aucune duplication
- Domaine complet
- Facilité de testing (toute la logique est au même endroit)
- Validation impérative (validation automatique lors de l'action sur l'objet du domaine)

Inconvénients :
- Demande un mapping de nos types de BusinessException avec les clients des ApplicationService (django Forms, API...)
- Pas possible de valider l'ensemble des invariants en même temps ("rapport")
    - Exemple : Je ne peux pas valider que mes crédits > 0 si le champ crédits = "Mauvaise donnée" ou crédits = None



<br/><br/><br/><br/><br/><br/><br/><br/>



### "Two steps validation" : Data contracts VS Invariant Validation

- "Data contract" (Input Validation)
    - Validation des données entrées par le client (tout processus externe)
    - Mécanisme protégeant notre système contre les infiltrations de données invalides
    - Objet autorisé en état invalide (avec données invalides)
    - "Bouclier de protection contre le monde extérieur"
    - Inclus **uniquement** les validations suivantes : 
        - Type de champ (Integer, Decimal, String...)
        - Required
        - Énumérations

- "Invariant validation"
    - Validation des invariants
    - Suppose que les données à l'intérieur du système sont dans un état valide
    - "Bouclier" de prévention pour s'asurer de la consistance de nos objets
    - Inclus toutes les validations qui ne sont pas des "data contract"



<br/><br/><br/><br/><br/><br/><br/><br/>



## Comment afficher les BusinessExceptions (invariants) par champ dans un form ? Comment éviter de s'arrêter à la 1ère exception ? Et comment afficher toutes les erreurs au client ?

### Principe du "Fail fast"

- Stopper l'opération en cours dès qu'une erreur inattendue se produit
- Objectif : application plus stable
    - Limite le temps de réaction pour corriger un bug
        - Erreur rapide = stacktrace = rollback (si activé) = information d'une erreur au plus tôt (à l'utilisateur)
    - Empêche de stocker des données en état inconsistant
    - Principe opposé : fail-silently (try-except)
- Exemple dans Osis : les validateurs
    - Tout invariant métier non respecté lève immédiatement une `BusinessException`



<br/><br/><br/><br/><br/><br/><br/><br/>



### Solution : ValidatorList + TwoStepsMultipleBusinessExceptionListValidator + DisplayExceptionsByFieldNameMixin

- Faire hériter nos ValidatorLists de `TwoStepsMultipleBusinessExceptionListValidator` (implémentation ci-dessous)
    - Toute règle métier (Validator) raise une `BusinessException`
    - Toute action métier (application service) raise une MultipleBusinessExceptions (ValidatorList)
    - Toute MultipleBusinessExceptions gérable par le client (view, API...)

- Utiliser `DisplayExceptionsByFieldNameMixin` dans nos Django forms


<br/><br/><br/><br/><br/><br/><br/><br/>



```python

#-------------------------------------------------------------------------------------------------------------------
# ddd/service/write 
def update_training_service(command: UpdateTrainingCommand) -> 'TrainingIdentity':
    identity = TrainingIdentity(acronym=command.acronym, year=command.year)
    
    training = TrainingRepository().get(identity)
    training.update(command)
    
    TrainingRepository().save(training)
    
    return identity


#-------------------------------------------------------------------------------------------------------------------
# ddd/validators/validators_by_business_action.py
@attr.s(frozen=True, slots=True)
class UpdateTrainingValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    command = attr.ib(type=CommandRequest)
    existing_training = attr.ib(type=Training)
    existing_training_identities = attr.ib(type=List[TrainingIdentity])

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        # Devrait être toujours valide via client Django Form, car validé via Parsley
        return [
            AcronymRequiredValidator(self.command.acronym),
            TypeChoiceValidator(self.command.type),
            # ...
        ]

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            HopsValuesValidator(self.existing_training),
            StartYearEndYearValidator(self.existing_training),
            UniqueAcronymValidator(self.command.acronym, self.existing_training_identities),
            # ...
        ]



#-------------------------------------------------------------------------------------------------------------------
# Django Form
class UpdateTrainingForm(ValidationRuleMixin, DisplayExceptionsByFieldNameMixin, forms.Form):
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

    def call_application_service(self):
        command = ...
        return update_training_service(command)


#-------------------------------------------------------------------------------------------------------------------
# Django View
class CreateTrainingView(generics.View):

    def post(self, *args, **kwargs):
        form = CreateTrainingForm(request.POST)
        # if form.is_valid():
        form.save()  # Appelle form.is_valid()
        if not form.errors:
            return success_redirect()
        return error_redirect()

```


<br/><br/><br/><br/><br/><br/><br/><br/>



## Validateurs génériques

- (à implémenter et à intégrer dans la lib DDD)
    - RequiredFieldsValidator
    - MaximumValueValidator
    - MinimumValueValidator
    - MaximumLengthValidator
    - MinimumLengthValidator
    - StringFormatValidator (regex)
    - ... à compléter ? 



<br/><br/><br/><br/><br/><br/><br/><br/>



### Quid de Parsley ? Si on "mappe" toutes nos erreurs à partir de nos validateurs ?

Rappel :

- Validation en direct (HTML5 / ajax)
- Basée sur les Django Form fields

Décision pour Osis :

- Dupliquer UNIQUEMENT les "data contract validations", càd :
    - Type de champ dans les Form (CharField, IntegerField...)
    - Required
    - Énumérations
    - ValidationRulesMixin
    - PermissionFieldMixin (FieldReference)


<br/><br/><br/><br/><br/><br/><br/><br/>



## Quid de ValidationRules et FieldReference ? Dans quelle(s) couche(s) devraient-ils se trouver ?
### Rappel : ValidationRules
- Django Model qui sauvegarde en DB des règles de validations (métier et affichage) par champs de formulaires
- Validation et affichage varient en fonction du l'état d'une donnée (par exemple, le type d'une UE)
- Variations possibles :
    - (métier) champ requis ou non
    - (métier) champ à valeur fixée (valeur par défaut bloquée et non éditable)
    - (métier) champ avec validation "regex"
    - (affichage) champs avec valeur par défaut
    - (affichage) champs avec help text (exemple)
    - (affichage) champs avec place holder (espace réservé)
- Initialisé à partir de `validation_rules.csv`
- Exemple : 
```python

ValidationRule(
    model='base_validationrule',
    pk="TrainingForm.AGGREGATION.acronym",  # field reference
    status_field="REQUIRED",  # NOT_REQUIRED - FIXED - ALERT_WARNING - DISABLED
    field_initial_value="2A",
    regex_rule="^([A-Za-z]{2,4})(2)([Aa])$",
    regex_error_message='Error message validation for regex rule',
    help_text_en="""
        Acronym of Aggregation is composed of:
        <ul>
        <li>2-4 letters + <b>2A</b></li>
        </ul>
        Examples: <i>ARKE2A, BIOL2A, HIST2A</i
    """,
    help_text_fr="""
        Sigle d’une Agrégation est composé de:
        <ul>
        <li>2-4 lettres + <b>2A</b></li>
        </ul>
        Exemples: <i>ARKE2A, BIOL2A, HIST2A</i>
    """,
    placeholder="Ex: BIOL2A",
)
```


<br/><br/><br/><br/><br/><br/><br/><br/>


### ValidationRules : Intégration dans le DDD et dans les forms

- À réutiliser dans
    - dans les `BusinessValidator` dans notre domaine (domaine complet)
    - dans les Django Forms (existe déjà - `ValidationRuleMixin`)

- Différence avec l'utilisation d'aujourd'hui :
    - le nommage des champs stockés dans `validation_rules.csv` seront des **termes métier du domaine**

- Exemple : 
```python

ValidationRule(
    model='base_validationrule',
    
    # DIFFERENCE : 
    pk="TrainingDomainObject.AGGREGATION.acronym",  # field reference

    status_field="REQUIRED",  # NOT_REQUIRED - FIXED - ALERT_WARNING - DISABLED
    field_initial_value="2A",
    regex_rule="^([A-Za-z]{2,4})(2)([Aa])$",
    regex_error_message='Error message validation for regex rule',
    help_text_en="""
        Acronym of Aggregation is composed of:
        <ul>
        <li>2-4 letters + <b>2A</b></li>
        </ul>
        Examples: <i>ARKE2A, BIOL2A, HIST2A</i
    """,
    help_text_fr="""
        Sigle d’une Agrégation est composé de:
        <ul>
        <li>2-4 lettres + <b>2A</b></li>
        </ul>
        Exemples: <i>ARKE2A, BIOL2A, HIST2A</i>
    """,
    placeholder="Ex: BIOL2A",
)
```

- Notes :
    - Mécanisme permettant de réutiliser des mêmes règles côté backend et côté frontend
        - NB : Si `backend Django` + `frontend Angular` ==> règles seraient dupliquées
    - Ce sont les forms qui devront s'adapter au format utilisé par notre domaine (et non l'inverse)
    - Les validation rules ne seront peut-être plus réutilisées à l'avenir
        - Utile uniquement pour formulaires massifs et complexes
        - À négocier avec le métier et les analystes : 
            - Tout doit-il faire partie d'une seule transaction (taille des aggrégats) ?
            - Peut-on découper notre domaine ?



<br/><br/><br/><br/><br/><br/><br/><br/>



### Rappel : FieldReference

- Django Model qui sauvegarde des règles de validations (métier et affichage) de champs de formulaires en DB
- Permet l'édition ou non des champs d'un formulaire en fonction :
    - du rôle de l'utilisateur (central, facultaire... - nécessite l'accès aux groupes / permissions)
    - du contexte (événement académique, type d'UE) :
- Initialisé à partir de `field_reference.json`
- Exemple :
```json
[
  {
      "fields": {
          "field_name": "acronym",
          "context": "TRAINING_DAILY_MANAGEMENT",
          "content_type": [
              "base",
              "educationgroupyear"
          ],
          "groups": [
              [
                  "central_managers"
              ]
          ]
      },
      "model": "rules_management.fieldreference"
  },  
  {
        "fields": {
            "field_name": "repartition_volume_additional_entity_1",
            "context": "EXTERNAL_PARTIM",
            "content_type": [
                "base",
                "learningcomponentyear"
            ],
            "groups": [
                [
                    "central_managers_for_ue"
                ]
            ]
        },
        "model": "rules_management.fieldreference"
    }
]
```


<br/><br/><br/><br/><br/><br/><br/><br/>



### FieldReference : Intégration dans le DDD et dans les forms

- À réutiliser
    - dans les DomainService
    - dans les Django Forms (existe déjà - `PermissionFieldMixin`)


#### :question: pourquoi ne pas réutiliser FieldReference dans nos validateurs (domaine) plutôt que dans un DomainService ?


- Différence avec l'utilisation d'aujourd'hui :
    - le nommage des champs stockés dans `field_reference.json` seront des **termes métier du domaine**

- Exemple :
```json
[
  {
      "fields": {
          "field_name": "acronym",
          "context": "TRAINING_DAILY_MANAGEMENT",
          "content_type": [
              // DIFFERENCE
              "TrainingDomainObject",
              ""
          ],
          "groups": [
              [
                  "central_managers"
              ]
          ]
      },
      "model": "rules_management.fieldreference"
  },  
  {
        "fields": {
            // DIFFERENCE
            "field_name": "additional_entity_1.repartition_volume",
            "context": "EXTERNAL_PARTIM",
            "content_type": [
              // DIFFERENCE
              "LearningUnitDomainObject",
              ""
            ],
            "groups": [
                [
                    "central_managers_for_ue"
                ]
            ]
        },
        "model": "rules_management.fieldreference"
    }
]
```


- Notes :
    - Mécanisme permettant de réutiliser des mêmes règles côté backend et côté frontend
        - NB : Si `backend Django` + `frontend Angular` ==> règles seraient dupliquées
    - Ce sont les forms qui devront s'adapter au format utilisé par notre domaine (et non l'inverse)
    - Les FieldReference ne seront peut-être plus réutilisées à l'avenir
        - Utile uniquement pour formulaires massifs et complexes
        - À négocier avec le métier et les analystes : 
            - Tout doit-il faire partie d'une seule transaction (taille des aggrégats) ?
            - Peut-on découper notre domaine ?


