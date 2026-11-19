import pandas as pd
import pytest
from football_prediction.ingestion import rules

"""_summary_
    Tests for the validation rules in the football prediction ingestion module.
"""
def test_invalid_date_rule():
    """
        Test the InvalidDateRule to ensure it correctly 
        identifies missing or invalid dates.
    """
    df = pd.DataFrame({"Date": [pd.NaT, "2023-01-01"]})
    rule = rules.InvalidDateRule()
    violations = list(rule.check(df))
    
    assert len(violations) == 1
    violation = violations[0]
    assert violation.code == "invalid_date"
    assert violation.mask.tolist() == [True, False]
    
def test_missing_team_rule():
    df = pd.DataFrame({"HomeTeam": [None, "TeamA"], "AwayTeam": ["TeamB", None]})
    home_rule = rules.MissingTeamRule("HomeTeam")
    away_rule = rules.MissingTeamRule("AwayTeam")
    
    home_violations = list(home_rule.check(df))
    away_violations = list(away_rule.check(df))
    
    assert len(home_violations) == 1
    assert home_violations[0].code == "missing_home_team"
    assert home_violations[0].mask.tolist() == [True, False]
    
    assert len(away_violations) == 1
    assert away_violations[0].code == "missing_away_team"
    assert away_violations[0].mask.tolist() == [False, True]
    
def test_result_code_rule():
    df = pd.DataFrame({"FTR": [None, "H", "X", "A"]})
    rule = rules.ResultCodeRule()
    violations = list(rule.check(df))
    
    assert len(violations) == 2
    missing_violation = violations[0]
    invalid_violation = violations[1]
    
    assert missing_violation.code == "missing_result"
    assert missing_violation.mask.tolist() == [True, False, False, False]
    
    assert invalid_violation.code == "invalid_result"
    assert invalid_violation.mask.tolist() == [False, False, True, False]
    
def test_same_team_rule():
    df = pd.DataFrame({"HomeTeam": ["TeamA", "TeamB"], "AwayTeam": ["TeamA", "TeamC"]})
    rule = rules.SameTeamRule()
    violations = list(rule.check(df))
    
    assert len(violations) == 1
    violation = violations[0]
    assert violation.code == "same_home_away_team"
    assert violation.mask.tolist() == [True, False]
    
def test_incomplete_goal_columns_warning_with_all_columns():
    df = pd.DataFrame({"FTHG": [1, 2], "FTAG": [0, 1]})
    warning = rules.IncompleteGoalColumnsWarning()
    warnings = list(warning.check(df))
    
    assert len(warnings) == 0  # No warnings since both columns are present
    for idx, code, msg in warnings:
        assert code == "incomplete_goal_columns"
        assert "missing columns" in msg
        
def test_incomplete_goal_columns_warning_with_missing_columns():
    df = pd.DataFrame({"FTHG": [1, 2]})  # Missing FTAG
    warning = rules.IncompleteGoalColumnsWarning()
    warnings = list(warning.check(df))
    
    assert len(warnings) == 2  # One warning for each row
    for idx, code, msg in warnings:
        assert code == "incomplete_goal_columns"
        assert "missing columns" in msg
        
def test_score_consistency_rule_with_invalid_columns():
    df = pd.DataFrame({"HomeGoals": [1, 2], "AwayGoals": [0, 1]})
    rule = rules.ScoreConsistencyRule()
    violations = list(rule.check(df))
    
    assert len(violations) == 0  # No violations since goal columns are missing, handled by warning
    
def test_score_consistency_rule_with_incomplete_scores():
    df = pd.DataFrame({"FTHG": [1, None], "FTAG": [0, 1], "FTR": ["H", "A"]})
    rule = rules.ScoreConsistencyRule()
    violations = list(rule.check(df))
    
    assert len(violations) == 4  # One violation for the incomplete score
    assert violations[0].code == "incomplete_score"
    assert violations[0].mask.tolist() == [False, True]  # Second row has incomplete score
    assert violations[0].message == "Only one full-time goal value is present"

def test_score_consistency_rule_with_negative_scores():
    df = pd.DataFrame({"FTHG": [1, -1], "FTAG": [0, 2], "FTR": ["H", "A"]})
    rule = rules.ScoreConsistencyRule()
    violations = list(rule.check(df))
    
    assert len(violations) == 4  # One violation for the negative score
    assert violations[1].code == "negative_score"
    assert violations[1].mask.tolist() == [False, True]  # Second row has negative score
    assert violations[1].message == "Full-time goals cannot be negative"
    
def test_score_consistency_rule_with_non_integer_scores():
    df = pd.DataFrame({"FTHG": [1, 1.5], "FTAG": [0, 2], "FTR": ["H", "A"]})
    rule = rules.ScoreConsistencyRule()
    violations = list(rule.check(df))
    
    assert len(violations) == 4  # One violation for the non-integer score
    assert violations[2].code == "non_integer_score"
    assert violations[2].mask.tolist() == [False, True]  # Second row has non-integer score
    assert violations[2].message == "Full-time goals must be whole numbers"
    
def test_score_consistency_rule_with_result_mismatch():
    df = pd.DataFrame({"FTHG": [1, 2], "FTAG": [0, 1], "FTR": ["H", "D"]})
    rule = rules.ScoreConsistencyRule()
    violations = list(rule.check(df))
    
    assert len(violations) == 4  # One violation for the result mismatch
    assert violations[3].code == "result_score_mismatch"
    assert violations[3].mask.tolist() == [False, True]  # Second row has result mismatch
    assert violations[3].message == "FTR does not match FTHG and FTAG"
    
def test_score_consistency_rule_with_valid_scores():
    df = pd.DataFrame({"FTHG": [1, 2], "FTAG": [0, 1], "FTR": ["H", "H"]})
    rule = rules.ScoreConsistencyRule()
    violations = list(rule.check(df))
    
    assert len(violations) == 4
    assert all(v.mask.tolist() == [False, False] for v in violations)  # No violations since scores are valid
    