Feature: Affichage en consultation

  Background:
    Given La base de données est dans son état initial.
    And L’utilisateur est dans le groupe faculty manager

  Scenario: 47. En tant que gestionnaire facultaire, je dois vérifier que les messages d'erreur pour les partims soient limités au partim lui-même et a son parent.
    Given Aller sur la page de detail de l'ue: LAGRE2020Q en 2019-20
    Then Vérifier le contenu des messages de warning affichés.
