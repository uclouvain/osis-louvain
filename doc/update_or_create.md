# Update or create ?

## Besoin métier

- En tant qu'utilisateur facultaire, je veux recopier une formation et son contenu de l'année N vers N+1.
- Si ma formation existe déjà, il faut la mettre à jour (sinon, la créer).


## Implémentation existante

```python

# Application service
@transaction.atomic()
def copy_training_to_next_year(cmd: CommandRequest) -> EntityIdentity:
    # GIVEN
    existing_training = TrainingRepository().get(
        entity_id=TrainingIdentity(acronym=copy_cmd.acronym, year=copy_cmd.postpone_from_year)
    )
    existing_training_next_year = TrainingRepository().get(
        entity_id=existing_training.get_identity_for_next_year()
    )
    
    # WHEN
    new_training_next_year = TrainingBuilder().copy_to_next_year(existing_training, existing_training_next_year)

    # THEN
    try:
        with transaction.atomic():
            identity = repository.create(new_training_next_year)
    except exception.TrainingAcronymAlreadyExistException:
        identity = repository.update(new_training_next_year)

```


## Questions : 

- Le update or create est-il une règle métier ?
- Notre EntityRoot (formation) est-elle en état consistant ?
- Quelle couche est responsable de la persistence des données ?


<br/><br/><br/><br/><br/><br/><br/><br/>


## Responsabilité : le repository

- Il est le seul à pouvoir déterminer si un aggrégat (EntityRoot) existe ou non en base de données
- Nouvelle fonction : Repository.save()
- Fonctions à déprécier : 
    - Repository.create()
    - Repository.update()
- Avantages :
    - Encapsulation de la logique de persistence dans la couche Repository
    - Facilité d'utilisation du Repository par nos Application services
        - Pas d'ambiguïté : dois-je create ou dois-je update mon aggregate ?



<br/><br/><br/><br/><br/><br/><br/><br/>


## Solution

```python

# Application service
@transaction.atomic()
def copy_training_to_next_year(cmd: CommandRequest) -> EntityIdentity:
    # GIVEN
    existing_training = TrainingRepository().get(
        entity_id=TrainingIdentity(acronym=copy_cmd.acronym, year=copy_cmd.postpone_from_year)
    )
    existing_training_next_year = TrainingRepository().get(
        entity_id=existing_training.get_identity_for_next_year()
    )
    
    # WHEN
    new_training_next_year = TrainingBuilder().copy_to_next_year(existing_training, existing_training_next_year)

    # THEN
    identity = TrainingRepository().save(new_training_next_year)
    return identity

```

