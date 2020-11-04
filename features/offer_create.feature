Feature: Création d'offre

  Background:
    Given La base de données est dans son état initial.
    And les flags d'éditions des offres sont désactivés.
    And L'utilisateur est loggé en tant que gestionnaire central

  Scenario Outline: En tant que gestionnaire central, je dois pouvoir créer une offre de type « formation ».
    Given Aller sur la page Catalogue de formations / Formation
    When Recherche offre Cliquer sur le menu « Actions »
    And Cliquer sur « Nouvelle Formation »
    And Sélectionner le type de formation à <type_de_formation>
    And Cliquer sur « Oui, je confirme »
    And Encoder <acronym> comme  Sigle/Intitulé abrégé
    And Encoder <code> comme Code
    And Remplir formulaire de création de formation
    And Cliquer sur l'onglet Diplômes/Certificats
    And Encoder <intitule_du_diplome> comme Intitulé du diplôme
    And Offre création Cliquer sur le bouton « Enregistrer »
    And Si une modal d'avertissement s'affiche, cliquer sur « oui »
    Then Vérifier que la formation <acronym> à bien été créée
    And Vérifier que le champ Sigle/Intitulé abrégé est bien <acronym>
    And Vérifier que le champ Code est bien <code>

    Examples:
      | acronym    | code      | type_de_formation                            | intitule_du_diplome |
      | DROI2MS/TT | LDROI200S | Master en 120 crédits à finalité spécialisée | Diplome en droit    |
      | CUIS2FC    | LCUIS100Q | Certificat d’université 2ème cycle           | Diplome en cuisine  |

  Scenario: En tant que gestionnaire central, je dois pouvoir créer une offre de type « mini- formation ».
  OPTIONENTF LSIPS100O CAMG CAMG
    Given Aller sur la page Catalogue de formations / Formation
    When Recherche offre Cliquer sur le menu « Actions »
    And Cliquer sur « Nouvelle Mini-Formation »
    And Sélectionner le type de formation à Option
    And Cliquer sur « Oui, je confirme »
    And Encoder OPTIONENTF comme  Sigle/Intitulé abrégé
    And Encoder LSIPS100O comme Code
    And Remplir formulaire de création de mini-formation
    And Offre création Cliquer sur le bouton « Enregistrer »

    Then Vérifier que la formation OPTIONENTF à bien été créée
    And Vérifier que le champ Sigle/Intitulé abrégé est bien OPTIONENTF
    And Vérifier que le champ Code est bien LSIPS100O
