Feature: Mise à jour en gestion journalière

  Background:
    Given La base de données est dans son état initial.
    And les flags d'éditions des UEs sont désactivés.
    And La période de modification des unités d'enseignement est en cours

    # TODO Modify cms data + attribution

  Scenario: En tant que gestionnaire facultaire, je ne peux pas modifier les UE d'une autre fac.
    Given L'utilisateur est loggé en tant que gestionnaire facultaire
    And Aller sur la page de detail d'une UE ne faisant pas partie de la faculté
    When Cliquer sur le menu « Actions »
    Then L’action « Modifier » est désactivée.

  Scenario: En tant que gestionnaire facultaire, je dois pouvoir mettre à jour une UE de ma fac.
    Given L'utilisateur est loggé en tant que gestionnaire facultaire
    And Aller sur la page de detail d'une UE faisant partie de la faculté
    When Cliquer sur le menu « Actions »
    And Cliquer sur le menu « Modifier »
    And Le gestionnaire faculatire remplit le formulaire d'édition des UE
    And Cliquer sur le bouton « Enregistrer »
    And A la question, « voulez-vous reporter » répondez « non »
    Then Vérifier UE a été mis à jour

  Scenario: En tant que gestionnaire central, je dois pouvoir mettre à jour une UE.
  Description : en particulier les crédits et la périodicité + vérifier que les UE peuvent
  être mises à jour par la gestionnaire central en dehors de la période de modification des programmes.
    Given L'utilisateur est loggé en tant que gestionnaire central
    And Aller sur la page de detail d'une UE faisant partie de la faculté

    When Cliquer sur le menu « Actions »
    And Cliquer sur le menu « Modifier »
    And Le gestionnaire central remplit le formulaire d'édition des UE
    And Cliquer sur le bouton « Enregistrer »
    And A la question, « voulez-vous reporter » répondez « oui »

    Then Vérifier UE a été mis à jour

  Scenario: En tant que gestionnaire facultaire, je dois pouvoir créer un nouveau partim.
    Given L'utilisateur est loggé en tant que gestionnaire facultaire
    And Aller sur la page de detail d'une UE faisant partie de la faculté
    When Cliquer sur le menu « Actions »
    And Cliquer sur le menu « Nouveau partim »
    And Le gestionnaire faculatire remplit le formulaire de création de partim
    And Cliquer sur le bouton « Enregistrer » pour partim

    Then Vérifier que le partim a bien été créé

  Scenario: En tant que gestionnaire facultaire, je dois pouvoir créer un autre collectif
    Given L'utilisateur est loggé en tant que gestionnaire facultaire

    Given Aller sur la page de recherche d'UE
    When Cliquer sur le menu « Actions » depuis la recherche
    And Cliquer sur le menu « Nouvelle UE »

    Then Le gestionnaire central remplit le formulaire de création d'autre collectif
    And Cliquer sur le bouton « Enregistrer » de la création

    Then Vérifier que l'UE a bien été créé
