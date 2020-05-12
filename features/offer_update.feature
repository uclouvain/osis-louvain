Feature: Modification d'offre

  Background:
    Given La base de données est dans son état initial.
    And les flags d'éditions des offres sont désactivés.

  Scenario: En tant que gestionnaire central, je dois pouvoir mettre une fin d’enseignement
    Given L'utilisateur est loggé en tant que gestionnaire central
    Given Aller sur la page de detail d'une formation en année académique courante
    When Offre cliquer sur le menu « Actions »
    When Cliquer sur « Modifier »
    And Encoder année de fin
    And Offre cliquer sur le bouton « Enregistrer »
    And Si une modal d'avertissement s'affiche, cliquer sur « oui »

    Then Vérifier que la dernière année d'organisation de la formation a été mis à jour
