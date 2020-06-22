Feature: Recherche des unités d'enseignements.

  Background:
    Given L'utilisateur est loggé en tant que gestionnaire
    And Aller sur la page de recherche d'UE
    And Réinitialiser les critères de recherche

  Scenario: En tant que gestionnaire, je recherche une UE par code
    When Encoder le code d'une UE
    And Cliquer sur le bouton Rechercher (Loupe)
    Then La liste de résultat doit correspondre aux crières de recherche

  Scenario: En tant que gestionnaire facultaire ou central, je recherche des UEs par type
    When Encoder le type d'UE
    And Cliquer sur le bouton Rechercher (Loupe)
    Then La liste de résultat doit correspondre aux crières de recherche

  Scenario: En tant que gestionnaire facultaire ou central, je recherche des UEs par entité
    When Encoder l'entité d'UE
    And Cliquer sur le bouton Rechercher (Loupe)
    Then La liste de résultat doit correspondre aux crières de recherche

#  TODO Should verify by going into attribution of one learning unit
#  Scenario: En tant que gestionnaire facultaire ou central, je recherche des UEs par enseignant
#    When Encoder l'enseignant d'UE
#    And Cliquer sur le bouton Rechercher (Loupe)
#    Then La liste de résultat doit correspondre aux crières de recherche

  Scenario: En tant que gestionnaire facultaire ou central, je recherche des UE pour produire un Excel
    When Encoder le code d'une UE
    And Cliquer sur le bouton Rechercher (Loupe)
    Then La liste de résultat doit correspondre aux crières de recherche
    When Ouvrir le menu « Exporter »
    And Sélection « Liste personnalisée des unités d’enseignement »
    And Cocher les cases « Programmes/regroupements » et « Enseignant(e)s »
    And Cliquer sur « Produire Excel »
    Then Le fichier excel devrait être présent