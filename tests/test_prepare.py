import pandas as pd
import pytest
from football_prediction.ingestion import prepare

def test_prepare_frame_adds_source_row_and_parses_dates():
    raw_data = {
        "Date": ["2023-01-01", "2023-01-02"],
        "HomeTeam": ["TeamA", "TeamB"],
        "AwayTeam": ["TeamC", "TeamD"],
        "FTR": ["H", "A"]
    }
    raw_df = pd.DataFrame(raw_data)
    
    prepared_df, source_map = prepare.prepare_frame(raw_df, date_format="%Y-%m-%d", league="EPL", season="2023/24")
    
    assert "_source_row" in prepared_df.columns
    assert prepared_df["_source_row"].tolist() == [2, 3]
    assert pd.api.types.is_datetime64_any_dtype(prepared_df["Date"])
    assert prepared_df["league_id"].iloc[0] == "EPL"
    assert prepared_df["season_id"].iloc[0] == "2023/24"
    
def test_prepare_frame_missing_required_columns():
    raw_data = {
        "Date": ["2023-01-01"],
        "HomeTeam": ["TeamA"],
        # "AwayTeam" is missing
        "FTR": ["H"]
    }
    raw_df = pd.DataFrame(raw_data)
    
    with pytest.raises(ValueError) as excinfo:
        prepare.prepare_frame(raw_df, date_format="%Y-%m-%d", league="EPL", season="2023/24")
    
    assert "Missing required logical columns" in str(excinfo.value)
    
def test_prepare_frame_strips_whitespace_and_handles_empty_strings():
    raw_data = {
        "Date": ["2023-01-01"],
        "HomeTeam": [" TeamA "],
        "AwayTeam": [" "],  # Empty string after stripping
        "FTR": [" h "]
    }
    raw_df = pd.DataFrame(raw_data)
    
    prepared_df, source_map = prepare.prepare_frame(raw_df, date_format="%Y-%m-%d", league=None, season=None)
    
    assert prepared_df["HomeTeam"].iloc[0] == "TeamA"
    assert pd.isna(prepared_df["AwayTeam"].iloc[0])
    assert prepared_df["FTR"].iloc[0] == "H"
    
def test_prepare_frame_numeric_conversion():
    raw_data = {
        "Date": ["2023-01-01"],
        "HomeTeam": ["TeamA"],
        "AwayTeam": ["TeamB"],
        "FTR": ["H"],
        "FTHG": ["2"],
        "FTAG": ["1"]
    }
    raw_df = pd.DataFrame(raw_data)
    
    prepared_df, source_map = prepare.prepare_frame(raw_df, date_format="%Y-%m-%d", league=None, season=None)
    
    assert pd.api.types.is_numeric_dtype(prepared_df["FTHG"])
    assert pd.api.types.is_numeric_dtype(prepared_df["FTAG"])
    assert prepared_df["FTHG"].iloc[0] == 2
    assert prepared_df["FTAG"].iloc[0] == 1
    
def test_prepare_frame_handles_missing_goal_columns():
    raw_data = {
        "Date": ["2023-01-01"],
        "HomeTeam": ["TeamA"],
        "AwayTeam": ["TeamB"],
        "FTR": ["H"]
        # FTHG and FTAG are missing
    }
    raw_df = pd.DataFrame(raw_data)
    
    prepared_df, source_map = prepare.prepare_frame(raw_df, date_format="%Y-%m-%d", league=None, season=None)
    
    assert "FTHG" not in prepared_df.columns
    assert "FTAG" not in prepared_df.columns
    
def test_prepare_frame_handles_div_column_for_league():
    raw_data = {
        "Date": ["2023-01-01"],
        "HomeTeam": ["TeamA"],
        "AwayTeam": ["TeamB"],
        "FTR": ["H"],
        "Div": ["EPL"]
    }
    raw_df = pd.DataFrame(raw_data)
    
    prepared_df, source_map = prepare.prepare_frame(raw_df, date_format="%Y-%m-%d", league=None, season=None)
    
    assert prepared_df["league_id"].iloc[0] == "EPL"
    
def test_prepare_frame_handles_none_league_and_season():
    raw_data = {
        "Date": ["2023-01-01"],
        "HomeTeam": ["TeamA"],
        "AwayTeam": ["TeamB"],
        "FTR": ["H"]
    }
    raw_df = pd.DataFrame(raw_data)
    
    prepared_df, source_map = prepare.prepare_frame(raw_df, date_format="%Y-%m-%d", league=None, season=None)
    
    assert "league_id" not in prepared_df.columns
    assert "season_id" not in prepared_df.columns
    
def test_prepare_frame_handles_invalid_goal_values():
    raw_data = {
        "Date": ["2023-01-01"],
        "HomeTeam": ["TeamA"],
        "AwayTeam": ["TeamB"],
        "FTR": ["H"],
        "FTHG": ["invalid"],  # Non-numeric value
        "FTAG": ["3"]
    }
    raw_df = pd.DataFrame(raw_data)
    
    prepared_df, source_map = prepare.prepare_frame(raw_df, date_format="%Y-%m-%d", league=None, season=None)
    
    assert pd.isna(prepared_df["FTHG"].iloc[0])  # Should be NaN due to coercion
    assert prepared_df["FTAG"].iloc[0] == 3
    
def test_prepare_frame_handles_empty_dataframe():
    raw_df = pd.DataFrame(columns=["Date", "HomeTeam", "AwayTeam", "FTR"])
    
    prepared_df, source_map = prepare.prepare_frame(raw_df, date_format="%Y-%m-%d", league=None, season=None)
    
    assert prepared_df.empty
    assert "_source_row" in prepared_df.columns
    
def test_prepare_frame_handles_additional_columns():
    raw_data = {
        "Date": ["2023-01-01"],
        "HomeTeam": ["TeamA"],
        "AwayTeam": ["TeamB"],
        "FTR": ["H"],
        "ExtraColumn": ["ExtraValue"]
    }
    raw_df = pd.DataFrame(raw_data)
    
    prepared_df, source_map = prepare.prepare_frame(raw_df, date_format="%Y-%m-%d", league=None, season=None)
    
    assert "ExtraColumn" in prepared_df.columns
    assert prepared_df["ExtraColumn"].iloc[0] == "ExtraValue"
    