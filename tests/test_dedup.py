import pandas as pd
import pytest
from football_prediction.ingestion import dedup

key_columns = ("league_id", "season_id", "Div","Date", "Time", "HomeTeam", "AwayTeam")

def test_find_duplicates():
    data = {
        "league_id": [1, 1, 1, 1],
        "season_id": [2020, 2020, 2020, 2020],
        "Div": ["E0", "E0", "E0", "E0"],
        "Date": ["2020-01-01", "2020-01-01", "2020-01-02", "2020-01-02"],
        "Time": ["15:00", "15:00", "17:00", "17:00"],
        "HomeTeam": ["TeamA", "TeamA", "TeamB", "TeamB"],
        "AwayTeam": ["TeamB", "TeamB", "TeamC", "TeamC"],
        "_source_row": [1, 2, 3, 4]
    }
    df = pd.DataFrame(data)
    detector = dedup.DuplicateDetector(key_columns)
    candidates, issues = detector.find(df)

    assert len(candidates) == 2
    assert len(issues) == 2
    assert all(issue.source_row in [2, 4] for issue in issues)
    assert all(issue.severity == "warning" for issue in issues)
    assert all(issue.code == "duplicate_candidate" for issue in issues)
    assert all(issue.message == "Fixture identity matches an earlier row; review before importing both records" for issue in issues)
    
def test_no_duplicates():
    data = {
        "league_id": [1, 1],
        "season_id": [2020, 2020],
        "Div": ["E0", "E0"],
        "Date": ["2020-01-01", "2020-01-02"],
        "Time": ["15:00", "17:00"],
        "HomeTeam": ["TeamA", "TeamB"],
        "AwayTeam": ["TeamB", "TeamC"],
        "_source_row": [1, 2]
    }
    df = pd.DataFrame(data)
    detector = dedup.DuplicateDetector(key_columns)
    candidates, issues = detector.find(df)

    assert len(candidates) == 0
    assert len(issues) == 0