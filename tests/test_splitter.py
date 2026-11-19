import pandas as pd
import pytest
from football_prediction.ingestion import splitter

def test_sort_matches_chronologically():
    df = pd.DataFrame({
        "Date": ["2023-01-01", "2023-01-02", "2023-01-01"],
        "Time": ["12:00", "12:00", "11:00"],
        "HomeTeam": ["A", "B", "C"],
        "AwayTeam": ["D", "E", "F"]
    })
    sorted_df = splitter.sort_matches_chronologically(df)
    assert sorted_df.iloc[0]["HomeTeam"] == "C"
    assert sorted_df.iloc[1]["HomeTeam"] == "A"
    assert sorted_df.iloc[2]["HomeTeam"] == "B"
    
def test_sort_matches_chronologically_no_time():
    df = pd.DataFrame({
        "Date": ["2023-01-01", "2023-01-02", "2023-01-01"],
        "HomeTeam": ["A", "B", "C"],
        "AwayTeam": ["D", "E", "F"]
    })
    sorted_df = splitter.sort_matches_chronologically(df)
    assert sorted_df.iloc[0]["HomeTeam"] == "A"
    assert sorted_df.iloc[1]["HomeTeam"] == "C"
    assert sorted_df.iloc[2]["HomeTeam"] == "B"
    
def test_sort_matches_chronologically_no_date():
    df = pd.DataFrame({
        "HomeTeam": ["A", "B", "C"],
        "AwayTeam": ["D", "E", "F"]
    })
    sorted_df = splitter.sort_matches_chronologically(df)
    assert sorted_df.equals(df)  # Should remain unchanged
    
def test_result_splitter_split():
    df = pd.DataFrame({
        "Date": ["2023-01-01", "2023-01-02", "2023-01-01"],
        "Time": ["12:00", "12:00", "11:00"],
        "HomeTeam": ["A", "B", "C"],
        "AwayTeam": ["D", "E", "F"]
    })
    rejected_indices = {1}
    duplicate_indices = {2}
    reasons = {1: ["Invalid score"], 2: ["Duplicate match"]}
    
    splitter_instance = splitter.ResultSplitter()
    accepted, rejected = splitter_instance.split(df, rejected_indices=rejected_indices,
                                                 duplicate_indices=duplicate_indices,
                                                 reasons=reasons)
    
    assert len(accepted) == 1
    assert accepted.iloc[0]["HomeTeam"] == "A"
    
    assert len(rejected) == 1
    assert rejected.iloc[0]["HomeTeam"] == "B"
    assert rejected.iloc[0]["_rejection_reasons"] == "Invalid score"