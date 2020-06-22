Feature: Modification de programme

  Background:
    Given La base de données est dans son état initial.
    And les flags d'éditions des offres sont désactivés.

  Scenario: En tant que gestionnaire central, je dois pouvoir ajouter une UE de type mémoire dans les mémoires du tronc commun d’une offre.
    Given L'utilisateur est loggé en tant que gestionnaire central

    Given Aller sur la page de detail d'une formation en année académique courante
    When Cliquer sur le menu « Actions »
    And Ouvrir l'arbre
    And Ouvrir l'entiereté de l'arbre
    And Sélectionner un tronc commun dans l'arbre
    When Offre cliquer sur le menu « Actions »
    And Offre Cliquer sur l'action recherche rapide
    And Selectionner l'onglet d'unité d'enseignement
    And Offre Encoder le code d'une UE
    And Cliquer sur le bouton Rechercher (recherche rapide)
    And Selectionner le premier resultat (recherche rapide)
    And Cliquer sur Ajouter (recherche rapide)
    And Cliquer sur « Enregistrer » dans la modal
    Then Vérifier que l'UE se trouve bien dans l'arbre
