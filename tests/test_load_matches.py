import pandas as pd
import pytest
from football_prediction.ingestion import load_matches
from football_prediction.ingestion.source import CSVMatchSource
from football_prediction.ingestion.validation import ValidationPipeline, default_rules, default_warnings
from football_prediction.ingestion.dedup import DuplicateDetector
from football_prediction.ingestion.splitter import ResultSplitter

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

def test_MatchImporter(tmp_path):
    path = tmp_path / "sample_matches.csv"
    path.write_text(csv_content, encoding="utf8")  
    source= CSVMatchSource(path)
    pipeline = ValidationPipeline(default_rules(), default_warnings())
    deduper = DuplicateDetector(("league_id", "season_id", "Date", "Time", "HomeTeam", "AwayTeam"))
    splitter=ResultSplitter()
    
    importer = load_matches.MatchImporter(
        source=source,
        pipeline=pipeline,
        deduper=deduper,
        splitter=splitter
    )
    
    import_result = importer.load(league="SPL", season="2014/2015", date_format="%d/%m/%Y")
    
    assert import_result.accepted.shape[0] > 0
    assert import_result.rejected.shape[0] >= 0
    assert import_result.duplicate_candidates.shape[0] >= 0
    assert len(import_result.issues) >= 0
    assert import_result.source_path == str(source.path.resolve())
    assert isinstance(import_result.source_column_map, dict)
    
def test_load_matches_function(tmp_path):
    path = tmp_path / "sample_matches.csv"
    path.write_text(csv_content, encoding="utf8")  
    
    import_result = load_matches.load_matches(path, league="SPL", season="2014/2015", date_format="%d/%m/%Y")
    
    assert import_result.accepted.shape[0] > 0
    assert import_result.rejected.shape[0] >= 0
    assert import_result.duplicate_candidates.shape[0] >= 0
    assert len(import_result.issues) >= 0
    assert import_result.source_path == str(path.resolve())
    assert isinstance(import_result.source_column_map, dict)
