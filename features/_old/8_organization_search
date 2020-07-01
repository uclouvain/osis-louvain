Feature: Recherche des organisations.

  Background:
    Given La base de données est dans son état initial.
    And L'utilisateur est loggé en tant que gestionnaire d'institution.
    And Aller sur la page de recherche d'organisations

  Scenario Outline: 42.43.44. En tant que gestionnaire facultaire ou central, je recherche une organisation par <search_field>.
    When Encoder la valeur <search_value> dans la zone de saisie <search_field>
    And Cliquer sur le bouton Rechercher organisation (Loupe)

    Then Dans la liste des organisations, le(s) premier(s) « Sigle » est(sont) bien <results>.

    Examples:
      | results | search_field  | search_value  |
      | UCL     | acronym       | UCL           |
      | UCL     | name          | UCLouvain     |
      | UCL     | type          | Principale    |
