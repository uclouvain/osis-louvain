Feature: Suppression d'offre.

  Background:
    Given La base de données est dans son état initial.
    And les flags d'éditions des offres sont désactivés.
    And L'utilisateur est loggé en tant que gestionnaire central

  Scenario: En tant que gestionnaire central, je dois pouvoir supprimer une offre.
    Given Aller sur la page Catalogue de formations / Formation
    And Offre réinitialiser les critères de recherche
    And Offre Cliquer sur le bouton Rechercher (Loupe)

    And Cliquer sur le premier sigle dans la liste de résultats
    When Offre cliquer sur le menu « Actions »
    And Cliquer sur « Supprimer »
    And Cliquer sur « Oui, je confirme »

    Given Aller sur la page Catalogue de formations / Formation
    And Offre Cliquer sur le bouton Rechercher (Loupe)
    Then Vérifier que l'offre n'apparaît plus dans la liste
