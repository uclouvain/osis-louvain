Feature: Recherche des entités.

  Background:
    Given La base de données est dans son état initial.
    And L'utilisateur est loggé en tant que gestionnaire facultaire
    And Aller sur la page de recherche d'entité

  Scenario Outline: 39.40.41. En tant que gestionnaire facultaire ou central, je recherche une entité par <search_field>.
    When Encoder la valeur <search_value> dans la zone de saisie <search_field>
    And Cliquer sur le bouton Rechercher entité (Loupe)

    Then Dans la liste des entités, le(s) premier(s) « Sigle » est(sont) bien <results>.

    Examples:
      | results | search_field        | search_value                      |
      | ESPO    | acronym             | ESPO                              |
      | ESPO    | title               | Faculté des sciences économiques  |
      | DEXT    | entity_type         | Secteur                           |
