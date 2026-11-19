import pandas as pd
import pytest
from football_prediction.ingestion import source

csv_content  = """
Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n
SP1, 21/08/15, Malaga, Sevilla, 0, 0, D \n
SP1, 22/08/15, Ath Madrid , Las Palmas , 1, 0, H \n
SP1, 22/08/15, Espanol    , Getafe     ,    1,    0, H \n
SP1, 22/08/15, La Coruna  , Sociedad   ,    0,    0, D  \n
SP1, 22/08/15, Vallecano  , Valencia   ,    0,    0, D  \n
SP1, 23/08/15, Ath Bilbao , Barcelona  ,    0,    1, A  \n
SP1, 23/08/15, Betis      , Villarreal ,    1,    1, D  \n
SP1, 23/08/15, Levante    , Celta      ,    1,    2, A  \n
SP1, 23/08/15, Sp Gijon   , Real Madrid,    0,    0, D"""

def test_CSVMatchSource_init_with_nonexistent_file_raises(tmp_path):
    non_existent_path = tmp_path / "nonexistent.csv"
    with pytest.raises(FileNotFoundError):
        source.CSVMatchSource(non_existent_path)
        
def test_CSVMatchSource_init_with_non_csv_file_raises(tmp_path):
    non_csv_path = tmp_path / "file.txt"
    non_csv_path.write_text("Some content")
    with pytest.raises(ValueError):
        source.CSVMatchSource(non_csv_path)
        
def test_CSVMatchSource_read_with_valid_csv(tmp_path):
    csv_path = tmp_path / "matches.csv"
    csv_path.write_text(csv_content, encoding="utf8")
    
    csv_source = source.CSVMatchSource(csv_path)
    df = csv_source.read()
    
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert len(df) == 9 
    assert list(df.columns) == ["Div", "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"]   
    
def test_CSVMatchSource_read_with_empty_csv_raises(tmp_path):
    empty_csv_path = tmp_path / "empty.csv"
    empty_csv_path.write_text("Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n", encoding="utf8")
    
    csv_source = source.CSVMatchSource(empty_csv_path)
    with pytest.raises(ValueError, match="CSV contains no data rows"):
        csv_source.read() 
        
def test_CSVMatchSource_read_with_invalid_encoding_raises(tmp_path):
    csv_path = tmp_path / "matches.csv"
    csv_path.write_text(csv_content, encoding="utf16")
    
    csv_source = source.CSVMatchSource(csv_path, encodings=("utf8", "cp1252"))
    with pytest.raises(ValueError, match="Failed to read CSV file with any supported encoding."):
        csv_source.read()
        
def test_CSVMatchSource_read_with_utf16_encoding(tmp_path):
    csv_path = tmp_path / "matches.csv"
    csv_path.write_text(csv_content, encoding="utf16")
    
    csv_source = source.CSVMatchSource(csv_path, encodings=("utf16", "utf8"))
    df = csv_source.read()
    
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert len(df) == 9 
    assert list(df.columns) == ["Div", "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"]