
## Message bus


### Commands : rappel

- Représente les actions possibles d'un utilisateur
    - Fait partie entièrement du domaine
- Déclenche une modification dans notre domaine
- Une commande peut ne pas être "valide" pour notre domaine (cf. validateurs) 
    - Les paramètres d'une commande ne peuvent jamais être considérés comme une valeur "valide"
    - Le domaine ne peut pas s'y fier et doit valider les paramètres d'entrée
    - Interdit de passer des valeurs calculées "businessement" dans une commande
- "Appels de méthode sérialisables"
- Exemple :
```python

@attr.s(frozen=True, slots=True)
class CreateOrphanGroupCommand(interface.CommandRequest):
    code = attr.ib(type=str)
    year = attr.ib(type=int)
    type = attr.ib(type=str)
    abbreviated_title = attr.ib(type=str)
    title_fr = attr.ib(type=str)
    title_en = attr.ib(type=str)
    credits = attr.ib(type=int)
    constraint_type = attr.ib(type=str)
    min_constraint = attr.ib(type=int)
    max_constraint = attr.ib(type=int)
    management_entity_acronym = attr.ib(type=str)
    teaching_campus_name = attr.ib(type=str)
    organization_name = attr.ib(type=str)
    remark_fr = attr.ib(type=str)
    remark_en = attr.ib(type=str)
    start_year = attr.ib(type=int)
    end_year = attr.ib(type=Optional[int])
```

- Application service == command handlers (gestionnaire de commandes)

- Lorsqu'on cherche un use case (application service), on doit chercher sa commande correspondante
    - redondance
    - 1 commande == une action métier == 1 application service



<br/><br/><br/><br/><br/><br/><br/><br/>



### Message bus : Définition et objectifs


- Activer les actions correspondantes aux commandes
- Gérer les événements associés
- Structure préparée à la gestion des événements




#### Message bus : Implémentation

- Cf. [DisplayExceptionsByFieldNameMixin](https://github.com/uclouvain/osis/blob/dev/base/utils/mixins_for_forms.py#L35)
pour fonctions à redéfinir dans un Form

```python

class MessageBus:
    command_handlers = {
        command.CreateOrphanGroupCommand: lambda cmd: create_group_service.create_orphan_group(cmd, GroupRepository())
    }


#-------------------------------------------------------------------------------------------------------------------
# Django Form
class UpdateTrainingForm(DisplayExceptionsByFieldNameMixin, forms.Form):
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
    
    def get_command(self) -> CommandRequest:
        return CommandRequest(**self.validated_data)

```

- Implique
    - Injection des `Repository` dans les application services
    - Une action métier (commande) correspond à un application service (exécution de l'action)
        - 2 commandes == 2 actions métier différentes
            - Pas d'héritage de commande
            - Pas de réutilisation d'1 command dans 2 Application services

- Avantages
    - Views django : plus d'import d'application service, uniquement de commands
    - Tests unitaires facilités : injection `repository` en fonction de l'environnement
        - InMemoryRepository
        - PostgresRepository
        - ...
