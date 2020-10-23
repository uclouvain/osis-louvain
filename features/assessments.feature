Feature: Score encoding

  Background:
    Given The program manager is logged

  Scenario: Encoding of scores
    When Go to score encoding home page
    And Search learning units of the program manager offer
    And Go encode scores for a learning unit returned
    And Submit score for one student
    Then Scores should be updated
    When Click on encode scores
    And Fill all scores
    Then Scores should be updated
    When Click on encode scores
    And Clear all scores
    Then Scores should be updated

  Scenario: Injection of excel file
    When Go to score encoding home page
    And Search learning units of the program manager offer
    And Go encode scores for a learning unit returned
    And Clear all scores
    And Download excel
    Then Excel should be present
    When Fill excel file
    And Inject excel file
    Then Scores should be updated

  Scenario: Double encoding of scores
    When Go to score encoding home page
    And Search learning units of the program manager offer
    And Go encode scores for a learning unit returned
    And Fill all scores
    And Click on double encode
    And Fill all scores
    And Solve differences
    Then Scores should be updated

  Scenario: Encode via pdf
    When Go to score encoding home page
    And Search learning units of the program manager offer
    And Select tab via paper
    And Download pdf
    Then Pdf should be present