import pandas as pd

class ResultSplitter:
    def __init__(self, sorter=None):
        self.sorter = sorter

    def split(self, frame: pd.DataFrame, *, rejected_indices, duplicate_indices, reasons):
        rejected = frame.loc[sorted(rejected_indices)].copy()
        rejected["_rejection_reasons"] = ["; ".join(reasons[i]) for i in rejected.index]

        accepted_idx = [i for i in frame.index
                        if i not in rejected_indices and i not in duplicate_indices]
        
        accepted = sort_matches_chronologically(frame.loc[accepted_idx].copy()) if self.sorter is None else self.sorter.sort(frame.loc[accepted_idx].copy())
        return accepted, rejected.reset_index(drop=True)
    
def sort_matches_chronologically(df: pd.DataFrame) -> pd.DataFrame:
    cols = (["Date"] if "Date" in df.columns else []) + (["Time"] if "Time" in df.columns else [])
    return (df.sort_values(cols, kind="stable").reset_index(drop=True) if cols else df)