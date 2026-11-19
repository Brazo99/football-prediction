import pandas as pd
import pytest
from football_prediction.ingestion import clean_columns

def test_clean_column_name_trims_and_collapses_whitespace():
    assert clean_columns._clean_column_name("  Column Name  ") == "ColumnName"
    assert clean_columns._clean_column_name("Column   Name") == "ColumnName"
    assert clean_columns._clean_column_name(" Column   Name ") == "ColumnName"
    assert clean_columns._clean_column_name("Column\tName") == "ColumnName"
    assert clean_columns._clean_column_name("Column\nName") == "ColumnName"
    
def test_normalize_columns_with_aliases():
    df = pd.DataFrame(columns=["HG", "AG", "Res"])
    normalized, source_map = clean_columns.normalize_columns(df)
    
    assert list(normalized.columns) == ["FTHG", "FTAG", "FTR"]
    assert source_map == {"HG": "FTHG", "AG": "FTAG", "Res": "FTR"}
    
def test_normalize_columns_with_duplicate_headers_raises():
    df = pd.DataFrame(columns=["Column1", "Column1"])
    with pytest.raises(ValueError, match="Duplicate columns after header normalization"):
        clean_columns.normalize_columns(df)
        
def test_normalize_columns_with_conflicting_aliases_raises():
    df = pd.DataFrame(columns=["FTHG", "HG"])
    with pytest.raises(ValueError, match="Conflicting source columns map to 'FTHG'"):
        clean_columns.normalize_columns(df)
        
def test_normalize_columns_with_multiple_columns_resolving_to_same_canonical_raises():
    df = pd.DataFrame(columns=["HG", "FTHG"])
    with pytest.raises(ValueError, match="Multiple input columns resolve to the same canonical column"):
        clean_columns.normalize_columns(df)
        
def test_normalize_columns_with_no_aliases():
    df = pd.DataFrame(columns=["Column1", "Column2"])
    normalized, source_map = clean_columns.normalize_columns(df)
    
    assert list(normalized.columns) == ["Column1", "Column2"]
    assert source_map == {"Column1": "Column1", "Column2": "Column2"}
    
def test_normalize_columns_with_mixed_aliases_and_non_aliases():
    df = pd.DataFrame(columns=["HG", "Column2", "AG"])
    normalized, source_map = clean_columns.normalize_columns(df)
    
    assert list(normalized.columns) == ["FTHG", "Column2", "FTAG"]
    assert source_map == {"HG": "FTHG", "Column2": "Column2", "AG": "FTAG"}
    
def test_normalize_columns_with_whitespace_in_headers():
    df = pd.DataFrame(columns=["  HG  ", "  AG  ", "  Res  "])
    normalized, source_map = clean_columns.normalize_columns(df)
    
    assert list(normalized.columns) == ["FTHG", "FTAG", "FTR"]
    assert source_map == {"HG": "FTHG", "AG": "FTAG", "Res": "FTR"}
    
def test_normalize_columns_with_empty_dataframe():
    df = pd.DataFrame(columns=[])
    normalized, source_map = clean_columns.normalize_columns(df)
    
    assert list(normalized.columns) == []
    assert source_map == {}