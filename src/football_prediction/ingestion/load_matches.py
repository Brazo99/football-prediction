from .rules import ImportResult
from .prepare import prepare_frame
from .source import CSVMatchSource
from .validation import ValidationPipeline, default_rules, default_warnings
from .dedup import DuplicateDetector
from .splitter import ResultSplitter

class MatchImporter:
    def __init__(self, *, source, pipeline, deduper, splitter):
        self.source = source
        self.pipeline = pipeline
        self.deduper = deduper
        self.splitter = splitter

    def load(self, *, league=None, season=None, date_format="%d/%m/%y") -> ImportResult:
        raw = self.source.read()
        frame, source_map = prepare_frame(raw, date_format=date_format,
                                          league=league, season=season)
        reasons, issues = self.pipeline.run(frame)
        dup_candidates, dup_issues = self.deduper.find(frame)
        issues.extend(dup_issues)

        accepted, rejected = self.splitter.split(
            frame,
            rejected_indices=set(reasons),
            duplicate_indices=set(dup_candidates.index),
            reasons=reasons,
        )
        
        return ImportResult(
            accepted=accepted, rejected=rejected,
            duplicate_candidates=dup_candidates.reset_index(drop=True),
            issues=issues,
            source_path=str(self.source.path.resolve()),
            source_column_map=source_map,
        )

def load_matches(path, *, league=None, season=None, date_format="%d/%m/%y", encoding="utf-8-sig") -> ImportResult:
    importer = MatchImporter(
        source= CSVMatchSource(path, encodings=(encoding, "cp1252")),
        pipeline = ValidationPipeline(default_rules(), default_warnings()),
        deduper = DuplicateDetector(
            ("league_id", "season_id", "Date", "Time", "HomeTeam", "AwayTeam")),
        splitter=ResultSplitter(),
    )
    return importer.load(league=league, season=season, date_format=date_format)