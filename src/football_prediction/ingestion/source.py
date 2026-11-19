from pathlib import Path
from typing import Protocol
from pandas.errors import ParserError
import pandas as pd


class MatchSource(Protocol):
    def read(self) -> pd.DataFrame: ...
    
class CSVMatchSource:
    def __init__(self, path: str | Path, *, encodings = ("utf8-sig", "cp1252")) -> None :
        self.path = Path(path)
        self.encoding = encodings
        if not self.path.exists():
            raise FileNotFoundError(f"File {self.path} does not exist.")
        
        if self.path.suffix.lower() != ".csv":
            raise ValueError(f"Expected a .csv file, got: {self.path.name}.")

    def read(self) -> pd.DataFrame:
        last_error: Exception | None = None
        df = None
        for enc in self.encoding:
            try:
                df = pd.read_csv(self.path, encoding=enc)
                break
            except (UnicodeDecodeError, ParserError ) as e:
                last_error = e
                   
        if isinstance(last_error, UnicodeDecodeError):
            raise last_error
        
        if df is None:
            raise ValueError("Failed to read CSV file with any supported encoding.")

        if df.empty:
            raise ValueError("CSV contains no data rows")
        
        return df