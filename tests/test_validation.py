import pandas as pd
from football_prediction.ingestion import validation

def test_validation_pipeline():
    data = {
        "Date": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "Time": ["12:00", "13:00", "14:00"],
        "HomeTeam": ["TeamA", None, "TeamC"],
        "AwayTeam": ["TeamB", "TeamD", None],
        "FTHG": [1, 2, 3],
        "FTAG": [0, 1, 2],
        "FTR": ["H", "A", "D"]
    }
    df = pd.DataFrame(data)
    df["_source_row"] = df.index  # Simulate source row tracking

    pipeline = validation.ValidationPipeline(
        rules=validation.default_rules(),
        warnings=validation.default_warnings()
    )

    reasons, issues = pipeline.run(df)

    assert len(reasons) == 2  # Two rows have issues
    assert len(issues) == 4   # Four issues in total (two errors and two warnings)
    
def test_validation_pipeline_with_no_issues():
    data = {
        "Date": ["2023-01-01", "2023-01-02"],
        "Time": ["12:00", "13:00"],
        "HomeTeam": ["TeamA", "TeamB"],
        "AwayTeam": ["TeamC", "TeamD"],
        "FTHG": [1, 0],
        "FTAG": [0, 1],
        "FTR": ["H", "A"]
    }
    df = pd.DataFrame(data)
    df["_source_row"] = df.index  # Simulate source row tracking

    pipeline = validation.ValidationPipeline(
        rules=validation.default_rules(),
        warnings=validation.default_warnings()
    )

    reasons, issues = pipeline.run(df)

    assert len(reasons) == 0  # No rows have issues
    assert len(issues) == 0   # No issues in total
    
    