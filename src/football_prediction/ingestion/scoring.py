import pandas as pd

def _result_from_goals(home_goals: pd.Series, away_goals: pd.Series) -> pd.Series:
    result = pd.Series(pd.NA, index=home_goals.index, dtype="object")
    mask = home_goals.notna() & away_goals.notna()

    result[mask & (home_goals > away_goals)] = "H"
    result[mask & (home_goals < away_goals)] = "A"
    result[mask & (home_goals == away_goals)] = "D"
    return result

if __name__ == "__main__":
    # Example usage
    home_goals = pd.Series([1, 2, 0, 3])
    away_goals = pd.Series([0, 2, 1, 3])
    results = _result_from_goals(home_goals, away_goals)
    print(results)