import pandas as pd
from .clean_columns import normalize_columns
from .constants import REQUIRED_COLUMNS, GOAL_COLUMNS
from .parsing import _parse_dates

def prepare_frame(raw: pd.DataFrame, *, date_format, league, season):
    frame, source_map = normalize_columns(raw)
    missing = sorted(REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        raise ValueError(
            "Missing required logical columns: " + ", ".join(missing)
            + ". Required fields are Date, HomeTeam, AwayTeam, and FTR (or Res)."
        )
        
    frame.insert(0, "_source_row", range(2, len(frame) + 2))
    frame["Date"] = _parse_dates(frame["Date"], date_format)
    
    for col in ("HomeTeam", "AwayTeam"):
        frame[col] = frame[col].astype("string").str.strip()
        frame.loc[frame[col].eq(""), col] = pd.NA
        
    frame["FTR"] = frame["FTR"].astype("string").str.strip().str.upper()
    for col in GOAL_COLUMNS.intersection(frame.columns):
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
        
    # Add league and season columns if provided
    if league is not None:
        frame["league_id"] = league.strip()
    elif "Div" in frame.columns:
        frame["league_id"] = frame["Div"].astype("string").str.strip()
    if season is not None:
        frame["season_id"] = season.strip()
    return frame, source_map