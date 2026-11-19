import pandas as pd

def _parse_dates(values: pd.Series, date_format: str | None) -> pd.Series:
    """
        Parse source dates without silently guessing ambiguous day/month order.
    """
    if date_format:
        parsed = pd.to_datetime(values, format=date_format, errors="coerce")
        # Some Football-Data exports use four-digit years; allow pandas' explicit
        # fallback only for rows the configured two-digit format did not parse.
        missing = parsed.isna() & values.notna() & values.astype(str).str.strip().ne("")
        if missing.any():
            fallback = pd.to_datetime(values[missing], dayfirst=True, errors="coerce")
            parsed.loc[missing] = fallback
        return parsed  
    return pd.to_datetime(values, dayfirst=True, errors="coerce")

if __name__ == "__main__":
    # Example usage
    dates = pd.Series([" 01/02/2020 ", " 15/03/2021 ", " 30/12/2019 "])
    parsed_dates = _parse_dates(dates, date_format="%d/%m/%Y")
    print(parsed_dates)