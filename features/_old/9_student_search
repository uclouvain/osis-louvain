Feature: Recherche des organisations.

  # FIXME Should not create user with permission
  Background:
    Given La base de données est dans son état initial.
    And L'utilisateur a la permission can_access_student.
    And Aller sur la page de recherche d'étudiants

  Scenario Outline: 45. Je recherche un étudiant par <search_field>.
    When Encoder la valeur <search_value> dans la zone de saisie <search_field>
    And Cliquer sur le bouton Rechercher étudiant (Loupe)

    Then Dans la liste des étudiants, le(s) premier(s) « Noma » est(sont) bien <results>.

    Examples:
      | results      | search_field    | search_value  |
      | 21301400     | registration_id | 21301400      |

  Scenario Outline: 46. Je recherche un étudiant par <search_field>.
    When Encoder la valeur <search_value> dans la zone de saisie <search_field>
    And Cliquer sur le bouton Rechercher étudiant (Loupe)

    Then Dans la liste, le « Nom » <search_value> est bien présent partout dans la colonne des noms.

    Examples:
      | search_field    | search_value  |
      | name            | Martin        |
