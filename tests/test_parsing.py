import pandas as pd
import pytest
from football_prediction.ingestion import parsing

def test_parse_dates_with_valid_format():
    dates = pd.Series(["01/02/2020", "15/03/2021", "30/12/2019"])
    expected = pd.to_datetime(dates, format="%d/%m/%Y")
    actual = parsing._parse_dates(dates, date_format="%d/%m/%Y")
    
    pd.testing.assert_series_equal(actual, expected)
    
def test_parse_dates_with_empty_series():
    dates = pd.Series([], dtype="object")
    expected = pd.Series([], dtype="datetime64[s]")
    actual = parsing._parse_dates(dates, date_format="%d/%m/%Y")
    
    pd.testing.assert_series_equal(actual, expected)

def test_parse_dates_with_none_format():
    dates = pd.Series(["01/02/2020", "15/03/2021", "30/12/2019"])
    expected = pd.to_datetime(dates, dayfirst=True, errors="coerce")
    actual = parsing._parse_dates(dates, date_format=None)
    
    pd.testing.assert_series_equal(actual, expected)
    
def test_parse_dates_with_mixed_valid_and_invalid_dates():
    dates = pd.Series(["01/02/2020", "invalid_date", "30/12/2019"])
    expected = pd.to_datetime(dates, dayfirst=True, errors="coerce")
    actual = parsing._parse_dates(dates, date_format="%d/%m/%Y")
    
    pd.testing.assert_series_equal(actual, expected)
    