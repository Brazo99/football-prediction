import re
import pandas as pd

ALIASES = {
    "HG": "FTHG",
    "AG": "FTAG",
    "Res": "FTR",
}

def _clean_column_name(name: object) -> str:
    """
        Trim column whitespace and collapse internal whitespace.
    """
    return re.sub(r"\s+", "", str(name).strip())

def normalize_columns(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    """
        Normalize headers and documented Football-Data aliases.

        Raises ValueError for duplicate headers after normalization or conflicting aliases.
    """
    original_names = list(frame.columns)
    cleaned = [_clean_column_name(name) for name in original_names]
    
    if len(cleaned) != len(set(cleaned)):
        duplicates = sorted({name for name in cleaned if cleaned.count(name) > 1})
        raise ValueError(f"Duplicate columns after header normalization: {duplicates}")

    rename: dict[str, str] = {}
    for name in cleaned:
        canonical = ALIASES.get(name, name)
        if canonical in rename.values() and name != canonical:
            raise ValueError(f"Conflicting source columns map to {canonical!r}")
        
        rename[name] = canonical
    
    normalized = frame.copy()
    normalized.columns = cleaned
    normalized = normalized.rename(columns=rename)
    
    if len(normalized.columns) != len(set(normalized.columns)):
        raise ValueError("Multiple input columns resolve to the same canonical column")
    
    source_map = {source: rename[source] for source in cleaned}
    return normalized, source_map