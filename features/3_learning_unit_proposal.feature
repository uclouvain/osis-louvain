Feature: Propositions d’UE

  Background:
    Given La base de données est dans son état initial.
    And LCHIM1141 est en proposition en 2019-20 lié à CHIM
    Given L’utilisateur est dans le groupe faculty manager

  Scenario: 20 : En tant que gestionnaire facultaire, je dois pouvoir rechercher des propositions par sigle ou numéro de dossier.
    Given L’utilisateur est attaché à l’entité MED
    Given L’utilisateur est attaché à l’entité CHIM
    And Aller sur la page de recherche d'UE
    And Sélectionner l’onglet « Propositions »
    And Réinitialiser les critères de recherche

    When Encoder 2019-20 comme Anac.
    And Encoder LCHIM1141 comme Code
    And Cliquer sur le bouton Rechercher (Loupe)
    Then Dans la liste de résultat, le(s) premier(s) « Code » est(sont) bien LCHIM1141.

    Given Réinitialiser les critères de recherche
    When Encoder 2019-20 comme Anac.
    And  Encoder CHIM comme Sigle dossier
    And Cliquer sur le bouton Rechercher (Loupe)
    Then Dans la liste de résultat, le(s) premier(s) « Code » est(sont) bien LCHIM1141.

  Scenario: 21 : En tant que gestionnaire facultaire, je dois pouvoir rechercher des propositions par entité de charge.
    And Les propositions LDROI1003, doivent être attachées à DRT en 2019-20
    Given L’utilisateur est attaché à l’entité DRT

    And Aller sur la page de recherche d'UE
    And Sélectionner l’onglet « Propositions »
    And Réinitialiser les critères de recherche

    When Encoder 2019-20 comme Anac.
    And Encoder DRT comme Ent. charge
    And Encoder LDROI1 comme Code
    And Cliquer sur le bouton Rechercher (Loupe)

    Then Dans la liste de résultat, le(s) premier(s) « Code » est(sont) bien LDROI1003.

  Scenario: 22 : En tant que gestionnaire facultaire, je dois pouvoir rechercher des propositions et produire un Excel.
  Description : Recherche des propositions + produire l’Excel

  Scenario: 23 : En tant que gestionnaire facultaire, je dois pouvoir faire une proposition de création.
    Given L’utilisateur est attaché à l’entité DRT
    And Aller sur la page de recherche d'UE

    When  Cliquer sur le menu « Actions »
    And Cliquer sur le menu Proposition de création
    And  Encoder LDROI1234 comme Code
    And  Encoder Cours comme Type
    And  Encoder 5 comme Crédits
    And  Encoder Cours de droit comme Intitulé commun
    And  Encoder Louvain-la-Neuve - UCLouvain comme Lieu d’enseignement
    And  Encoder DRT comme Entité resp. cahier des charges
    And  Encoder DRT comme Entité d’attribution
    And  Encoder 2019-20 comme Année académique
    And  Encoder DRT1234 comme Dossier

    Then  Vérifier que la zone Etat est bien grisée
    And la valeur de Etat est bien Faculté
    And Cliquer sur le bouton « Enregistrer »

    Then  Vérifier que la unité d'enseignement LDROI1234 a bien été mise en proposition pour l'année 2019-20

    Given Aller sur la page de recherche d'UE
    And Sélectionner l’onglet « Propositions »
    And Réinitialiser les critères de recherche

    When Encoder 2019-20 comme Anac.
    And Encoder LDROI1234 comme Code
    And Encoder DRT comme Ent. charge
    And Cliquer sur le bouton Rechercher (Loupe)
    Then Dans la liste de résultat, le(s) premier(s) « Code » est(sont) bien LDROI1234.

    Given Aller sur la page de recherche d'UE
    And Réinitialiser les critères de recherche

    When Encoder 2019-20 comme Anac.
    And Encoder LDROI1234 comme Code
    And Encoder DRT comme Ent. charge
    And Cliquer sur le bouton Rechercher (Loupe)
    Then Dans la liste de résultat, le(s) premier(s) « Code » est(sont) bien LDROI1234.

  Scenario: 24 : En tant que gestionnaire facultaire, je dois pouvoir faire une proposition de modification.
    Given L’utilisateur est attaché à l’entité DRT
    And Aller sur la page de detail de l'ue: LDROI1006 en 2019-20

    When Cliquer sur le menu « Actions »
    And Cliquer sur le menu « Mettre en proposition de modification »

    When Encoder 4 comme Crédits
    And Encoder bisannuelle paire comme Périodicité
    And Encoder DRT4321 comme Dossier
    Then Vérifier que la zone Etat est bien grisée
    And Vérifier que la zone Type est bien grisée

    When Cliquer sur le bouton « Enregistrer »
    Then Vérifier que une proposition de Modification a été faite pour l'unité d'enseignement LDROI1006
    And Vérifier que le champ Crédits est bien 4
    And Vérifier que la Périodicité est bien bisannuelle paire


  Scenario: 25 : En tant que gestionnaire facultaire, je dois pouvoir faire une proposition de fin d’enseignement.
    Given L’utilisateur est attaché à l’entité DRT
    And Aller sur la page de detail de l'ue: LDROI1007 en 2019-20

    When Cliquer sur le menu « Actions »
    And Cliquer sur le menu « Mettre en proposition de fin d’enseignement »

    When Encoder 2020-21 comme Anac de fin
    When Encoder DRT5678 comme Dossier

    Then Vérifier que la zone Etat est bien grisée
    And Vérifier que la zone Type est bien grisée

    When Cliquer sur le bouton « Oui, je confirme »

    Then Vérifier que une proposition de Suppression a été faite pour l'unité d'enseignement LDROI1007
    And Vérifier que l'année academique termine en 2020-21

  Scenario Outline: 26 : En tant que gestionnaire facultaire, je dois pouvoir modifier une proposition.

    Given L'ue LDROI1234 en 2019-20 et liée à DRT est en proposition de création
    Given L'ue LDROI1006 en 2019-20 et liée à DRT est en proposition de modification
    Given L'ue LDROI1007 en 2019-20 et liée à DRT est en proposition de suppression

    Given L’utilisateur est attaché à l’entité DRT

    And Aller sur la page de detail de l'ue: <acronym> en <year>
    When Cliquer sur le menu « Actions »
    And Cliquer sur « Modifier la proposition »
    And Encoder <value> comme <field>
    And Cliquer sur le bouton « Enregistrer »
    Then Vérifier que une proposition de <proposal_type> a été faite pour l'unité d'enseignement <acronym>
    And Vérifier que le champ <field> est bien <value>
    Examples:
      | acronym   | year    | proposal_type | field            | value   |
      | LDROI1234 | 2019-20 | Création      | Crédits          | 6       |
      | LDROI1006 | 2019-20 | Modification  | Crédits          | 6       |
      | LDROI1007 | 2019-20 | Suppression   | Année academique | 2021-22 |


  Scenario Outline: 27 : En tant que gestionnaire facultaire, je dois pouvoir annuler une proposition.
  Description :
  Annuler la proposition de création du scénario #23
  Annuler la proposition de modification du scénario #24
  Annuler la proposition de modification de fin d’enseignement du scénario #25

    Given L'ue LDROI1234 en 2019-20 et liée à DRT est en proposition de création
    Given L'ue LDROI1006 en 2019-20 et liée à DRT est en proposition de modification
    Given L'ue LDROI1007 en 2019-20 et liée à DRT est en proposition de suppression

    And L’utilisateur est attaché à l’entité DRT
    And Aller sur la page de recherche d'UE
    And Sélectionner l’onglet « Propositions »
    And Réinitialiser les critères de recherche

    When Encoder <year> comme Anac.
    And Encoder <acronym> comme Code
    And Cliquer sur le bouton Rechercher (Loupe)
    Then Dans la liste de résultat, le(s) premier(s) « Code » est(sont) bien <acronym>.

    When Sélectionner le premier résultat
    And Cliquer sur « Retour à l’état initial »
    And Cliquer sur « Oui » pour retourner à l'état initial
    Then Vérifier que la proposition <acronym> a été annulée avec succès.

    Examples:
      | acronym   | year    |
      | LDROI1234 | 2019-20 |
      | LDROI1006 | 2019-20 |
      | LDROI1007 | 2019-20 |


  Scenario Outline: 28 : En tant que gestionnaire central, je dois pouvoir consolider une proposition.
    Given L'ue LDROI1234 en 2019-20 et liée à DRT est en proposition de création
    Given L'ue LDROI1006 en 2019-20 et liée à DRT est en proposition de modification
    Given L'ue LSINF1121 en 2019-20 et liée à EPL est en proposition de suppression
    Given S’assurer que la date de fin de LSINF1121 est 2020-21.

    Given L’utilisateur est dans le groupe central manager
    And L’utilisateur est attaché à l’entité DRT
    And L’utilisateur est attaché à l’entité EPL
    And Aller sur la page de detail de l'ue: <acronym> en <year>
    When Cliquer sur le menu « Actions »
    And Cliquer sur « Modifier la proposition »
    And Encoder Accepté comme Etat
    And Cliquer sur le bouton « Enregistrer »

    And Aller sur la page de recherche d'UE
    And Sélectionner l’onglet « Propositions »
    And Réinitialiser les critères de recherche

    When Encoder <year> comme Anac.
    And Encoder <acronym> comme Code
    And Cliquer sur le bouton Rechercher (Loupe)

    Then Vérifier que le dossier <acronym> est bien Accepté
    When Sélectionner le premier résultat
    And Cliquer sur « Consolider »
    And Cliquer sur « Oui » pour consolider
    Then Vérifier que la proposition <acronym> a été consolidée avec succès.

    And Aller sur la page de recherche d'UE
    And Réinitialiser les critères de recherche

    When Encoder <year> comme Anac.
    And Encoder <acronym> comme Code
    And Cliquer sur le bouton Rechercher (Loupe)
    Then Vérifier que <acronym> n'est pas en proposition.

    Examples:
      | acronym   | year    | proposal_type |
      | LDROI1234 | 2019-20 | Création      |
      | LDROI1006 | 2019-20 | Modification  |
      | LSINF1121 | 2019-20 | Suppression   |
