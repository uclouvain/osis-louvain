## Serializers 


Confusion de l'équipe entr responsabilité de l'affichage et du domaine
Exemples : 
- DROI1BA[CEMS][TRANSITION] : affichage ? Domaine ?
    - réponse perso : attribut "sigle complet" du domaine
- "translate" dans les prérequis : And, et, or, ou... : affichage ? domaine ?


- [???] Ou gérer les traductions ?

- Single respojsibility principle
def __gt__(self, other):
    return other.year > self.year


- W5? Bounded contexts
    - [ALES] ApplicationService peutil appeler plusieurs repositories de plusieurs domaines différents ?


- Ajouter une classe RequiredBoostrapField pour les "*" - si required=False à tous les forms


- TODO :: comment gérer injection enttiy dans UE ? Repository pour ValueObject ? 



### Rapports
- Rapports (warnings, changes...) et events

## Et si mon domaine ne peut pas être complet à cause des performances ?
## Et si mon use case nécessite des actions métier sur plusieurs aggrégats ?

- Utiliser un DomainService
- Si un rapport est nécessaire : utiliser 
TODO :: implémenter fonction pour try except les BusinessException de plusieurs actions métier pour en faire un rapport

- Quid par rapport à DomainObject.report ?

```python

class UpdateTraining(interface.DomainService):
    def update(
            self,
            training: Training,
            command: UpdateTrainingCommand,
            repository: TrainingRepository
    ) -> None:
        business_exceptions = []
        if repository.acronym_exists(command.acronym):
            business_exceptions.append(AcronymAlreadyExistsException())

        try:
            training.update(command)
        except MultipleBusinessExceptions as e:
            business_exceptions += e.exceptions
        if business_exceptions:
            raise MultipleBusinessExceptions(exceptions=business_exceptions)


```

