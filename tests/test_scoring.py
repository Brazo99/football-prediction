import pandas as pd
import pytest
from football_prediction.ingestion import scoring

def test_result_from_goals():
    home_goals = pd.Series([0, 1, 1, 0, 0, 0, 1, 1, 0])
    away_goals = pd.Series([0, 0, 0, 0, 0, 1, 1, 2, 0])

    expected_results = pd.Series(["D", "H", "H", "D", "D", "A", "D", "A", "D"], dtype="object")
    actual_results = scoring._result_from_goals(home_goals, away_goals)
    
    pd.testing.assert_series_equal(actual_results, expected_results)
    
def test_result_from_goals_with_missing_values():
    home_goals = pd.Series([0, 1, None, 0, 0, 0, 1, 1, 0])
    away_goals = pd.Series([0, 0, 0, None, 0, 1, 1, 2, None])

    expected_results = pd.Series(["D", "H", pd.NA, pd.NA, "D", "A", "D", "A", pd.NA], dtype="object")
    actual_results = scoring._result_from_goals(home_goals, away_goals)
    
    pd.testing.assert_series_equal(actual_results, expected_results)
    
def test_result_from_goals_with_all_missing_values():
    home_goals = pd.Series([None, None, None])
    away_goals = pd.Series([None, None, None])

    expected_results = pd.Series([pd.NA, pd.NA, pd.NA], dtype="object")
    actual_results = scoring._result_from_goals(home_goals, away_goals)
    
    pd.testing.assert_series_equal(actual_results, expected_results)
    
def test_result_from_goals_with_empty_series():
    home_goals = pd.Series([])
    away_goals = pd.Series([])

    expected_results = pd.Series([], dtype="object")
    actual_results = scoring._result_from_goals(home_goals, away_goals)
    
    pd.testing.assert_series_equal(actual_results, expected_results)