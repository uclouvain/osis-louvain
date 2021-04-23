

# Partie 2 : DDD

## Différence entre "domain service" et "application service"

### Différence principale
- Les "domain services" contiennent de la logique métier alors que les "application services" n'en contiennent pas

### Application service
- Un application service représente un service qui effectue une action métier complète
- Use case : given - when - then facilement identifiable
- Orchestre les appels dans les différentes couches (Repository, Domaine, DomaineService)
- Cf. [Couche "use case" (application service)](https://github.com/uclouvain/osis/blob/dev/.github/CONTRIBUTING.md#dddservice-application-service)



### Domain service
- Un domain service est un service qui encapsule une logique métier qui ne sait pas être représenté par un Entity ou à un ValueObject,
et qui ne représente pas un cas d'utilisation en tant que tel
- Quand utiliser un DomainService ?
    - Le plus rarement possible ! (Plus le domaine est [pure et complet](#application_service_vs_domain_service.md),
     moins les DomainServices sont utiles)
        - Lorsque le use case nécessite une logique métier à travers plusieurs RootEntity (aggrégats)
        - Lorsque notre domaine ne peut pas être "complet" à cause des performances
            - Exemple : Vérifier si l'email d'un utilisateur existe (charger la liste de tous les utilisateurs en mémoire serait trop couteux)
        - Lorsque notre use case est dépendant d'un service technique / extérieur au domaine
            - Exemple : Générer un numéro de séquence pour une entité du domaine (dépendance externe : base de données)
            - Exemple : Attacher un groupement dans le contenu d'une formation n'est possible que si le cache contient un groupement et peut être vidé (dépendance externe : système de cache)
            - Exemple : Calculer la date de fin de report d'une formation (dépendance externe : gestion des événements académiques)
        - Lorsque notre use case se comporte différemment en fonction du résultat d'un service extérieur
            - Exemple codé : 

```python
import attr
from decimal import Decimal
from osis_common.ddd import interface
from external.dependency.gateway import payment_gateway

# Domain
@attr.s(slots=True)
class ATM(interface.RootEntity):
    """Distributeur automatique de billets"""
    commission = attr.ib(type=Decimal)

    def calculate_amount_with_commission(self, amount: Decimal) -> Decimal:
        """Calcule le montant additionné de la commission propre à l'ATM"""
        return amount + self.commission


#-----------------------------------------------------------------------
# Application Service


# Application service (use case)
def withdraw_money(amount: Decimal) -> interface.EntityIdentity:
    """Retirer de l'argent sur un distributeur automatique de billets"""
    repository = ATMRepository()
    atm = repository.get()  # distributeur automatique de billets

    # Charge le montant avec une commission pour le facturer à travers un gateway
    amount_with_commission = atm.calculate_amount_with_commission(amount)
    result = payment_gateway.charge_payment(amount_with_commission)  # dépendance externe

    if result.is_failure():
        # Logique métier : ce "if" décide si l'argent sera finalement retiré de l'ATM ou non. 
        raise interface.BusinessException("Couldn't charge the payment from the gateway")
    
    atm.dispense_money(amount)
    
    repository.update(atm)
    
    return atm.entity_identity
    
```

<br/><br/>

- NB : plus la logique métier est isolée (encapsulée dans le domaine = domaine COMPLET), moins il y aura de domain services


<br/><br/><br/><br/><br/><br/><br/><br/>



- Solution : Domain service

```python
from decimal import Decimal
from osis_common.ddd import interface
from external.dependency.gateway import payment_gateway


# Application service
def withdraw_money(amount: Decimal) -> interface.EntityIdentity:
    repository = ATMRepository()
    atm = repository.get()  # distributeur automatique de billets
    AtmWithdrawMoney.withdraw_money(atm, amount, payment_gateway)
    repository.update(atm)
    
    return atm.entity_identity


# Domain service
class AtmWithdrawMoney(interface.DomainService):
    def withdraw_money(self, atm: ATM, amount: Decimal, payment_gateway) -> None:
        # Charge le montant avec une commission pour le facturer à travers un gateway
        amount_with_commission = atm.calculate_amount_with_commission(amount)
        result = payment_gateway.charge_payment(amount_with_commission)  # dépendance externe
    
        if result.is_failure():
            # Logique métier : ce "if" décide si l'argent sera finalement retiré de l'ATM ou non. 
            raise interface.BusinessException("Couldn't charge the payment from the gateway")
        
        atm.dispense_money(amount)


    
```


<br/><br/><br/><br/><br/><br/><br/><br/>


## Questions

- Puis-je appeler un application service dans un domain service ?
- Puis-je appeler un Domain service dans un application service ?
- Le code suivant est-il pure ?

```python
from ddd.domain.formation_enrollment import STATE1, STATE4, STATE8
from osis_common.ddd import interface

# Repository
class FormationEnrollmentRepository(interface.AbstractRepository):

    def search_enrollments_by_student(self, student_identity: StudentIdentity) -> List[FormationEnrollmentEntity]:
        data_from_db = EnrollmentDatabaseDjangoModel.objects.filter(
            student__registration_id=student_identity.registration_id,
            enrollment_state__in=[STATE1, STATE4, STATE8],
        )
        return [FormationEnrollmentEntity(...obj) for obj in data_from_db]



#-----------------------------------------------------------------------

# ApplicationService
def search_enrollments_of_student(cmd: interface.CommandRequest) -> List[FormationEnrollmentEntity]:
    student_identity = StudentIdentity(cmd.registration_id)
    return FormationEnrollmentRepository().search_enrollments_by_student(student_identity)

```


<br/><br/><br/><br/><br/><br/><br/><br/>


- Réponses :
    - Non. Dans l'architecture en oignon, la couche ApplicationService connaît la couche DomainService, et non l'inverse 
    - Oui. Un DomainService encapsule une logique métier qui interragit avec des dépendances extérieures, nécessaire
    dans le cadre d'une Use case (ApplicationService)
    - Non. Le filtre `enrollment_state__in=[STATE1, STATE4, STATE8]` représente de la logique métier. À encapsuler 
    dans le domaine (ou dans un DomainService)


## Exercices

Les éléments suivants sont-ils réellement des DomainService ? Pourrait-on s'en passer ? Notre domaine est-il pure et/ou complet ?
- program_management.ddd.domain.service.has_specific_version_with_greater_end_year.HasSpecificVersionWithGreaterEndYear
- program_management.ddd.domain.service.get_last_existing_version_name.GetLastExistingVersion
- program_management.ddd.domain.service.generate_node_code.GenerateNodeCode
- program_management.ddd.domain.service.calculate_end_postponement.CalculateEndPostponement
- program_management.ddd.domain.service.get_node_publish_url.GetNodePublishUrl
- program_management.ddd.domain.service.validation_rule.FieldValidationRule
