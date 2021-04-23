Pour les units tests : 
- FakeRepositories, injectés dans les services
- FakeRepo des tests des services "write" chargent des données prédéfinies d'office
    - Via fixture, factory... ou autre
    - ce qui fait plusieurs cas de données pour un même use case
        - implique d'office un subtest qui itère sur tous les objets du métier


## Tests unitaires [W6]

Comment découpler/structurer les tests unitaires ? (Nomenclature, quand utiliser TestCase ou SimpleTestCase...)
Doit-on tester couche par couche et utiliser des mocks ?

Comment tester les Django forms? (Note : quid du "doublon" entre les validateurs des forms et les validateurs métier)
Commenter tester les views Django ?
Commenter tester les serializers (API) ?
Comment tester le DDD (repository, domain...) ==> Faut-il vraiment créer des FakeRepo? Ne faudrait-il pas simplement une seul fixture (ou Factory, exemple : DROI2MFactory) de test qui contient tous les cas possibles d'un domaine métier ? Et nos tests récupèreraient les données àpd de cette fixture, plutôt que de créer tout le temps les mêmes setUp pour chaque test unitaire ?

# Notes existant dans guidelines (car à clarifier / étoffer):
Idéalement lorsqu'on teste une view, on doit vérifier :
- Le template utilisé (assertTemplateUsed)
- Les redirections en cas de succès/erreurs
- Le contenu du contexte utilisé dans le render du template
- Les éventuels ordres de listes attendus