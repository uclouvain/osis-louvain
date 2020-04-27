Feature: Propositions d’UE

  Background:
    Given La base de données est dans son état initial.
    And les flags d'éditions des UEs sont désactivés.
    And La période de modification des unités d'enseignement est en cours

  Scenario: En tant que gestionnaire central, je dois pouvoir consolider une proposition de création
    Given L'utilisateur est loggé en tant que gestionnaire central
    And Aller sur la page de recherche des propositions
    And Réinitialiser les critères de recherche
    And Rechercher propositions de création
    Then Sélectionner une proposition

    When Cliquer sur le menu « Actions »
    And Cliquer sur « Modifier la proposition »
    And Proposition encoder l'état Accepté
    And Proposition Cliquer sur le bouton « Enregistrer »
    Then Vérifier que la proposition est en état Accepté

    When Cliquer sur le menu « Actions »
    And Cliquer sur « Consolider »
    And Cliquer sur « Oui » pour consolider
    Then Vérifier que la proposition a été consolidée avec succès

 Scenario: En tant que gestionnaire central, je dois pouvoir consolider une proposition de suppression
    Given L'utilisateur est loggé en tant que gestionnaire central
    And Aller sur la page de recherche des propositions
    And Réinitialiser les critères de recherche
    And Rechercher propositions de suppression
    Then Sélectionner une proposition

    When Cliquer sur le menu « Actions »
    And Cliquer sur « Modifier la proposition »
    And Proposition encoder l'état Accepté
    And Proposition Cliquer sur le bouton « Enregistrer »
    Then Vérifier que la proposition est en état Accepté

    When Cliquer sur le menu « Actions »
    And Cliquer sur « Consolider »
    And Cliquer sur « Oui » pour consolider
    Then Vérifier que la proposition a été consolidée avec succès

Scenario: En tant que gestionnaire central, je dois pouvoir consolider une proposition de modification
    Given L'utilisateur est loggé en tant que gestionnaire central
    And Aller sur la page de recherche des propositions
    And Réinitialiser les critères de recherche
    And Rechercher propositions de modification
    Then Sélectionner une proposition

    When Cliquer sur le menu « Actions »
    And Cliquer sur « Modifier la proposition »
    And Proposition encoder l'état Accepté
    And Proposition Cliquer sur le bouton « Enregistrer »
    Then Vérifier que la proposition est en état Accepté

    When Cliquer sur le menu « Actions »
    And Cliquer sur « Consolider »
    And Cliquer sur « Oui » pour consolider
    Then Vérifier que la proposition a été consolidée avec succès
