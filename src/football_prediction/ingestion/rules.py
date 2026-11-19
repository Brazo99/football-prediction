from dataclasses import dataclass, field
from typing import Protocol, Iterable
import pandas as pd
from .constants import VALID_RESULTS, GOAL_COLUMNS
from .scoring import _result_from_goals

@dataclass(frozen=True)
class Violation:
    mask: pd.Series       # True where the row violates
    code: str
    message: str

@dataclass(frozen=True)
class RowIssue:
    source_row: int
    severity: str  # "error" or "warning"
    code: str
    message: str

class ValidationRule(Protocol):
    def check(self, frame: pd.DataFrame) -> Iterable[Violation]: ...

@dataclass
class InvalidDateRule:
    def check(self, frame: pd.DataFrame) -> Iterable[Violation]:
        yield Violation(frame["Date"].isna(), "invalid_date","Date is missing or cannot be parsed")

@dataclass
class MissingTeamRule:
    column: str
    def check(self, frame: pd.DataFrame) -> Iterable[Violation]:
        code = "missing_home_team" if self.column == "HomeTeam" else "missing_away_team"
        yield Violation(frame[self.column].isna(), code, f"{self.column} is missing")

@dataclass
class ResultCodeRule:
    def check(self, frame: pd.DataFrame) -> Iterable[Violation]:
        ftr = frame["FTR"]
        yield Violation(ftr.isna(), "missing_result", "FTR/Res is missing")
        invalid = ftr.notna() & ~ftr.isin(VALID_RESULTS)
        yield Violation(invalid, "invalid_result", "FTR must be one of H, D, or A")

@dataclass
class SameTeamRule:
    def check(self, frame: pd.DataFrame) -> Iterable[Violation]:
        h, a = frame["HomeTeam"], frame["AwayTeam"]
        bad = h.notna() & a.notna() & h.str.casefold().eq(a.str.casefold())
        yield Violation(bad, "same_home_away_team", "HomeTeam and AwayTeam must be different teams")

@dataclass
class IncompleteGoalColumnsWarning:
    def check(self, frame: pd.DataFrame) -> Iterable[tuple[int, str, str]]:
        present = GOAL_COLUMNS.intersection(frame.columns)
        if not present or GOAL_COLUMNS.issubset(frame.columns):
            return
        missing = sorted(GOAL_COLUMNS - set(frame.columns))
        for idx in frame.index:
            yield idx, "incomplete_goal_columns", \
                f"Only part of the full-time score is present; missing columns: {missing}"
                
@dataclass
class ScoreConsistencyRule:
    def check(self, frame: pd.DataFrame):
        present = GOAL_COLUMNS.intersection(frame.columns)
        if not present:
            return
        if not GOAL_COLUMNS.issubset(frame.columns):
            return  # handled by IncompleteGoalColumnsRule (warning, not reject)
        
        hg, ag = frame["FTHG"], frame["FTAG"]
        yield Violation(hg.isna() ^ ag.isna(), "incomplete_score",
                        "Only one full-time goal value is present")
        
        yield Violation(hg.notna() & ag.notna() & ((hg < 0) | (ag < 0)),
                        "negative_score", "Full-time goals cannot be negative")
        
        yield Violation(hg.notna() & ag.notna() & ((hg % 1 != 0) | (ag % 1 != 0)),
                        "non_integer_score", "Full-time goals must be whole numbers")
        
        complete = hg.notna() & ag.notna() & frame["FTR"].isin(VALID_RESULTS)
        expected = pd.Series(index=frame.index, dtype="string")
        
        expected.loc[complete] = _result_from_goals(hg[complete], ag[complete]).astype("string")
        yield Violation(complete & expected.ne(frame["FTR"]),
                        "result_score_mismatch", "FTR does not match FTHG and FTAG")
        
@dataclass
class ImportResult:
    """
        Validated rows and an auditable summary of a CSV import.
    """

    accepted: pd.DataFrame
    rejected: pd.DataFrame
    duplicate_candidates: pd.DataFrame
    issues: list[RowIssue] = field(default_factory=list)
    source_path: str = ""
    source_column_map: dict[str, str] = field(default_factory=dict)

    @property
    def summary(self) -> dict[str, int | str]:
        return {
            "source_path": self.source_path,
            "accepted_rows": len(self.accepted),
            "rejected_rows": len(self.rejected),
            "duplicate_candidates": len(self.duplicate_candidates),
            "errors": sum(issue.severity == "error" for issue in self.issues),
            "warnings": sum(issue.severity == "warning" for issue in self.issues),
        }
