from .rules import RowIssue
import pandas as pd
from typing import cast

class DuplicateDetector:
    def __init__(self, key_columns):
        self.key_columns = key_columns

    def find(self, frame: pd.DataFrame):
        keys = [c for c in self.key_columns if c in frame.columns]
        
        if not {"Date", "HomeTeam", "AwayTeam"}.issubset(keys):
            raise RuntimeError("Internal error: fixture identity columns unavailable")
        
        mask = frame.duplicated(subset=keys, keep="first")
        candidates = frame.loc[mask].copy()
        issues = [
            RowIssue(int(cast(int, frame.at[idx, "_source_row"])), "warning", "duplicate_candidate",
                     "Fixture identity matches an earlier row; review before importing both records" )
            for idx in candidates.index
        ]
        return candidates, issues