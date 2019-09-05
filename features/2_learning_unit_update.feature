Feature: Mise à jour en gestion journalière

  Background:
    Given La base de données est dans son état initial.
    And les flags d'éditions des UEs sont désactivés.
    And L’utilisateur est dans le groupe faculty manager

  Scenario: 7. En tant que gestionnaire facultaire, je ne peux pas modifier uniquement les UE d'une autre fac.
    Given La période de modification des programmes est en cours
    And L’utilisateur est attaché à l’entité DRT
    Given Aller sur la page de detail de l'ue: LLSMS2000 en 2019-20
    When Cliquer sur le menu « Actions »
    Then L’action « Modifier » est désactivée.

  Scenario: 7. En tant que gestionnaire facultaire, je peux modifier uniquement les UE de ma FAC.
    Given La période de modification des programmes est en cours
    And L’utilisateur est attaché à l’entité DRT
    Given Aller sur la page de detail de l'ue: LDROI1004 en 2019-20
    When Cliquer sur le menu « Actions »
    Then L’action « Modifier » est activée.

  Scenario: 8. En tant que gestionnaire facultaire, je dois pouvoir mettre à jour une UE.
    Given La période de modification des programmes est en cours
    And L’utilisateur est attaché à l’entité DRT
    Given Aller sur la page de detail de l'ue: LDROI1004 en 2019-20
    When Cliquer sur le menu « Actions »
    And Cliquer sur le menu « Modifier »
    And Décocher la case « Actif »
    And Encoder Q1 et Q2 comme Quadrimestre
    And Encoder 1 comme Session dérogation
    And Encoder 30 comme volume Q2 pour la partie magistrale
    And Encoder 30 comme volume Q1 pour la partie magistrale
    And Encoder 6 comme volume Q1 pour la partie pratique
    And Encoder 6 comme volume Q2 pour la partie pratique
    And Cliquer sur le bouton « Enregistrer »
    And A la question, « voulez-vous reporter » répondez « non »

    Then Vérifier que le cours est bien Inactif
    And Vérifier que le Quadrimestre est bien Q1 et Q2
    And Vérifier que la Session dérogation est bien 1
    And Vérifier que le volume Q1 pour la partie magistrale est bien 30
    And Vérifier que le volume Q2 pour la partie magistrale est bien 30
    And Vérifier que le volume Q1 pour la partie pratique est bien 6
    And Vérifier que la volume Q2 pour la partie pratique est bien 6


  Scenario: 9. En tant que gestionnaire central, je dois pouvoir mettre à jour une UE.
  Description : en particulier les crédits et la périodicité + vérifier que les UE peuvent
  être mises à jour par la gestionnaire central en dehors de la période de modification des programmes.
    Given La période de modification des programmes n’est pas en cours
    And L’utilisateur est attaché à l’entité DRT
    And L’utilisateur est dans le groupe central manager
    And Aller sur la page de detail de l'ue: LDROI1003 en 2019-20

    When Cliquer sur le menu « Actions »
    And Cliquer sur le menu « Modifier »
    And Décocher la case « Actif »
    And Encoder 12 comme Crédits
    And Encoder bisannuelle paire comme Périodicité
    And Cliquer sur le bouton « Enregistrer »
    And A la question, « voulez-vous reporter » répondez « oui »

    Then Vérifier que le champ Crédits est bien 12
    And Vérifier que la Périodicité est bien bisannuelle paire
    And Rechercher LDROI1003 en 2020-21
    And Vérifier que le champ Crédits est bien 12
    And Vérifier que la Périodicité est bien bisannuelle paire

  Scenario: 10. En tant que gestionnaire facultaire, je dois pouvoir créer un nouveau partim.
    Given La période de modification des programmes est en cours
    And L’utilisateur est attaché à l’entité MED
    Given Aller sur la page de detail de l'ue: WPEDI2190 en 2019-20
    When Cliquer sur le menu « Actions »
    And Cliquer sur le menu « Nouveau partim »
    And Encoder 3 comme Code dédié au partim
    And Cliquer sur le bouton « Enregistrer »

    Then Vérifier que le partim WPEDI21903 a bien été créé de 2019-20 à 2024-25.
    When Cliquer sur le lien WPEDI2190
    Then Vérifier que le cours parent WPEDI2190 contient bien 3 partims.

  Scenario: 11. Un tant que gestionnaire facultaire, je dois pouvoir créer un autre collectif
    Given La période de modification des programmes est en cours
    And L’utilisateur est attaché à l’entité MED

    Given Aller sur la page de recherche d'UE
    When Cliquer sur le menu « Actions »
    And Cliquer sur le menu « Nouvelle UE »

    And Encoder WMEDI1234 comme Code
    And Encoder Autre collectif comme Type
    And Encoder 5 comme Crédit
    And Encoder Louvain-la-Neuve - UCLouvain comme Lieu d’enseignement
    And Encoder MED comme Entité resp. cahier des charges
    And Encoder MED comme Entité d’attribution
    And Encoder Test comme Intitulé commun
    And Cliquer sur le bouton « Enregistrer »

    Then Vérifier que le partim WMEDI1234 a bien été créé de 2019-20 à 2024-25.

  Scenario: 12. En tant que gestionnaire facultaire, je dois pouvoir modifier un autre collectif.
    Given La période de modification des programmes est en cours
    And L’utilisateur est attaché à l’entité GLOR
    Given Aller sur la page de detail de l'ue: LGLOR2839 en 2019-20

    When Cliquer sur le menu « Actions »
    And Cliquer sur le menu « Modifier »
    And Encoder Annuel comme Périodicité
    And Cliquer sur le bouton « Enregistrer »
    And A la question, « voulez-vous reporter » répondez « oui »
    Then Vérifier que la Périodicité est bien Annuel

  Scenario: 13. En tant que gestionnaire facultaire, je dois pouvoir consulter l’onglet « Formations ».
    Given Aller sur la page de detail de l'ue: LCHM1211 en 2018-19
    When Cliquer sur l'onglet Formations
    Then Vérifier que l'unité d'enseignement est incluse dans LBBMC365R, LBBMC951R, LCHIM501F, LCHIM971R
    Then Vérifier que BIOL1BA à la ligne 1 a 88 inscrits dont 4 à l'ue
    Then Vérifier que CHIM11BA à la ligne 2 a 63 inscrits dont 1 à l'ue
    Then Vérifier que CHIM1BA à la ligne 3 a 53 inscrits dont 34 à l'ue

  Scenario: 14. En tant que gestionnaire facultaire, je dois pouvoir consulter l’onglet « Enseignants ».
    Given Aller sur la page de detail de l'ue: LCHM1211 en 2018-19
    When Cliquer sur l'onglet Enseignant·e·s
    Then Vérifier que à la ligne 2, l'enseignant est bien HAUTIER, Geoffroy avec comme fonction Co-titulaire débutant en 2017 pour une durée de 3 ans avec un volume en Q1 de 15,00 et en Q2 de 27,00
    Then Vérifier que à la ligne 3, l'enseignant est bien DEVILLERS, Michel avec comme fonction Co-titulaire débutant en 2017 pour une durée de 3 ans avec un volume en Q1 de 15,00 et en Q2 de 27,00

  Scenario: 15. En tant que gestionnaire facultaire, je dois pouvoir modifier l’onglet « Enseignant ».
    Given La période de modification des programmes est en cours
    And L’utilisateur est attaché à l’entité MED
    And Aller sur la page de detail de l'ue: WPEDI21901 en 2018-19
    When Cliquer sur l'onglet Enseignant·e·s
    And Cliquer sur le bouton « Gérer la répartition »
    And Cliquer sur « Ajouter sur l’année en cours » sur la ligne 1
    And Encoder 2.0 comme PP
    And Cliquer sur le bouton « Enregistrer »
    Then Vérifier que à la ligne 2, l'enseignant a comme fonction Co-titulaire avec un volume en Q1 de 2,00 et en Q2 de 2,00

    When  Cliquer sur le bouton « Modifier » sur la ligne 1
    And Encoder 2.0 comme PM
    And Cliquer sur le bouton « Enregistrer »
    Then Vérifier que à la ligne 1, l'enseignant a comme fonction Coordinateur(trice) avec un volume en Q1 de 2,00 et en Q2 de 0,00

  Scenario: 16. En tant que gestionnaire facultaire, je dois pouvoir mettre à jour les fiches descriptives.
    Given L’utilisateur est attaché à l’entité FARM
    And Aller sur la page de detail de l'ue: WFARM1003 en 2019-20
    When Cliquer sur l'onglet Fiche descriptive
    And Cliquer sur le bouton « Modifier » sur la ligne Méthodes d’enseignement
    And Encoder Test comme méthode d'enseignement
    And Cliquer sur le bouton « Enregistrer »
    And Cliquer sur le bouton « Ajouter »
    And Encoder Test comme Intitulé
    And Encoder Oui comme Support Obligatoire
    And Cliquer sur le bouton « Enregistrer »

    Then Vérifier que la  Méthode d'enseignement est à Test
    And Vérifier que le support de cours possède bien Test

  Scenario: 17. En tant que professeur, je dois pouvoir mettre à jour les fiches descriptives.
  Description : Mise à jour par les professeurs depuis le bureau virtuel
  Tester l’interface telle que vue par les professeurs

  Scenario: 18. En tant que gestionnaire facultaire, je dois pouvoir modifier le cahier des charges.
    Given La période de modification des programmes est en cours
    And L’utilisateur est attaché à l’entité MED
    And Aller sur la page de detail de l'ue: WBIOL1950 en 2019-20
    When Sélectionner l’onglet « Cahier des charges »
    And Cliquer sur le bouton « Modifier » sur la ligne Thèmes abordés
    And Encoder Test1 comme thèmes abordés
    And Cliquer sur le bouton « Enregistrer »
    Then Vérifier que Test1 est bien un thème abordé

    When Cliquer sur le bouton « Ajouter un autre »
    And Encoder AA1 comme Code
    And Encoder Test AA1 comme Texte
    And Cliquer sur le bouton « Enregistrer »

    When  Cliquer sur le bouton « Ajouter un autre »
    And Encoder AA2 comme Code
    And Encoder Test AA2 comme Texte
    And Cliquer sur le bouton « Enregistrer »
    And Cliquer sur la « flèche vers le haut »

    Then Vérifier que Test AA2 est bien présent à la ligne 1 des acquis d'apprentissage.
    And Vérifier que Test AA1 est bien présent à la ligne 2 des acquis d'apprentissage.
