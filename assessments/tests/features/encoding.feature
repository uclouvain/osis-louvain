Feature: Score encoding

  Background:
    Given The program manager is logged

  Scenario: Encoding of scores
    When Go to score encoding home page
    And Select user offer
    And Click on encode
    And Fill score for one student
    Then Modification should be visible
    When Click on encode bis
    And Fill all scores
    Then Modification should be visible
    When Click on encode bis
    And Clear all scores
    Then Modification should be visible

  Scenario: Injection of excel file
    When Go to score encoding home page
    And Select user offer
    And Click on encode
    And Clear all scores
    And Download excel
    Then Excel should be present
    When Fill excel file
    And Inject excel file
    Then Modification should be visible

  Scenario: Double encoding of scores
    When Go to score encoding home page
    And Select user offer
    And Click on encode
    And Fill all scores
    And Click on double encode
    And Fill all scores
    And Solve differences
    Then Modification should be visible

  Scenario: Encode via pdf
    When Go to score encoding home page
    And Select user offer
    And Select tab via paper
    And Download pdf
    Then Pdf should be present