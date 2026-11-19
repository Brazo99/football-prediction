import pandas as pd
from typing import cast
from .rules import (RowIssue, InvalidDateRule,
                    MissingTeamRule, ResultCodeRule, 
                    SameTeamRule, ScoreConsistencyRule, 
                    IncompleteGoalColumnsWarning)
    
class ValidationPipeline:
    def __init__(self, rules, warnings=()):
        self.rules = list(rules)
        self.warnings = list(warnings)

    def run(self, frame: pd.DataFrame):
        reasons: dict[int, list[str]] = {}
        issues: list[RowIssue] = []

        def record(idx: int, code: str, message: str, severity: str):
            reasons.setdefault(idx, []).append(message)
            issues.append(RowIssue(int(cast(int, frame.at[idx, "_source_row"])),
                                   severity, code, message))

        for rule in self.rules:
            for v in rule.check(frame):
                for idx in frame.index[v.mask.fillna(False)]:
                    record(idx, v.code, v.message, "error")

        for warn in self.warnings:
            for idx, code, msg in warn.check(frame):
                issues.append(RowIssue(int(cast(int, frame.at[idx, "_source_row"])),
                                       "warning", code, msg))

        return reasons, issues
    
def default_rules():
    return [
        InvalidDateRule(),
        MissingTeamRule("HomeTeam"),
        MissingTeamRule("AwayTeam"),
        ResultCodeRule(),
        SameTeamRule(),
        ScoreConsistencyRule(),
    ]

def default_warnings():
    return [IncompleteGoalColumnsWarning()]
